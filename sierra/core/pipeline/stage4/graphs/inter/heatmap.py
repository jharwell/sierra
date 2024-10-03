#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import typing as tp
import pathlib
import logging
import re
import glob

# 3rd party packages
import json

# Project packages
from sierra.core import types, config,
from sierra.core.variables import batch_criteria as bc
from sierra.core.graphs.heatmap import Heatmap

_logger = logging.getLogger(__name__)


def generate(cmdopts: types.Cmdopts,
             pathset: batchroot.PathSet,
             targets: tp.List[types.YAMLDict],
             criteria: bc.IConcreteBatchCriteria) -> None:
    """Generate heatmaps from: term: `Collated .csv` files.

    The graphs generated by this module respect the ``--exp-range`` cmdline
    option.
    """

    _logger.info("Heatmaps from %s", pathlib.Path)

    # For each category of heatmaps we are generating
    for category in targets:

        # For each graph in each category
        for graph in category['graphs']:
            _logger.trace('\n' +  # type: ignore
                          json.dumps(graph, indent=4))

            pattern = str(pathset.stat_collate_root / (graph['dest_stem'] + "*" +
                                                       config.kStats['mean'].exts['mean']))
            specs = {}
            for f in glob.glob(pattern):
                if res := re.search('_[0-9]+', f):
                    interval = int(res.group(0)[1:])
                    specs[interval] = pathlib.Path(f)

            for interval, ipath in specs.items():
                _generate_hm(graph=graph,
                             graph_collate_root=pathset.graph_collate_root,
                             cmdopts=cmdopts,
                             criteria=criteria,
                             interval=interval,
                             ipath=ipath)


def _generate_hm(graph: types.YAMLDict,
                 graph_collate_root: pathlib.Path,
                 cmdopts: types.Cmdopts,
                 criteria: bc.IConcreteBatchCriteria,
                 interval: int,
                 ipath: pathlib.Path) -> None:

    odir = graph_root / ("HM-" + graph['dest_stem'])
    odir.mkdir(parents=True, exist_ok=True)
    opath = odir / ('HM-{0}_{1}{2}'.format(graph['dest_stem'],
                                           interval,
                                           config.kImageExt))

    if title := graph.get('title', None):
        title += f" (Interval={interval})"

    hm = Heatmap(input_fpath=ipath,
                 output_fpath=opath,
                 title=title,
                 xlabel=criteria.graph_xlabel(cmdopts),
                 ylabel=criteria.graph_ylabel(cmdopts),
                 transpose=cmdopts['plot_transpose_graphs'],
                 interpolation=graph.get('interpolation', None),
                 zlabel=graph.get('zlabel', None),
                 large_text=cmdopts['plot_large_text'])

    hm.generate()


__api__ = [
    'generate'
]
