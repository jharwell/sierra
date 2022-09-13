# Copyright 2018 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""Stage 4 of the experimental pipeline: generating deliverables.

"""

# Core packages
import typing as tp
import time
import datetime
import logging
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core.pipeline.stage4.graph_collator import GraphParallelCollator
from sierra.core.pipeline.stage4.intra_exp_graph_generator import BatchIntraExpGraphGenerator
from sierra.core.pipeline.stage4.model_runner import IntraExpModelRunner
from sierra.core.pipeline.stage4.model_runner import InterExpModelRunner
import sierra.core.variables.batch_criteria as bc

from sierra.core.pipeline.stage4 import rendering
import sierra.core.plugin_manager as pm
from sierra.core import types, config, utils


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

        inter_LN_config: YAML configuration file found in
                         ``<project_config_root>/inter-graphs-line.yaml``
                         Contains configuration for categories of linegraphs
                         that can potentially be generated for all controllers
                         `across` experiments in a batch. Which linegraphs are
                         actually generated for a given controller is controlled
                         by ``<project_config_root>/controllers.yaml``.

        intra_LN_config: YAML configuration file found in
                         ``<project_config_root>/intra-graphs-line.yaml``
                         Contains configuration for categories of linegraphs
                         that can potentially be generated for all controllers
                         `within` each experiment in a batch. Which linegraphs
                         are actually generated for a given controller in each
                         experiment is controlled by
                         ``<project_config_root>/controllers.yaml``.

        intra_HM_config: YAML configuration file found in
                         ``<project_config_root>/intra-graphs-hm.yaml`` Contains
                         configuration for categories of heatmaps that can
                         potentially be generated for all controllers `within`
                         each experiment in a batch. Which heatmaps are actually
                         generated for a given controller in each experiment is
                         controlled by
                         ``<project_config_root>/controllers.yaml``.

        inter_HM_config: YAML configuration file found in
                         ``<project_config_root>/inter-graphs-hm.yaml`` Contains
                         configuration for categories of heatmaps that can
                         potentially be generated for all controllers `across`
                         each experiment in a batch. Which heatmaps are actually
                         generated for a given controller in each experiment is
                         controlled by
                         ``<project_config_root>/controllers.yaml``.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        self.main_config = main_config

        self.project_config_root = pathlib.Path(self.cmdopts['project_config_root'])
        controllers_yaml = self.project_config_root / config.kYAML.controllers

        with utils.utf8open(controllers_yaml) as f:
            self.controller_config = yaml.load(f, yaml.FullLoader)
        self.logger = logging.getLogger(__name__)

        # Load YAML config
        loader = pm.module_load_tiered(project=self.cmdopts['project'],
                                       path='pipeline.stage4.yaml_config_loader')
        graphs_config = loader.YAMLConfigLoader()(self.cmdopts)
        self.intra_LN_config = graphs_config['intra_LN']
        self.intra_HM_config = graphs_config['intra_HM']
        self.inter_HM_config = graphs_config['inter_HM']
        self.inter_LN_config = graphs_config['inter_LN']

        # Load models
        if self.cmdopts['models_enable']:
            self._load_models()

    def run(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """Run the pipeline stage.

        Intra-experiment graph generation: if intra-experiment graphs should be
        generated, according to cmdline configuration, the following is run:

        #. Model generation for each enabled and loaded model.

        #. :class:`~sierra.core.pipeline.stage4.intra_exp_graph_generator.BatchIntraExpGraphGenerator`
           to generate graphs for each experiment in the batch, or a subset.

        Inter-experiment graph generation: if inter-experiment graphs should be
        generated according to cmdline configuration, the following is run:

        #. :class:`~sierra.core.pipeline.stage4.graph_collator.UnivarGraphCollator`
           or
           :class:`~sierra.core.pipeline.stage4.graph_collator.BivarGraphCollator`
           as appropriate (depending on which type of
           :class:`~sierra.core.variables.batch_criteria.BatchCriteria` was
           specified on the cmdline).

        #. Model generation for each enabled and loaded model.

        #. :class:`~sierra.core.pipeline.stage4.inter_exp_graph_generator.InterExpGraphGenerator`
           to perform graph generation from collated CSV files.


        Video generation: The following is run:

        #. :class:`~sierra.core.pipeline.stage4.rendering.PlatformFramesRenderer`,
           if ``--platform-vc`` was passed

        #. :class:`~sierra.core.pipeline.stage4.rendering.ProjectFramesRenderer`,
           if ``--project-imagizing`` was passed previously to generate frames,
           and ``--project-rendering`` is passed.

        #. :class:`~sierra.core.pipeline.stage4.rendering.BivarHeatmapRenderer`,
           if the batch criteria was bivariate and ``--HM-rendering`` was
           passed.

        """
        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'intra':
            if criteria.is_univar() and self.cmdopts['models_enable']:
                self._run_intra_models(criteria)

            self._run_intra_graph_generation(criteria)

        # Collation must be after intra-experiment graph generation, so that all
        # .csv files to be collated have been generated/modified according to
        # parameters.
        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'inter':
            self._run_collation(criteria)

            if criteria.is_univar() and self.cmdopts['models_enable']:
                self._run_inter_models(criteria)

            self._run_inter_graph_generation(criteria)

        # Rendering must be after graph generation in case we should be
        # rendering videos from generated graphs.
        self._run_rendering(criteria)

    def _load_models(self) -> None:
        project_models = self.project_config_root / config.kYAML.models
        self.models_intra = []
        self.models_inter = []

        if not utils.path_exists(project_models):
            self.logger.debug("No models to load for project '%s': %s does not exist",
                              self.cmdopts['project'],
                              project_models)
            return

        self.logger.info("Loading models for project '%s'",
                         self.cmdopts['project'])

        self.models_config = yaml.load(utils.utf8open(project_models),
                                       yaml.FullLoader)
        pm.models.initialize(self.cmdopts['project'],
                             pathlib.Path(self.cmdopts['project_model_root']))

        # All models present in the .yaml file are enabled/set to run
        # unconditionally
        available = pm.models.available_plugins()
        self.logger.debug("Project %s has %d available model plugins",
                          self.cmdopts['project'],
                          len(available))

        for module_name in pm.models.available_plugins():
            # No models specified--nothing to do
            if self.models_config.get('models') is None:
                continue

            for conf in self.models_config['models']:
                if conf['pyfile'] == module_name:

                    self.logger.debug("Model %s enabled by configuration",
                                      module_name)
                    pm.models.load_plugin(module_name)
                    model_name = f'models.{module_name}'
                    module = pm.models.get_plugin_module(model_name)
                    self.logger.debug(("Configured model %s has %d "
                                       "intra-experiment models"),
                                      model_name,
                                      len(module.available_models('intra')))

                    self.logger.debug(("Configured model %s has %d "
                                       "inter-experiment models"),
                                      model_name,
                                      len(module.available_models('inter')))

                    for avail in module.available_models('intra'):
                        model = getattr(module, avail)(self.main_config, conf)
                        self.models_intra.append(model)

                    for avail in module.available_models('inter'):
                        model = getattr(module, avail)(self.main_config, conf)
                        self.models_inter.append(model)
                else:
                    self.logger.debug("Model %s disabled by configuration",
                                      module_name)

        if len(self.models_intra) > 0:
            self.logger.info("Loaded %s intra-experiment models for project '%s'",
                             len(self.models_intra),
                             self.cmdopts['project'])

        if len(self.models_inter) > 0:
            self.logger.info("Loaded %s inter-experiment models for project '%s'",
                             len(self.models_inter),
                             self.cmdopts['project'])

    def _calc_inter_targets(self,
                            name: str,
                            category_prefix: str,
                            loaded_graphs: types.YAMLDict) -> tp.List[types.YAMLDict]:
        """Calculate what inter-experiment graphs to generate.

        This also defines what CSV files need to be collated, as one graph is
        always generated from one CSV file. Uses YAML configuration for
        controllers and inter-experiment graphs.

        """
        keys = []
        for category in list(self.controller_config.keys()):
            if category not in self.cmdopts['controller']:
                continue
            for controller in self.controller_config[category]['controllers']:
                if controller['name'] not in self.cmdopts['controller']:
                    continue

                # valid to specify no graphs, and only to inherit graphs
                keys = controller.get('graphs', [])
                if 'graphs_inherit' in controller:
                    for inherit in controller['graphs_inherit']:
                        keys.extend(inherit)   # optional

        self.logger.debug("Loaded %s inter-experiment categories: %s",
                          name,
                          keys)

        filtered_keys = [k for k in loaded_graphs if category_prefix in k]
        filtered_keys = [k for k in loaded_graphs if k in keys]
        targets = [loaded_graphs[k] for k in filtered_keys]

        self.logger.debug("Enabled %s inter-experiment categories: %s", name,
                          filtered_keys)
        return targets

    def _run_rendering(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """Render captured frames and/or imagized frames into videos.

        """
        if ((not self.cmdopts['platform_vc']) and
            (not self.cmdopts['project_rendering']) and
                (not (criteria.is_bivar() and self.cmdopts['bc_rendering']))):
            return

        self.logger.info("Rendering videos...")
        start = time.time()

        if self.cmdopts['platform_vc']:
            rendering.PlatformFramesRenderer(self.main_config,
                                             self.cmdopts)(criteria)
        else:
            self.logger.debug(("--platform-vc not passed--skipping rendering "
                               "frames captured by the platform"))

        if self.cmdopts['project_rendering']:
            rendering.ProjectFramesRenderer(self.main_config,
                                            self.cmdopts)(criteria)
        else:
            self.logger.debug(("--project-rendering not passed--skipping "
                               "rendering frames captured by the project"))

        if criteria.is_bivar() and self.cmdopts['bc_rendering']:
            rendering.BivarHeatmapRenderer(self.main_config,
                                           self.cmdopts)(criteria)
        else:
            self.logger.debug(("--bc-rendering not passed or univariate batch "
                               "criteria--skipping rendering generated graphs"))

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Rendering complete in %s", str(sec))

    def _run_intra_models(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("Running %d intra-experiment models...",
                         len(self.models_intra))
        start = time.time()
        IntraExpModelRunner(self.cmdopts,
                            self.models_intra)(self.main_config,
                                               criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Intra-experiment models finished in %s", str(sec))

    def _run_inter_models(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("Running %d inter-experiment models...",
                         len(self.models_inter))
        start = time.time()

        runner = InterExpModelRunner(self.cmdopts, self.models_inter)
        runner(self.main_config, criteria)

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Inter-experiment models finished in %s", str(sec))

    def _run_intra_graph_generation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate intra-experiment graphs (duh).
        """
        self.logger.info("Generating intra-experiment graphs...")
        start = time.time()
        BatchIntraExpGraphGenerator(self.cmdopts)(self.main_config,
                                                  self.controller_config,
                                                  self.intra_LN_config,
                                                  self.intra_HM_config,
                                                  criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info(
            "Intra-experiment graph generation complete: %s", str(sec))

    def _run_collation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        LN_targets = self._calc_inter_targets(name='linegraph',
                                              category_prefix='LN',
                                              loaded_graphs=self.inter_LN_config)
        HM_targets = self._calc_inter_targets(name='heatmap',
                                              category_prefix='HM',
                                              loaded_graphs=self.inter_HM_config)

        if not self.cmdopts['skip_collate']:
            self.logger.info("Collating inter-experiment CSV files...")
            start = time.time()
            collator = GraphParallelCollator(self.main_config, self.cmdopts)
            collator(criteria, LN_targets)
            collator(criteria, HM_targets)
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            self.logger.info("Collating inter-experiment CSV files complete: %s",
                             str(sec))

    def _run_inter_graph_generation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate inter-experiment graphs (duh).
        """
        LN_targets = self._calc_inter_targets(name='linegraph',
                                              category_prefix='LN',
                                              loaded_graphs=self.inter_LN_config)
        HM_targets = self._calc_inter_targets(name='heatmap',
                                              category_prefix='HM',
                                              loaded_graphs=self.inter_HM_config)

        self.logger.info("Generating inter-experiment graphs...")
        start = time.time()

        module = pm.module_load_tiered(project=self.cmdopts['project'],
                                       path='pipeline.stage4.inter_exp_graph_generator')
        generator = module.InterExpGraphGenerator(self.main_config,
                                                  self.cmdopts,
                                                  LN_targets,
                                                  HM_targets)
        generator(criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)

        self.logger.info("Inter-experiment graph generation complete: %s",
                         str(sec))


__api__ = [
    'PipelineStage4'
]
