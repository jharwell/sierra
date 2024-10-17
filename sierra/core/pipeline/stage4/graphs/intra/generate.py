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

# Project packages

import sierra.core.variables.batch_criteria as bc
import sierra.core.plugin_manager as pm
from sierra.core import types, utils, batchroot, exproot
from sierra.core.pipeline.stage4.graphs.intra import line, heatmap

_logger = logging.getLogger(__name__)


def generate(main_config: types.YAMLDict,
             cmdopts: types.Cmdopts,
             pathset: batchroot.PathSet,
             controller_config: types.YAMLDict,
             LN_config: types.YAMLDict,
             HM_config: types.YAMLDict,
             criteria: bc.IConcreteBatchCriteria) -> None:
    """
    Generate intra-experiment graphs for a :term:`Batch Experiment`.

    Parameters:

        main_config: Parsed dictionary of main YAML configuration

        controller_config: Parsed dictionary of controller YAML
                           configuration.

        LN_config: Parsed dictionary of intra-experiment linegraph
                   configuration.

        HM_config: Parsed dictionary of intra-experiment heatmap
                   configuration.

        criteria:  The :term:`Batch Criteria` used for the batch
                   experiment.
    """
    exp_to_gen = utils.exp_range_calc(cmdopts["exp_range"],
                                      pathset.output_root,
                                      criteria)

    if not exp_to_gen:
        return

    module = pm.module_load_tiered(project=cmdopts['project'],
                                   path='pipeline.stage4.graphs.intra.generate')

    generator = module.IntraExpGraphGenerator(main_config,
                                              controller_config,
                                              LN_config,
                                              HM_config,
                                              cmdopts)
    for exp in exp_to_gen:
        exproots = exproot.PathSet(pathset, exp.name)

        if os.path.isdir(exproots.stat_root):
            generator(exproots, criteria)
        else:
            _logger.warning("Skipping experiment '%s': % s does not exist, or "
                            "isn't a directory",
                            exp,
                            cmdopts['exp_stat_root'])


class IntraExpGraphGenerator:
    """Generates graphs from :term:`Averaged .csv` files for a single experiment.

    Which graphs are generated is controlled by YAML configuration files parsed
    in :class:`~sierra.core.pipeline.stage4.pipeline_stage4.PipelineStage4`.

    This class can be extended/overriden using a :term:`Project` hook. See
    :ref:`ln-sierra-tutorials-project-hooks` for details.

    Attributes:

        cmdopts: Dictionary of parsed cmdline attributes.

        main_config: Parsed dictionary of main YAML configuration

        controller_config: Parsed dictionary of controller YAML
                           configuration.

        LN_config: Parsed dictionary of intra-experiment linegraph
                   configuration.

        HM_config: Parsed dictionary of intra-experiment heatmap
                   configuration.

        criteria:  The :term:`Batch Criteria` used for the batch
                   experiment.

        logger: The handle to the logger for this class. If you extend this
               class, you should save/restore this variable in tandem with
               overriding it in order to get logging messages have unique logger
               names between this class and your derived class, in order to
               reduce confusion.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 controller_config: types.YAMLDict,
                 LN_config: types.YAMLDict,
                 HM_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        # Copy because we are modifying it and don't want to mess up the
        # arguments for graphs that are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.LN_config = LN_config
        self.HM_config = HM_config
        self.controller_config = controller_config
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 pathset: exproot.PathSet,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate graphs.

        Performs the following steps:

        #. :func:`~sierra.core.pipeline.stage4.graphs.intra.line.generate()`
            to generate linegraphs for each experiment in the batch.

        #. :func:`~sierra.core.pipeline.stage4.graphs.intra.heatmap.generate()`
            to generate heatmaps for each experiment in the batch.
        """
        utils.dir_create_checked(self.pathset.graph_root, exist_ok=True)

        LN_targets, HM_targets = self.calc_targets()

        if not self.cmdopts['project_no_LN']:
            line.generate(self.cmdopts, LN_targets)

        if not self.cmdopts['project_no_HM']:
            heatmap.generate(self.cmdopts, HM_targets)

    def calc_targets(self) -> tp.Tuple[tp.List[types.YAMLDict],
                                       tp.List[types.YAMLDict]]:
        """Calculate what intra-experiment graphs should be generated.

        Uses YAML configuration for controller and intra-experiment graphs.
        Returns a tuple of dictionaries: (intra-experiment linegraphs,
        intra-experiment heatmaps) defined what graphs to generate. The enabled
        graphs exist in their YAML respective YAML configuration `and` are
        enabled by the YAML configuration for the selected controller.

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

        # Get keys for enabled graphs
        LN_keys = [k for k in self.LN_config if k in keys]
        self.logger.debug("Enabled linegraph categories: %s", LN_keys)

        HM_keys = [k for k in self.HM_config if k in keys]
        self.logger.debug("Enabled heatmap categories: %s", HM_keys)

        # Strip out all configured graphs which are not enabled
        LN_targets = [self.LN_config[k] for k in LN_keys]
        HM_targets = [self.HM_config[k] for k in HM_keys]

        return LN_targets, HM_targets


__api__ = [
    'generate',
    'IntraExpGraphGenerator',
]
