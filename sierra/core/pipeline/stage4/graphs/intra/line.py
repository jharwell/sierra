#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import typing as tp
import logging

# 3rd party packages
import json

# Project packages
from sierra.core import types, config
from sierra.core.graphs.stacked_line_graph import StackedLineGraph

_logger = logging.getLogger(__name__)


def generate(cmdopts: types.Cmdopts,
             targets: tp.List[types.YAMLDict]) -> None:
    """
    Generate linegraphs from: term: `Averaged .csv` files within an experiment.
    """

    graph_root = pathlib.Path(cmdopts['exp_graph_root'])
    stats_root = pathlib.Path(cmdopts['exp_stat_root'])
    _logger.info("Linegraphs from %s", cmdopts['exp_stat_root'])

    # For each category of linegraphs we are generating
    for category in targets:

        # For each graph in each category
        for graph in category['graphs']:
            output_fpath = graph_root / ('SLN-' + graph['dest_stem'] +
                                         config.kImageExt)
            try:
                _logger.trace('\n' +  # type: ignore
                              json.dumps(graph, indent=4))
                StackedLineGraph(stats_root=stats_root,
                                 input_stem=graph['src_stem'],
                                 output_fpath=output_fpath,
                                 stats=cmdopts['dist_stats'],
                                 dashstyles=graph.get('dashes', None),
                                 linestyles=graph.get('styles', None),
                                 cols=graph.get('cols', None),
                                 title=graph.get('title', None),
                                 legend=graph.get('legend', None),
                                 xlabel=graph.get('xlabel', None),
                                 ylabel=graph.get('ylabel', None),
                                 logyscale=cmdopts['plot_log_yscale'],
                                 large_text=cmdopts['plot_large_text']).generate()
            except KeyError:
                _logger.fatal(("Could not generate linegraph. "
                               "Possible reasons include: "))

                _logger.fatal(("1. The YAML configuration entry is "
                               "missing required fields"))
                missing_cols = graph.get('cols', "MISSING_KEY")
                missing_stem = graph.get('src_stem', "MISSING_KEY")
                _logger.fatal(("2. 'cols' is present in YAML "
                               "configuration but some of %s are "
                               "missing from %s"),
                              missing_cols,
                              missing_stem)

                raise


__api__ = [
    'generate'
]
