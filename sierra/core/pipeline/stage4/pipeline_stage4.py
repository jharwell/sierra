# Copyright 2018 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT

"""Stage 4 of the experimental pipeline: generating deliverables."""

# Core packages
import typing as tp
import time
import datetime
import logging
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core.pipeline.stage4 import graphs
from sierra.core.pipeline.stage4.model_runner import IntraExpModelRunner
from sierra.core.pipeline.stage4.model_runner import InterExpModelRunner
import sierra.core.variables.batch_criteria as bc

from sierra.core.pipeline.stage4 import render
import sierra.core.plugin_manager as pm
from sierra.core import types, config, utils, batchroot


class PipelineStage4:
    """Generates end-result experimental deliverables.

    Delvirables can be within a single experiment (intra-experiment) and across
    experiments in a batch (inter-experiment).  Currently this includes:

    - Graph generation controlled via YAML config files.

    - Video rendering controlled via YAML config files.

    This stage is idempotent.

    Attributes:
        cmdopts: Dictionary of parsed cmdline options.

        controller_config: YAML configuration file found in
                           ``<project_config_root>/controllers.yaml``. Contains
                           configuration for what categories of graphs should be
                           generated for what controllers, for all categories of
                           graphs in both inter- and intra-experiment graph
                           generation.

        graphs_config: YAML configuration file found in
                         ``<project_config_root>/graphs.yaml``
                         Contains configuration for categories of graphs
                         that *can* potentially be generated for all controllers
                         *across* experiments in a batch and *within* each
                         experiment in a batch. Which linegraphs are
                         *actually* generated for a given controller is
                         controlled by
                         ``<project_config_root>/controllers.yaml``.
    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
    ) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.pathset = pathset

        self.project_config_root = pathlib.Path(self.cmdopts["project_config_root"])
        controllers_yaml = self.project_config_root / config.kYAML.controllers

        if controllers_yaml.exists():
            with utils.utf8open(controllers_yaml) as f:
                self.controller_config = yaml.load(f, yaml.FullLoader)
        else:
            self.controller_config = None

        self.logger = logging.getLogger(__name__)

        # Load YAML config
        loader = pm.module_load_tiered(
            project=self.cmdopts["project"], path="pipeline.stage4.graphs.loader"
        )
        self.graphs_config = loader.load_config(self.cmdopts)

        # Load models
        if self.cmdopts["models_enable"]:
            self._load_models()

    def run(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """Run the pipeline stage.

        Intra-experiment graph generation: if intra-experiment graphs should be
        generated, according to cmdline configuration, the following is run:

        #. Model generation for each enabled and loaded model.

        #. :py:func:`~sierra.core.pipeline.stage4.graphs.intra.generate`
           to generate graphs for each experiment in the batch, or a subset.

        Inter-experiment graph generation: if inter-experiment graphs should be
        generated according to cmdline configuration, the following is run:

        #. :class:`~sierra.core.pipeline.stage4.graphs.collate.UnivarGraphCollator`
           or
           :class:`~sierra.core.pipeline.stage4.graphs.collate.BivarGraphCollator`
           as appropriate (depending on which type of
           :class:`~sierra.core.variables.batch_criteria.BatchCriteria` was
           specified on the cmdline).

        #. Model generation for each enabled and loaded model.

        #. :py:func:`~sierra.core.pipeline.stage4.graphs.inter.generate`
           to perform graph generation from collated CSV files.


        Video generation: The following is run:

        #. :func:`~sierra.core.pipeline.stage4.render.from_engine()`,
           if ``--engine-vc`` was passed

        #. :func:`~sierra.core.pipeline.stage4.render.from_project_imagized()`,
           if ``--project-imagizing`` was passed previously to generate frames,
           and ``--project-rendering`` is passed.

        #. :func:`~sierra.core.pipeline.stage4.render.from_bivar_heatmaps()`,
           if the batch criteria was bivariate and ``--HM-rendering`` was
           passed.

        """
        if self.cmdopts["exp_graphs"] == "all" or self.cmdopts["exp_graphs"] == "intra":
            if criteria.is_univar() and self.cmdopts["models_enable"]:
                self._run_intra_models(criteria)

            if self.graphs_config is not None and "intra-exp" in self.graphs_config:
                self._run_intra_graph_generation(criteria)

        # Collation must be after intra-experiment graph generation, so that all
        # .csv files to be collated have been generated/modified according to
        # parameters.
        if self.cmdopts["exp_graphs"] == "all" or self.cmdopts["exp_graphs"] == "inter":
            self._run_collation(criteria)

            if criteria.is_univar() and self.cmdopts["models_enable"]:
                self._run_inter_models(criteria)

            if self.graphs_config is not None and "inter-exp" in self.graphs_config:
                self._run_inter_graph_generation(criteria)

        # Rendering must be after graph generation in case we should be
        # rendering videos from generated graphs.
        self._run_rendering(criteria)

    def _load_models(self) -> None:
        project_models = self.project_config_root / config.kYAML.models
        self.models_intra = []
        self.models_inter = []

        if not utils.path_exists(project_models):
            self.logger.debug(
                "No models to load for project '%s': %s does not exist",
                self.cmdopts["project"],
                project_models,
            )
            return

        self.logger.info("Loading models for project '%s'", self.cmdopts["project"])

        self.models_config = yaml.load(utils.utf8open(project_models), yaml.FullLoader)
        pm.models.initialize(
            self.cmdopts["project"], pathlib.Path(self.cmdopts["project_model_root"])
        )

        # All models present in the .yaml file are enabled/set to run
        # unconditionally
        available = pm.models.available_plugins()
        self.logger.debug(
            "Project %s has %d available model plugins",
            self.cmdopts["project"],
            len(available),
        )

        for module_name in pm.models.available_plugins():
            # No models specified--nothing to do
            if self.models_config.get("models") is None:
                continue

            for conf in self.models_config["models"]:
                if conf["pyfile"] == module_name:

                    self.logger.debug("Model %s enabled by configuration", module_name)
                    pm.models.load_plugin(module_name)
                    model_name = f"models.{module_name}"
                    module = pm.models.get_plugin_module(model_name)
                    self.logger.debug(
                        ("Configured model %s has %d " "intra-experiment models"),
                        model_name,
                        len(module.available_models("intra")),
                    )

                    self.logger.debug(
                        ("Configured model %s has %d " "inter-experiment models"),
                        model_name,
                        len(module.available_models("inter")),
                    )

                    for avail in module.available_models("intra"):
                        model = getattr(module, avail)(self.main_config, conf)
                        self.models_intra.append(model)

                    for avail in module.available_models("inter"):
                        model = getattr(module, avail)(self.main_config, conf)
                        self.models_inter.append(model)
                else:
                    self.logger.debug("Model %s disabled by configuration", module_name)

        if len(self.models_intra) > 0:
            self.logger.info(
                "Loaded %s intra-experiment models for project '%s'",
                len(self.models_intra),
                self.cmdopts["project"],
            )

        if len(self.models_inter) > 0:
            self.logger.info(
                "Loaded %s inter-experiment models for project '%s'",
                len(self.models_inter),
                self.cmdopts["project"],
            )

    def _calc_inter_targets(
        self, loaded_graphs: types.YAMLDict
    ) -> tp.Optional[tp.List[types.YAMLDict]]:
        """Calculate what inter-experiment graphs to generate.

        This also defines what CSV files need to be collated, as one graph is
        always generated from one CSV file. Uses YAML configuration for
        controllers and inter-experiment graphs.

        """
        keys = []
        if self.controller_config:
            for category in list(self.controller_config.keys()):
                if category not in self.cmdopts["controller"]:
                    continue
                for controller in self.controller_config[category]["controllers"]:
                    if controller["name"] not in self.cmdopts["controller"]:
                        continue

                    # valid to specify no graphs, and only to inherit graphs
                    keys = controller.get("graphs", [])
                    if "graphs_inherit" in controller:
                        for inherit in controller["graphs_inherit"]:
                            keys.extend(inherit)  # optional
            self.logger.debug(
                "Loaded %s inter-experiment categories: %s", len(keys), keys
            )
        else:
            keys = [k for k in loaded_graphs]
            self.logger.debug(
                "Missing controller graph config--generating all "
                "inter-experiment graphs for all controllers: %s",
                keys,
            )

        filtered_keys = [k for k in loaded_graphs if k in keys]
        targets = [loaded_graphs[k] for k in filtered_keys]

        self.logger.debug(
            "Enabled %s inter-experiment categories: %s",
            len(filtered_keys),
            filtered_keys,
        )
        return targets

    def _run_rendering(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """Render captured frames and/or imagized frames into videos."""
        if (
            (not self.cmdopts["engine_vc"])
            and (not self.cmdopts["project_rendering"])
            and (not (criteria.is_bivar() and self.cmdopts["bc_rendering"]))
        ):
            return

        self.logger.info("Rendering videos...")
        start = time.time()

        if self.cmdopts["engine_vc"]:
            render.from_engine(
                self.graphs_config["intra-exp"], self.cmdopts, self.pathset, criteria
            )
        else:
            self.logger.debug(
                (
                    "--engine-vc not passed--(possibly) skipping "
                    "rendering frames captured by the engine"
                )
            )

        if self.cmdopts["project_rendering"]:
            render.from_project_imagized(
                self.graphs_config["intra-exp"], self.cmdopts, self.pathset, criteria
            )
        else:
            self.logger.debug(
                (
                    "--project-rendering not passed--(possibly) "
                    "skipping rendering frames captured by the "
                    "project"
                )
            )

        if criteria.is_bivar() and self.cmdopts["bc_rendering"]:
            render.from_bivar_heatmaps(
                self.graphs_config["intra-exp"], self.cmdopts, self.pathset, criteria
            )
        else:
            self.logger.debug(
                (
                    "--bc-rendering not passed or univariate batch "
                    "criteria--skipping rendering generated graphs"
                )
            )

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Rendering complete in %s", str(sec))

    def _run_intra_models(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info(
            "Running %d intra-experiment models...", len(self.models_intra)
        )
        start = time.time()
        IntraExpModelRunner(self.cmdopts, self.pathset, self.models_intra)(criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Intra-experiment models finished in %s", str(sec))

    def _run_inter_models(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info(
            "Running %d inter-experiment models...", len(self.models_inter)
        )
        start = time.time()

        InterExpModelRunner(self.cmdopts, self.pathset, self.models_inter)(criteria)

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Inter-experiment models finished in %s", str(sec))

    def _run_intra_graph_generation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate intra-experiment graphs (duh).
        """
        self.logger.info("Generating intra-experiment graphs...")
        start = time.time()
        graphs.intra.generate.generate(
            self.main_config,
            self.cmdopts,
            self.pathset,
            self.controller_config,
            self.graphs_config["intra-exp"],
            criteria,
        )
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Intra-experiment graph generation complete: %s", str(sec))

    def _run_collation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        if not self.graphs_config or "inter-exp" not in self.graphs_config:
            self.logger.debug(
                "Skipping inter-experiment collation: no output graphs defined"
            )
            return

        targets = self._calc_inter_targets(
            loaded_graphs=self.graphs_config["inter-exp"],
        )

        if not self.cmdopts["skip_collate"]:
            self.logger.info("Collating inter-experiment CSV files...")
            start = time.time()
            collator = graphs.collate.ParallelCollator(
                self.main_config, self.cmdopts, self.pathset
            )
            collator(criteria, targets)
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            self.logger.info(
                "Collating inter-experiment CSV files complete: %s", str(sec)
            )

    def _run_inter_graph_generation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate inter-experiment graphs (duh).
        """
        targets = self._calc_inter_targets(
            loaded_graphs=self.graphs_config["inter-exp"],
        )

        self.logger.info("Generating inter-experiment graphs...")
        start = time.time()

        module = pm.module_load_tiered(
            project=self.cmdopts["project"],
            path="pipeline.stage4.graphs.inter.generate",
        )
        module.generate(
            self.main_config,
            self.cmdopts,
            self.pathset,
            targets,
            criteria,
        )
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)

        self.logger.info("Inter-experiment graph generation complete: %s", str(sec))


__all__ = ["PipelineStage4"]
