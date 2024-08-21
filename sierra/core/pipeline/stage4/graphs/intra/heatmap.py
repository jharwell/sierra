#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import typing as tp
import pathlib
import logging

# 3rd party packages
import json

# Project packages
from sierra.core import types, config
from sierra.core.models.graphs import IntraExpModel2DGraphSet
from sierra.core.graphs.heatmap import Heatmap

_logger = logging.getLogger(__name__)


def generate(cmdopts: types.Cmdopts,
             targets: tp.List[types.YAMLDict]) -> None:
    """
    Generate heatmaps from: term: `Averaged .csv` files for a single experiment.
    """
    exp_stat_root = pathlib.Path(cmdopts['exp_stat_root'])
    exp_graph_root = pathlib.Path(cmdopts["exp_graph_root"])
    exp_model_root = pathlib.Path(cmdopts["exp_model_root"])
    large_text = cmdopts['plot_large_text']

    targets = targets

    _logger.info("Heatmaps from %s", exp_stat_root)

    # For each category of heatmaps we are generating
    for category in targets:

        # For each graph in each category
        for graph in category['graphs']:
            _logger.trace('\n' +  # type: ignore
                          json.dumps(graph, indent=4))
            if IntraExpModel2DGraphSet.model_exists(exp_model_root,
                                                    graph['src_stem']):
                IntraExpModel2DGraphSet(exp_stat_root,
                                        exp_model_root,
                                        exp_graph_root,
                                        graph['src_stem'],
                                        graph.get('title', None)).generate()
            else:
                input_fpath = exp_stat_root / (graph['src_stem'] +
                                               config.kStats['mean'].exts['mean'])
                output_fpath = exp_graph_root / ('HM-' + graph['src_stem'] +
                                                 config.kImageExt)

                Heatmap(input_fpath=input_fpath,
                        output_fpath=output_fpath,
                        title=graph.get('title', None),
                        xlabel='X',
                        ylabel='Y',
                        large_text=large_text).generate()


__api__ = [
    'generate'
]
