# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#

"""
Generate graphs across experiments in a batch.
"""

# Core packages
import typing as tp

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import types, utils, batchroot

from sierra.core.pipeline.stage4.graphs.inter import line, heatmap


def generate(main_config: types.YAMLDict,
             cmdopts: types.Cmdopts,
             pathset: batchroot.PathSet,
             LN_targets: tp.List[types.YAMLDict],
             HM_targets: tp.List[types.YAMLDict],
             criteria: bc.IConcreteBatchCriteria) -> None:
    """Generate graphs from :term:`Collated .csv` files.

    Performs the following steps:

        #. :func:`~sierra.core.pipeline.stage4.graphs.inter.line.generate()` to
           generate linegraphs (univariate batch criteria only).

        #. :func:`~sierra.core.pipeline.stage4.graphs.inter.heatmap.generate()`
           to generate heatmaps (bivariate batch criteria only).

    Which graphs are generated can be controlled by YAML configuration files
    parsed in
    :class:`~sierra.core.pipeline.stage4.pipeline_stage4.PipelineStage4`.

    This class can be extended/overriden using a: term: `Project` hook.  See
    :ref:`tutorials/project/hooks` for details.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.

        main_config: Parsed dictionary of main YAML configuration

        LN_targets: A list of dictionaries, where each dictionary defines an
        inter-experiment linegraph to generate.

        HM_targets: A list of dictionaries, where each dictionary defines an
        inter-experiment heatmap to generate.

        logger: The handle to the logger for this class .  If you extend this
        class you should save/restore this variable in tandem with overriding it
        in order to get logging messages have unique logger names between this
        class and your derived class , in order to reduce confusion.
    """
    utils.dir_create_checked(pathset.graph_collate_root, exist_ok=True)

    if criteria.is_univar():
        if not cmdopts['project_no_LN']:
            line.generate(cmdopts,
                          pathset,
                          LN_targets,
                          criteria)
    else:
        if not cmdopts['project_no_HM']:
            heatmap.generate(cmdopts,
                             pathset,
                             HM_targets,
                             criteria)


__all__ = [
    'generate',
]
