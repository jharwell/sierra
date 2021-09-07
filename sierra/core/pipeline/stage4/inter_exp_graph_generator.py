# Copyright 2018 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#

"""
Classes for generating graphs across experiments in a batch.
"""

# Core packages
import os
import copy
import logging
import typing as tp

# 3rd party packages
import json

# Project packages
import sierra.core.utils
from sierra.core.graphs.stacked_line_graph import StackedLineGraph
from sierra.core.graphs.summary_line_graph import SummaryLinegraph
from sierra.core.variables import batch_criteria as bc
import sierra.core.config


class InterExpGraphGenerator:
    """
    Generates graphs from collated ``.csv`` files across experiments in a batch. Which graphs are
    generated can be controlled by:

    #. YAML configuration files parsed in
    :class:`~sierra.core.pipeline.stage4.pipeline_stage4.PipelineStage4`

    #. The batch criteria was used (if this class is extended in a ``--project``).

    """

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 targets: tp.List[tp.Dict[str, tp.Any]]) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.targets = targets

        sierra.core.utils.dir_create_checked(
            self.cmdopts['batch_graph_collate_root'], exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Runs the following to generate graphs across experiments in the batch:

        #. :class:`~sierra.core.pipeline.stage4.inter_exp_graph_generator.LinegraphsGenerator`
           to generate linegraphs (univariate batch criteria only).
        """

        if criteria.is_univar():
            if not self.cmdopts['project_no_yaml_LN']:
                LinegraphsGenerator(self.cmdopts, self.targets).generate(criteria)


class LinegraphsGenerator:
    """
    Generates linegraphs from collated .csv data across a batch of experiments. The graphs generated
    by this class respect the ``--exp-range`` cmdline option.

    Attributes:
      batch_stat_collate_root: Absolute path to root directory for collated csvs.
      batch_graph_root: Absolute path to root directory where the generated graphs should be saved.
      targets: Dictionary of parsed YAML configuration controlling what graphs should be generated.
    """

    def __init__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 targets: tp.List[tp.Dict[str, tp.Any]]) -> None:
        self.cmdopts = cmdopts
        self.targets = targets
        self.logger = logging.getLogger(__name__)

    def generate(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("Linegraphs from %s", self.cmdopts['batch_stat_collate_root'])
        # For each category of linegraphs we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                self.logger.trace('\n' + json.dumps(graph, indent=4))
                if graph.get('summary', False):
                    SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                                     input_stem=graph['dest_stem'],
                                     output_fpath=os.path.join(self.cmdopts['batch_graph_collate_root'],
                                                               'SM-' + graph['dest_stem'] + sierra.core.config.kImageExt),
                                     stats=self.cmdopts['dist_stats'],
                                     model_root=self.cmdopts['batch_model_root'],
                                     title=graph['title'],
                                     xlabel=criteria.graph_xlabel(self.cmdopts),
                                     ylabel=graph['ylabel'],
                                     xticks=criteria.graph_xticks(self.cmdopts),
                                     xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                                     logyscale=self.cmdopts['plot_log_yscale'],
                                     large_text=self.cmdopts['plot_large_text']).generate()
                else:
                    StackedLineGraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                                     input_stem=graph['dest_stem'],
                                     output_fpath=os.path.join(self.cmdopts['batch_graph_collate_root'],
                                                               'SLN-' + graph['dest_stem'] +
                                                               sierra.core.config.kImageExt),
                                     stats=self.cmdopts['dist_stats'],
                                     dashstyles=graph.get('dashes', None),
                                     linestyles=graph.get('lines', None),
                                     title=graph['title'],
                                     xlabel=graph['xlabel'],
                                     ylabel=graph['ylabel'],
                                     logyscale=self.cmdopts['plot_log_yscale'],
                                     large_text=self.cmdopts['plot_large_text']).generate()


__api__ = ['InterExpGraphGenerator',
           'LinegraphsGenerator']
