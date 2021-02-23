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

# Project packages
import core.perf_measures.scalability as pms
import core.perf_measures.self_organization as pmso
import core.perf_measures.raw as pmraw
import core.perf_measures.robustness as pmb
import core.perf_measures.flexibility as pmf
import core.utils
from core.graphs.stacked_line_graph import StackedLineGraph
from core.graphs.summary_line_graph import SummaryLinegraph
from core.variables import batch_criteria as bc
import core.config


class InterExpGraphGenerator:
    """
    Generates graphs from collated ``.csv`` files across experiments in a batch. Which graphs are
    generated is controlled by (1) YAML configuration files parsed in
    :class:`~core.pipeline.stage4.pipeline_stage4.PipelineStage4` (2) which batch criteria was used
    (for performance measures).

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

        core.utils.dir_create_checked(self.cmdopts['batch_graph_collate_root'], exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Runs the following to generate graphs across experiments in the batch:

        #. :class:`~core.pipeline.stage4.inter_exp_graph_generator.LinegraphsGenerator`
           to generate linegraphs (univariate batch criteria only).

        #. :class:`~core.pipeline.stage4.inter_exp_graph_generator.UnivarPerfMeasuresGenerator`
           to performance measures (univariate batch criteria only).

        #. :class:`~core.pipeline.stage4.inter_exp_graph_generator.BivarPerfMeasuresGenerator`
           to generate performance measures (bivariate batch criteria only).
        """

        if criteria.is_univar():
            if not self.cmdopts['project_no_yaml_LN']:
                LinegraphsGenerator(self.cmdopts, self.targets).generate(criteria)
            UnivarPerfMeasuresGenerator(self.main_config, self.cmdopts)(criteria)
        else:
            BivarPerfMeasuresGenerator(self.main_config, self.cmdopts)(criteria)


class LinegraphsGenerator:
    """
    Generates linegraphs from collated .csv data across a batch of experiments. The graphs generated
    by this class ignore the ``--exp-range`` cmdline option.

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
                if graph.get('summary', False):
                    SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                                     input_stem=graph['dest_stem'],
                                     output_fpath=os.path.join(self.cmdopts['batch_graph_collate_root'],
                                                               'SM-' + graph['dest_stem'] + core.config.kImageExt),
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
                                                               core.config.kImageExt),
                                     stats=self.cmdopts['dist_stats'],
                                     dashstyles=graph.get('dashes', None),
                                     linestyles=graph.get('lines', None),
                                     title=graph['title'],
                                     xlabel=graph['xlabel'],
                                     ylabel=graph['ylabel'],
                                     logyscale=self.cmdopts['plot_log_yscale'],
                                     large_text=self.cmdopts['plot_large_text']).generate()


class UnivarPerfMeasuresGenerator:
    """
    Generates performance measures from collated .csv data across a batch of experiments. Which
    measures are generated is controlled by the batch criteria used for the experiment. Univariate
    batch criteria only.

    Attributes:
        cmdopts: Dictionary of parsed cmdline options.
        main_config: Dictionary of parsed main YAML config.
    """

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any]) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        perf_csv = self.main_config['perf']['intra_perf_csv']
        perf_col = self.main_config['perf']['intra_perf_col']
        interference_csv = self.main_config['perf']['intra_interference_csv']
        interference_col = self.main_config['perf']['intra_interference_col']
        raw_title = self.main_config['perf']['raw_perf_title']
        raw_ylabel = self.main_config['perf']['raw_perf_ylabel']

        if criteria.pm_query('raw'):
            pmraw.SteadyStateRawUnivar(self.cmdopts, perf_csv, perf_col).from_batch(criteria,
                                                                                    title=raw_title,
                                                                                    ylabel=raw_ylabel)
        if criteria.pm_query('scalability'):
            pms.ScalabilityUnivarGenerator()(perf_csv, perf_col, self.cmdopts, criteria)

        if criteria.pm_query('self-org'):
            pmso.SelfOrgUnivarGenerator()(self.cmdopts,
                                          perf_csv,
                                          perf_col,
                                          interference_csv,
                                          interference_col,
                                          criteria)

        if criteria.pm_query('flexibility'):
            pmf.FlexibilityUnivarGenerator()(self.cmdopts,
                                             self.main_config,
                                             criteria)

        if criteria.pm_query('robustness_pd') or criteria.pm_query('robustness_saa'):
            pmb.RobustnessUnivarGenerator()(self.cmdopts,
                                            self.main_config,
                                            criteria)


class BivarPerfMeasuresGenerator:
    """
    Generates performance measures from collated .csv data across a batch of experiments. Which
    measures are generated is controlled by the batch criteria used for the experiment. Bivariate
    batch criteria only.

    Attributes:
        cmdopts: Dictionary of parsed cmdline options.
        main_config: Dictionary of parsed main YAML config.
    """

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any]) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        perf_csv = self.main_config['perf']['intra_perf_csv']
        perf_col = self.main_config['perf']['intra_perf_col']
        interference_csv = self.main_config['perf']['intra_interference_csv']
        interference_col = self.main_config['perf']['intra_interference_col']
        raw_title = self.main_config['perf']['raw_perf_title']

        if criteria.pm_query('raw'):
            pmraw.SteadyStateRawBivar(self.cmdopts,
                                      perf_csv=perf_csv,
                                      perf_col=perf_col).from_batch(criteria,
                                                                    title=raw_title)

        if criteria.pm_query('scalability'):
            pms.ScalabilityBivarGenerator()(perf_csv, perf_col, self.cmdopts, criteria)

        if criteria.pm_query('self-org'):
            pmso.SelfOrgBivarGenerator()(self.cmdopts,
                                         perf_csv,
                                         perf_col,
                                         interference_csv,
                                         interference_col,
                                         criteria)

        if criteria.pm_query('flexibility'):
            pmf.FlexibilityBivarGenerator()(self.cmdopts,
                                            self.main_config,
                                            criteria)

        if criteria.pm_query('robustness_pd') or criteria.pm_query('robustness_saa'):
            pmb.RobustnessBivarGenerator()(self.cmdopts,
                                           self.main_config,
                                           criteria)


__api__ = ['InterExpGraphGenerator',
           'BivarPerfMeasuresGenerator',
           'UnivarPerfMeasuresGenerator',
           'LinegraphsGenerator']
