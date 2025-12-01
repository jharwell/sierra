# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
Generate graphs within a single :term:`Experiment`.
"""

# Core packages
import os
import copy
import typing as tp
import logging
import pathlib

# 3rd party packages
import yaml
import json
import numpy as np

# Project packages

import sierra.core.plugin as pm
from sierra.core import types, utils, batchroot, exproot, config, graphs
from sierra.core.variables import batch_criteria as bc


_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Generate intra-experiment graphs for a :term:`Batch Experiment`.

    Arguments:
        main_config: Parsed dictionary of main YAML configuration


        criteria:  The :term:`Batch Criteria` used for the batch
                   experiment.
    """
    info = criteria.graph_info(cmdopts, batch_output_root=pathset.output_root)
    exp_to_gen = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, info.exp_names
    )

    if not exp_to_gen:
        return

    loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")

    graphs_config = loader.load_config(cmdopts, config.PROJECT_YAML.graphs)

    if "intra-exp" not in graphs_config:
        _logger.warning(
            "Cannot generate graphs: 'intra-exp' key not found in YAML config"
        )
        return

    project_config_root = pathlib.Path(cmdopts["project_config_root"])
    controllers_yaml = project_config_root / config.PROJECT_YAML.controllers

    if controllers_yaml.exists():
        with utils.utf8open(controllers_yaml) as f:
            controller_config = yaml.load(f, yaml.FullLoader)
    else:
        controller_config = None

    generator = _ExpGraphGenerator(
        main_config, controller_config, graphs_config["intra-exp"], cmdopts
    )
    for exp in exp_to_gen:
        exproots = exproot.PathSet(pathset, exp.name)

        if exproots.stat_root.is_dir():
            generator(exproots)
        else:
            _logger.warning(
                "Skipping experiment '%s': %s does not exist, or isn't a directory",
                exp,
                exproots.stat_root,
            )


class _ExpGraphGenerator:
    """Generates graphs from :term:`Processed Output Data` files.

    Which graphs are generated is controlled by YAML configuration files parsed
    in stage 4.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.

        main_config: Parsed dictionary of main YAML configuration

        controller_config: Parsed dictionary of controller YAML
                           configuration.

        graphs_config: Parsed dictionary of intra-experiment graph
                       configuration.

        logger: The handle to the logger for this class. If you extend this
               class, you should save/restore this variable in tandem with
               overriding it in order to get logging messages have unique logger
               names between this class and your derived class, in order to
               reduce confusion.

    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        controller_config: tp.Optional[types.YAMLDict],
        graphs_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
    ) -> None:
        # Copy because we are modifying it and don't want to mess up the
        # arguments for graphs that are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.graphs_config = graphs_config
        self.controller_config = controller_config
        self.logger = logging.getLogger(__name__)

    def __call__(self, pathset: exproot.PathSet) -> None:
        """
        Generate all intra-experiment graphs for a single experiment.

        Performs the following steps:

            #. Generates linegraphs for each experiment in the batch.

            #. Generates heatmaps for each experiment in the batch.

            #. Generates confusion matrices for each experiment in the batch.
        """
        utils.dir_create_checked(pathset.graph_root, exist_ok=True)

        LN_targets, HM_targets, CM_targets = self._calc_targets()

        if not self.cmdopts["project_no_LN"]:
            _generate_linegraphs(self.cmdopts, pathset, LN_targets)

        if not self.cmdopts["project_no_HM"]:
            _generate_heatmaps(self.cmdopts, pathset, HM_targets)

        if not self.cmdopts["project_no_CM"]:
            _generate_confusion_matrices(self.cmdopts, pathset, CM_targets)

    def _calc_targets(
        self,
    ) -> tuple[list[types.YAMLDict], list[types.YAMLDict], list[types.YAMLDict]]:
        """Calculate what intra-experiment graphs should be generated.

        Uses YAML configuration for controller and intra-experiment graphs.
        Returns a tuple of dictionaries defining what graphs to generate.  The
        enabled graphs exist in their respective YAML configuration *and* are
        enabled by the YAML configuration for the selected controller.
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

        else:
            keys = list(self.graphs_config)
            self.logger.warning(
                "Missing controller graph config--generating all enabled "
                "intra-experiment graphs for all controllers: %s",
                keys,
            )

        # Get keys for enabled graphs
        LN_keys = [k for k in self.graphs_config if k in keys]
        self.logger.debug("Enabled linegraph categories: %s", LN_keys)

        HM_keys = [k for k in self.graphs_config if k in keys]
        self.logger.debug("Enabled heatmap categories: %s", HM_keys)

        CM_keys = [k for k in self.graphs_config if k in keys]
        self.logger.debug("Enabled confusion matrix categories: %s", CM_keys)

        # Strip out all configured graphs which are not enabled
        LN_targets = [self.graphs_config[k] for k in LN_keys]
        HM_targets = [self.graphs_config[k] for k in HM_keys]
        CM_targets = [self.graphs_config[k] for k in CM_keys]

        return LN_targets, HM_targets, CM_targets


