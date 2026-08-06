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
from sierra.core.graphs import gconfig
from sierra.plugins.prod.graphs import targets
from sierra.core import plugin as pm
from sierra.core.variables import batch_criteria as bc
from . import line, heatmap, histogram, scatterplot

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """Generate graphs from :term:`Collated Output Data` files.

    Which graphs are generated can be controlled by YAML configuration files
    parsed in stage 4.

    Arguments:
        main_config: Parsed dictionary of main YAML configuration

        cmdopts: Dictionary of parsed cmdline attributes.

        targets: A list of dictionaries, where each dictionary defines an
                 inter-experiment graph to generate.
    """
    utils.dir_create_checked(pathset.graph_interexp_root, exist_ok=True)

    graphs_config = gconfig.load(cmdopts)
    inter_config = gconfig.section(graphs_config, "inter-exp")

    if inter_config is None:
        return

    loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")
    controller_config = loader.load_config(cmdopts, config.PROJECT_YAML.controllers)

    info = criteria.graph_info(cmdopts, batch_output_root=pathset.output_root)
    graph_targets = targets.inter_exp_calc(inter_config, controller_config, cmdopts)

    if criteria.cardinality() == 1:
        if not cmdopts["graphs_no_LN"]:
            line.generate(cmdopts, pathset, graph_targets, info)
        if not cmdopts["graphs_no_HG"]:
            histogram.generate(cmdopts, pathset, graph_targets, info)
        if not cmdopts["graphs_no_SP"]:
            scatterplot.generate(cmdopts, pathset, graph_targets, info)
    elif criteria.cardinality() == 2:
        if not cmdopts["graphs_no_HM"]:
            heatmap.generate(cmdopts, pathset, graph_targets, info)
    else:
        raise RuntimeError("Batch criteria with cardinality > 2 not supported")


__all__ = [
    "proc_batch_exp",
]
