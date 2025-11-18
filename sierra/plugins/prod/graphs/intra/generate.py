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

# Project packages

import sierra.core.plugin as pm
from sierra.core import types, utils, batchroot, exproot, config
from sierra.plugins.prod.graphs import intra
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

    generator = IntraExpGraphGenerator(
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


class IntraExpGraphGenerator:
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
        Generate graphs.

        Performs the following steps:

        #. :func:`~sierra.plugins.prod.graphs.intra.line.generate()`
            to generate linegraphs for each experiment in the batch.

        #. :func:`~sierra.plugins.prod.graphs.intra.heatmap.generate()`
            to generate heatmaps for each experiment in the batch.
        """
        utils.dir_create_checked(pathset.graph_root, exist_ok=True)

        LN_targets, HM_targets = self._calc_targets()

        if not self.cmdopts["project_no_LN"]:
            intra.line.generate(self.cmdopts, pathset, LN_targets)

        if not self.cmdopts["project_no_HM"]:
            intra.heatmap.generate(self.cmdopts, pathset, HM_targets)

    def _calc_targets(
        self,
    ) -> tuple[list[types.YAMLDict], list[types.YAMLDict]]:
        """Calculate what intra-experiment graphs should be generated.

        Uses YAML configuration for controller and intra-experiment graphs.
        Returns a tuple of dictionaries: (intra-experiment linegraphs,
        intra-experiment heatmaps) defined what graphs to generate.  The enabled
        graphs exist in their respective YAML configuration *and* are enabled by
        the YAML configuration for the selected controller.
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

        # Strip out all configured graphs which are not enabled
        LN_targets = [self.graphs_config[k] for k in LN_keys]
        HM_targets = [self.graphs_config[k] for k in HM_keys]

        return LN_targets, HM_targets


__all__ = [
    "IntraExpGraphGenerator",
    "proc_batch_exp",
]
