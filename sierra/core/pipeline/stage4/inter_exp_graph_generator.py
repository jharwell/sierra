# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#

"""
Classes for generating graphs across experiments in a batch.
"""

# Core packages
import copy
import typing as tp
import logging
import pathlib
import glob
import re

# 3rd party packages
import json

# Project packages
from sierra.core.graphs.stacked_line_graph import StackedLineGraph
from sierra.core.graphs.summary_line_graph import SummaryLineGraph
from sierra.core.graphs.heatmap import Heatmap
from sierra.core.variables import batch_criteria as bc
from sierra.core import types, config, utils


class InterExpGraphGenerator:
    """Generates graphs from :term:`Collated .csv` files.

    Which graphs are generated can be controlled by YAML configuration
    files parsed in
    :class:`~sierra.core.pipeline.stage4.pipeline_stage4.PipelineStage4`.


    This class can be extended/overriden using a :term:`Project` hook. See
    :ref:`ln-sierra-tutorials-project-hooks` for details.

    Attributes:

        cmdopts: Dictionary of parsed cmdline attributes.

        main_config: Parsed dictionary of main YAML configuration

        LN_targets: A list of dictionaries, where each dictionary defines an
                    inter-experiment linegraph to generate.

        HM_targets: A list of dictionaries, where each dictionary defines an
                    inter-experiment heatmap to generate.

        logger: The handle to the logger for this class. If you extend this
               class, you should save/restore this variable in tandem with
               overriding it in order to get logging messages have unique logger
               names between this class and your derived class, in order to
               reduce confusion.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts,
                 LN_targets: tp.List[types.YAMLDict],
                 HM_targets: tp.List[types.YAMLDict]) -> None:
        # Copy because we are modifying it and don't want to mess up the
        # arguments for graphs that are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.LN_targets = LN_targets
        self.HM_targets = HM_targets

        utils.dir_create_checked(self.cmdopts['batch_graph_collate_root'],
                                 exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate graphs.

        Performs the following steps:

        # . :class:`~sierra.core.pipeline.stage4.inter_exp_graph_generator.LineGraphsGenerator`
           to generate linegraphs (univariate batch criteria only).
        """
        if criteria.is_univar():
            if not self.cmdopts['project_no_LN']:
                LineGraphsGenerator(self.cmdopts,
                                    self.LN_targets).generate(criteria)
        else:
            if not self.cmdopts['project_no_HM']:
                HeatmapsGenerator(self.cmdopts,
                                  self.HM_targets).generate(criteria)


class LineGraphsGenerator:
    """Generates linegraphs from :term:`Collated .csv` files.

    The graphs generated by this class respect the ``--exp-range`` cmdline
    option.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 targets: tp.List[types.YAMLDict]) -> None:
        self.cmdopts = cmdopts
        self.targets = targets
        self.logger = logging.getLogger(__name__)

    def generate(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("LineGraphs from %s",
                         self.cmdopts['batch_stat_collate_root'])
        graph_root = pathlib.Path(self.cmdopts['batch_graph_collate_root'])

        # For each category of linegraphs we are generating
        for category in self.targets:

            # For each graph in each category
            for graph in category['graphs']:
                self.logger.trace('\n' +  # type: ignore
                                  json.dumps(graph, indent=4))
                if graph.get('summary', False):
                    self._gen_summary_linegraph(graph, criteria, graph_root)
                else:
                    self._gen_stacked_linegraph(graph, criteria, graph_root)

    def _gen_summary_linegraph(self,
                               graph: types.YAMLDict,
                               criteria: bc.IConcreteBatchCriteria,
                               graph_root: pathlib.Path) -> None:
        opath = graph_root / ('SM-' + graph['dest_stem'] + config.kImageExt)

        ln = SummaryLineGraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                              input_stem=graph['dest_stem'],
                              output_fpath=opath,
                              stats=self.cmdopts['dist_stats'],
                              model_root=self.cmdopts['batch_model_root'],
                              title=graph['title'],
                              xlabel=criteria.graph_xlabel(self.cmdopts),
                              ylabel=graph.get('ylabel', None),
                              xticks=criteria.graph_xticks(self.cmdopts),
                              xtick_labels=criteria.graph_xticklabels(
            self.cmdopts),
            logyscale=self.cmdopts['plot_log_yscale'],
            large_text=self.cmdopts['plot_large_text'])
        ln.generate()

    def _gen_stacked_linegraph(self,
                               graph: types.YAMLDict,
                               criteria: bc.IConcreteBatchCriteria,
                               graph_root: pathlib.Path) -> None:
        opath = graph_root / ('SLN-' + graph['dest_stem'] +
                              config.kImageExt)

        ln = StackedLineGraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                              input_stem=graph['dest_stem'],
                              output_fpath=opath,
                              stats=self.cmdopts['dist_stats'],
                              dashstyles=graph.get('dashes', None),
                              linestyles=graph.get('lines', None),
                              title=graph['title'],
                              xlabel=graph.get('xlabel', None),
                              ylabel=graph.get('ylabel', None),
                              logyscale=self.cmdopts['plot_log_yscale'],
                              large_text=self.cmdopts['plot_large_text'])

        ln.generate()


class HeatmapsGenerator:
    """Generates heatmaps from :term:`Collated .csv` files.

    The graphs generated by this class respect the ``--exp-range`` cmdline
    option.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 targets: tp.List[types.YAMLDict]) -> None:
        self.cmdopts = cmdopts
        self.targets = targets
        self.logger = logging.getLogger(__name__)
        self.stat_root = pathlib.Path(self.cmdopts['batch_stat_collate_root'])
        self.graph_root = pathlib.Path(self.cmdopts['batch_graph_collate_root'])

    def generate(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("Heatmaps from %s", self.stat_root)

        # For each category of heatmaps we are generating
        for category in self.targets:

            # For each graph in each category
            for graph in category['graphs']:
                self.logger.trace('\n' +  # type: ignore
                                  json.dumps(graph, indent=4))

                pattern = str(self.stat_root / (graph['dest_stem'] + "*" +
                                                config.kStats['mean'].exts['mean']))
                specs = {}
                for f in glob.glob(pattern):
                    if res := re.search('_[0-9]+', f):
                        interval = int(res.group(0)[1:])
                        specs[interval] = pathlib.Path(f)

                for interval, ipath in specs.items():
                    self._generate_hm(graph, criteria, interval, ipath)

    def _generate_hm(self, graph: types.YAMLDict,
                     criteria: bc.IConcreteBatchCriteria,
                     interval: int,
                     ipath: pathlib.Path) -> None:

        odir = self.graph_root / ("HM-" + graph['dest_stem'])
        odir.mkdir(parents=True, exist_ok=True)
        opath = odir / ('HM-{0}_{1}{2}'.format(graph['dest_stem'],
                                               interval,
                                               config.kImageExt))

        if title := graph.get('title', None):
            title += f" (Interval={interval})"

        hm = Heatmap(input_fpath=ipath,
                     output_fpath=opath,
                     title=title,
                     xlabel=criteria.graph_xlabel(self.cmdopts),
                     ylabel=criteria.graph_ylabel(self.cmdopts),
                     transpose=self.cmdopts['plot_transpose_graphs'],
                     interpolation=graph.get('interpolation', None),
                     zlabel=graph.get('zlabel', None),
                     large_text=self.cmdopts['plot_large_text'])

        hm. generate()


__api__ = [
    'InterExpGraphGenerator',
    'LineGraphsGenerator',
    'HeatmapsGenerator'


]
