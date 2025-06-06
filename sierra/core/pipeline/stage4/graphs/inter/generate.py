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

from sierra.core.pipeline.stage4.graphs.inter import line


def generate(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    targets: tp.List[types.YAMLDict],
    criteria: bc.IConcreteBatchCriteria,
) -> None:
    """Generate graphs from :term:`Collated Output Data` files.

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

    Arguments:
        main_config: Parsed dictionary of main YAML configuration

        cmdopts: Dictionary of parsed cmdline attributes.

        targets: A list of dictionaries, where each dictionary defines an
                 inter-experiment graph to generate.
    """
    utils.dir_create_checked(pathset.graph_collate_root, exist_ok=True)

    if criteria.is_univar():
        if not cmdopts["project_no_LN"]:
            line.generate(cmdopts, pathset, targets, criteria)


__all__ = [
    "generate",
]