def _generate_heatmaps(
    cmdopts: types.Cmdopts,
    pathset: exproot.PathSet,
    targets: list[types.YAMLDict],
) -> None:
    """
    Generate heatmaps from: term:`Processed Output Data` files.
    """
    large_text = cmdopts["plot_large_text"]

    _logger.info(
        "Heatmaps from <batch_root>/%s", pathset.stat_root.relative_to(pathset.parent)
    )

    # For each category of heatmaps we are generating
    for category in targets:

        # For each graph in each category
        for graph in category:
            # Only try to create heatmaps (duh)
            if graph["type"] != "heatmap":
                continue

            _logger.trace("\n" + json.dumps(graph, indent=4))

            graph_pathset = graphs.PathSet(
                input_root=pathset.stat_root,
                output_root=pathset.graph_root,
                batchroot=pathset.parent.parent,
                model_root=None,
            )
            # 2025-06-05 [JRH]: We always write stage {3,4} output data files as
            # .csv because that is currently SIERRA's 'native' format; this may
            # change in the future.
            graphs.heatmap(
                pathset=graph_pathset,
                input_stem=graph["src_stem"],
                output_stem=graph["dest_stem"],
                medium="storage.csv",
                title=graph.get("title", None),
                xlabel=graph.get("xlabel", None),
                ylabel=graph.get("ylabel", None),
                zlabel=graph.get("zlabel", None),
                backend=graph.get("backend", cmdopts["graphs_backend"]),
                colnames=(
                    graph.get("x", "x"),
                    graph.get("y", "y"),
                    graph.get("z", "z"),
                ),
                large_text=large_text,
            )


def _generate_linegraphs(
    cmdopts: types.Cmdopts, pathset: exproot.PathSet, targets: list[types.YAMLDict]
) -> None:
    """
    Generate linegraphs from: term:`Processed Output Data` files.
    """

    _logger.info(
        "Linegraphs from <batch_root>/%s", pathset.stat_root.relative_to(pathset.parent)
    )

    # For each category of linegraphs we are generating
    for category in targets:
        # For each graph in each category
        for graph in category:

            # Only try to create linegraphs (duh)
            if graph["type"] != "stacked_line":
                continue

            _logger.trace("\n" + json.dumps(graph, indent=4))

            paths = graphs.PathSet(
                input_root=pathset.stat_root,
                output_root=pathset.graph_root,
                batchroot=pathset.parent.parent,
                model_root=pathset.model_root,
            )

            try:
                # 2025-06-05 [JRH]: We always write stage {3,4} output data
                # files as .csv because that is currently SIERRA's 'native'
                # format; this may change in the future.
                module = pm.pipeline.get_plugin_module(cmdopts["engine"])
                if hasattr(module, "expsetup_from_def"):
                    module2 = pm.pipeline.get_plugin_module(cmdopts["expdef"])
                    pkl_def = module2.unpickle(pathset.input_root / config.PICKLE_LEAF)

                    info = module.expsetup_from_def(pkl_def)
                    xticks = np.linspace(
                        0,
                        info["duration"],
                        int(
                            info["duration"]
                            * info["n_ticks_per_sec"]
                            * cmdopts["exp_n_datapoints_factor"]
                        ),
                    )
                else:
                    xticks = None

                graphs.stacked_line(
                    paths=paths,
                    input_stem=graph["src_stem"],
                    output_stem=graph["dest_stem"],
                    medium="storage.csv",
                    backend=graph.get("backend", cmdopts["graphs_backend"]),
                    xticks=xticks,
                    stats=cmdopts.get("dist_stats", "none"),
                    cols=graph.get("cols", None),
                    title=graph.get("title", ""),
                    legend=graph.get("legend", graph.get("cols", None)),
                    xlabel=graph.get("xlabel", ""),
                    ylabel=graph.get("ylabel", ""),
                    points=graph.get("points", False),
                    logyscale=graph.get("logy", cmdopts["plot_log_yscale"]),
                    large_text=cmdopts["plot_large_text"],
                )
            except KeyError:
                _logger.fatal(
                    "Could not generate linegraph. Possible reasons include: "
                )

                _logger.fatal(
                    "1. The YAML configuration entry is missing required fields"
                )
                missing_cols = graph.get("cols", "MISSING_KEY")
                missing_stem = graph.get("src_stem", "MISSING_KEY")
                _logger.fatal(
                    (
                        "2. 'cols' is present in YAML "
                        "configuration but some of %s are "
                        "missing from %s"
                    ),
                    missing_cols,
                    missing_stem,
                )

                raise


def _generate_confusion_matrices(
    cmdopts: types.Cmdopts,
    pathset: exproot.PathSet,
    targets: list[types.YAMLDict],
) -> None:
    """
    Generate confusion matrices from: term:`Processed Output Data` files.
    """
    large_text = cmdopts["plot_large_text"]

    _logger.info(
        "Confusion matrices from <batch_root>/%s",
        pathset.stat_root.relative_to(pathset.parent),
    )

    # For each category of heatmaps we are generating
    for category in targets:

        # For each graph in each category
        for graph in category:
            # Only try to create confusion matrices (duh)
            if graph["type"] != "confusion_matrix":
                continue

            _logger.trace("\n" + json.dumps(graph, indent=4))

            graph_pathset = graphs.PathSet(
                input_root=pathset.stat_root,
                output_root=pathset.graph_root,
                batchroot=pathset.parent.parent,
                model_root=None,
            )
            graphs.confusion_matrix(
                pathset=graph_pathset,
                input_stem=graph["src_stem"],
                output_stem=graph["dest_stem"],
                medium="storage.csv",
                title=graph.get("title", None),
                backend=graph.get("backend", cmdopts["graphs_backend"]),
                truth_col=graph.get("truth_col", "truth"),
                predicted_col=graph.get("predicted_col", "predicted"),
                xlabels_rotate=graph.get("xlabels_rotate", False),
                large_text=large_text,
            )


__all__ = [
    "_ExpGraphGenerator",
    "proc_batch_exp",
]
