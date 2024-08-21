#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages
import json

# Project packages
from sierra.core import types, config
from sierra.core.variables import batch_criteria as bc
from sierra.core.graphs.stacked_line_graph import StackedLineGraph
from sierra.core.graphs.summary_line_graph import SummaryLineGraph

_logger = logging.getLogger(__name__)


def generate(
        cmdopts: types.Cmdopts,
        targets: tp.List[types.YAMLDict],
        criteria: bc.IConcreteBatchCriteria) -> None:
    """Generate linegraphs from :term:`Collated .csv` files.

    The graphs generated by this module respect the ``--exp-range`` cmdline
    option.
    """

    _logger.info("LineGraphs from %s",
                 cmdopts['batch_stat_collate_root'])
    graph_root = pathlib.Path(cmdopts['batch_graph_collate_root'])

    # For each category of linegraphs we are generating
    for category in targets:

        # For each graph in each category
        for graph in category['graphs']:
            _logger.trace('\n' +  # type: ignore
                          json.dumps(graph, indent=4))
            if graph.get('summary', False):
                _gen_summary_linegraph(graph, cmdopts, criteria, graph_root)
            else:
                _gen_stacked_linegraph(graph, cmdopts, criteria, graph_root)


def _gen_summary_linegraph(graph: types.YAMLDict,
                           cmdopts:  types.Cmdopts,
                           criteria: bc.IConcreteBatchCriteria,
                           graph_root: pathlib.Path) -> None:
    opath = graph_root / ('SM-' + graph['dest_stem'] + config.kImageExt)

    ln = SummaryLineGraph(stats_root=cmdopts['batch_stat_collate_root'],
                          input_stem=graph['dest_stem'],
                          output_fpath=opath,
                          stats=cmdopts['dist_stats'],
                          model_root=cmdopts['batch_model_root'],
                          title=graph['title'],
                          xlabel=criteria.graph_xlabel(cmdopts),
                          ylabel=graph.get('ylabel', None),
                          xticks=criteria.graph_xticks(cmdopts),
                          xtick_labels=criteria.graph_xticklabels(
        cmdopts),
        logyscale=cmdopts['plot_log_yscale'],
        large_text=cmdopts['plot_large_text'])
    ln.generate()


def _gen_stacked_linegraph(graph: types.YAMLDict,
                           cmdopts:  types.Cmdopts,
                           criteria: bc.IConcreteBatchCriteria,
                           graph_root: pathlib.Path) -> None:
    opath = graph_root / ('SLN-' + graph['dest_stem'] +
                          config.kImageExt)

    ln = StackedLineGraph(stats_root=cmdopts['batch_stat_collate_root'],
                          input_stem=graph['dest_stem'],
                          output_fpath=opath,
                          stats=cmdopts['dist_stats'],
                          dashstyles=graph.get('dashes', None),
                          linestyles=graph.get('lines', None),
                          title=graph['title'],
                          xlabel=graph.get('xlabel', None),
                          ylabel=graph.get('ylabel', None),
                          logyscale=cmdopts['plot_log_yscale'],
                          large_text=cmdopts['plot_large_text'])

    ln.generate()


__api__ = [
    "generate"
]