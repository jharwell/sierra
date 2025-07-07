# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#

"""
Generate graphs across experiments in a batch.
"""

# Core packages
import logging

# 3rd party packages

# Project packages
from sierra.core import types, utils, batchroot, config
from . import line, heatmap
from sierra.plugins.prod.graphs import targets
from sierra.core import plugin as pm
from sierra.core.graphs import bcbridge
from sierra.core.variables import batch_criteria as bc

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """Generate graphs from :term:`Collated Output Data` files.

    Performs the following steps:

        #. :func:`~sierra.plugins.prod.graphs.inter.line.generate()` to
           generate linegraphs (univariate batch criteria only).

        #. :func:`~sierra.plugins.prod.graphs.inter.heatmap.generate()`
           to generate heatmaps (bivariate batch criteria only).

    Which graphs are generated can be controlled by YAML configuration files
    parsed in
    :class:`~sierra.plugins.prod.pipeline_stage4.PipelineStage4`.

    This class can be extended/overriden using a: term: `Project` hook.  See
    :ref:`tutorials/project/hooks` for details.

    Arguments:
        main_config: Parsed dictionary of main YAML configuration

        cmdopts: Dictionary of parsed cmdline attributes.

        targets: A list of dictionaries, where each dictionary defines an
                 inter-experiment graph to generate.
    """
    utils.dir_create_checked(pathset.graph_collate_root, exist_ok=True)

    loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")

    graphs_config = loader.load_config(cmdopts, config.kYAML.graphs)

    if "inter-exp" not in graphs_config:
        _logger.warning(
            "Cannot generate graphs: 'inter-exp' key not found in YAML config"
        )
        return

    controller_config = loader.load_config(cmdopts, config.kYAML.controllers)

    info = criteria.graph_info(cmdopts, batch_output_root=pathset.output_root)

    if criteria.cardinality() == 1:
        if not cmdopts["project_no_LN"]:
            graph_targets = targets.inter_exp_calc(
                graphs_config["inter-exp"], controller_config, cmdopts
            )
            line.generate(cmdopts, pathset, graph_targets, info)
    else:
        graph_targets = targets.inter_exp_calc(
            graphs_config["inter-exp"], controller_config, cmdopts
        )
        heatmap.generate(cmdopts, pathset, graph_targets, info)


__all__ = [
    "proc_batch_exp",
]
