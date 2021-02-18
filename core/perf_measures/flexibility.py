# Copyright 2018 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
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
"""
Measures for swarm flexibility in univariate and bivariate batched experiments.

"""

# Core packages
import os
import copy
import logging
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
from core.graphs.summary_line_graph import SummaryLinegraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import vcs
import core.variables.batch_criteria as bc
import core.perf_measures.common as common
import core.variables.temporal_variance as tv
import core.utils
import core.config

################################################################################
# Univariate Classes
################################################################################


class ReactivityUnivar:
    """
    Calculates the reactivity of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data.
    """
    kLeaf = 'PM-reactivity'

    @staticmethod
    def df_kernel(criteria: bc.BivarBatchCriteria,
                  main_config: dict,
                  cmdopts: dict,
                  stat_ext: str,
                  raw_df: pd.DataFrame):

        df = pd.DataFrame(columns=raw_df.columns[1:], index=[0])

        for i in range(len(raw_df.columns)):
            df[df.columns[i]] = vcs.ReactivityCS(main_config,
                                                 cmdopts,
                                                 criteria,
                                                 stat_ext,
                                                 0,
                                                 i + 1)()
        return df

    def __init__(self, main_config: dict, cmdopts: dict, inter_perf_csv: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        """
        Calculate the reactivity metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """

        _stats_prepare(self.main_config,
                       self.cmdopts,
                       criteria,
                       self.inter_perf_leaf,
                       self.kLeaf,
                       self.df_kernel)

        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=opath,
                         title="Swarm Reactivity",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel=vcs.method_ylabel(self.cmdopts["reactivity_cs_method"],
                                                  'reactivity'),
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
                         xtick_labels=criteria.graph_xticklabels(self.cmdopts)[1:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class AdaptabilityUnivar:
    """
    Calculates the adaptability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data.
    """
    kLeaf = 'PM-adaptability'

    @staticmethod
    def df_kernel(criteria: bc.BivarBatchCriteria,
                  main_config: dict,
                  cmdopts: dict,
                  stat_ext: str,
                  raw_df: pd.DataFrame):

        df = pd.DataFrame(columns=raw_df.columns[1:], index=[0])

        for i in range(len(raw_df.columns)):
            df[df.columns[i]] = vcs.AdaptabilityCS(main_config,
                                                   cmdopts,
                                                   criteria,
                                                   stat_ext,
                                                   0,
                                                   i + 1)()
        return df

    def __init__(self, main_config: dict, cmdopts: dict, inter_perf_csv: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        """
        Calculate the adaptability metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """

        _stats_prepare(self.main_config,
                       self.cmdopts,
                       criteria,
                       self.inter_perf_leaf,
                       self.kLeaf,
                       self.df_kernel)

        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=opath,
                         title="Swarm Adaptability",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel=vcs.method_ylabel(self.cmdopts["adaptability_cs_method"],
                                                  'adaptability'),
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
                         xtick_labels=criteria.graph_xticklabels(self.cmdopts)[1:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class FlexibilityUnivarGenerator:
    """
    Calculates the flexibility of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data in the following ways:

    - Reactivity
    - Adaptability
    - Weight reactivity+adaptability
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: dict,
                 main_config: dict,
                 inter_perf_csv: str,
                 alpha_SAA: float,
                 alpha_PD: float,
                 criteria: bc.IConcreteBatchCriteria):
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        ReactivityUnivar(main_config, cmdopts, inter_perf_csv).from_batch(criteria)
        AdaptabilityUnivar(main_config, cmdopts, inter_perf_csv).from_batch(criteria)

        title1 = r'Swarm Flexbility '
        title2 = r'($\alpha_{{F_{{R}}}}={0},\alpha_{{F_{{A}}}}={1}$)'.format(alpha_SAA,
                                                                             alpha_PD)
        w = common.WeightedPMUnivar(cmdopts=cmdopts,
                                    output_leaf='PM-flexibility',
                                    ax1_leaf=ReactivityUnivar.kLeaf,
                                    ax2_leaf=AdaptabilityUnivar.kLeaf,
                                    ax1_alpha=alpha_SAA,
                                    ax2_alpha=alpha_PD,
                                    title=title1 + title2)
        w.generate(criteria)

################################################################################
# Bivariate Classes
################################################################################


class ReactivityBivar:
    """
    Calculates the reactivity of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data.

    """
    kLeaf = 'PM-reactivity'

    @staticmethod
    def df_kernel(criteria: bc.BivarBatchCriteria,
                  main_config: dict,
                  cmdopts: dict,
                  stat_ext: str,
                  raw_df: pd.DataFrame) -> pd.DataFrame:
        df = pd.DataFrame(columns=raw_df.columns, index=raw_df.index)
        exp_dirs = criteria.gen_exp_dirnames(cmdopts)

        for i in range(0, len(df.index)):
            for j in range(0, len(df.columns)):
                # We need to know which of the 2 variables was temporal variance, in order to
                # determine the correct dimension along which to compute the metric.
                if isinstance(criteria.criteria1, tv.TemporalVariance) or cmdopts['plot_primary_axis'] == '0':
                    val = vcs.ReactivityCS(main_config,
                                           cmdopts,
                                           criteria,
                                           stat_ext,
                                           j,  # exp0 in first row with i=0
                                           i)(exp_dirs)
                else:
                    val = vcs.ReactivityCS(main_config,
                                           cmdopts,
                                           criteria,
                                           stat_ext,
                                           i * len(df.columns),  # exp0 in first col with j=0
                                           i * len(df.columns) + j)(exp_dirs)

                df.iloc[i, j] = val
        return df

    def __init__(self, main_config: dict, cmdopts: dict, inter_perf_csv: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        """
        Generate a reactivity graph for a given controller in a given scenario by computing the
        value of the reactivity metric for each experiment within the batch, and plot
        a :class:`~core.graphs.heatmap.Heatmap` of the reactivity variable vs. the other one.

        Returns:
           The path to the `.csv` file used to generate the heatmap.
        """
        _stats_prepare(self.main_config,
                       self.cmdopts,
                       criteria,
                       self.inter_perf_leaf,
                       self.kLeaf,
                       self.df_kernel)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"], self.kLeaf + '.csv')
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title='Swarm Reactivity',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


class AdaptabilityBivar:
    """
    Calculates the adaptability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data.

    """
    kLeaf = 'PM-adaptability'

    @staticmethod
    def df_kernel(criteria: bc.BivarBatchCriteria,
                  main_config: dict,
                  cmdopts: dict,
                  stat_ext: str,
                  raw_df: pd.DataFrame) -> pd.DataFrame:
        df = pd.DataFrame(columns=raw_df.columns, index=raw_df.index)

        exp_dirs = criteria.gen_exp_dirnames(cmdopts)

        for i in range(0, len(df.index)):
            for j in range(0, len(df.columns)):
                # We need to know which of the 2 variables was temporal variance, in order to
                # determine the correct dimension along which to compute the metric.
                if isinstance(criteria.criteria1, tv.TemporalVariance) or cmdopts['plot_primary_axis'] == '0':
                    val = vcs.AdaptabilityCS(main_config,
                                             cmdopts,
                                             criteria,
                                             stat_ext,
                                             j,  # exp0 in first row with i=0
                                             i)(exp_dirs)
                else:
                    val = vcs.AdaptabilityCS(main_config,
                                             cmdopts,
                                             criteria,
                                             stat_ext,
                                             i * len(df.columns),  # exp0 in first col with j=0
                                             i * len(df.columns) + j)(exp_dirs)

                df.iloc[i, j] = val

        return df

    def __init__(self, main_config: dict, cmdopts: dict, inter_perf_csv: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        """
        Generate a adaptability graph for a given controller in a given scenario by computing the
        value of the adaptability metric for each experiment within the batch, and plot
        a :class:`~core.graphs.heatmap.Heatmap` of the adaptability variable vs. the other one.
        """
        _stats_prepare(self.main_config,
                       self.cmdopts,
                       criteria,
                       self.inter_perf_leaf,
                       self.kLeaf,
                       self.df_kernel)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"], self.kLeaf + '.csv')
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title='Swarm Adaptability',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


class FlexibilityBivarGenerator:
    """
    Calculates the flexibility of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in the following ways:

    - Reactivity
    - Adaptability
    - Weight reactivity+adaptability
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: dict,
                 main_config: dict,
                 inter_perf_csv: str,
                 alpha_SAA: float,
                 alpha_PD: float,
                 criteria: bc.IConcreteBatchCriteria):
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        ReactivityBivar(main_config, cmdopts, inter_perf_csv).from_batch(criteria)
        AdaptabilityBivar(main_config, cmdopts, inter_perf_csv).from_batch(criteria)

        title1 = 'Swarm Flexbility '
        title2 = r'($\alpha_{{F_{{R}}}}={0},\alpha_{{F_{{A}}}}={1}$)'.format(alpha_SAA,
                                                                             alpha_PD)
        w = common.WeightedPMBivar(cmdopts=cmdopts,
                                   output_leaf='pm-flexibility',
                                   ax1_leaf=ReactivityBivar.kLeaf,
                                   ax2_leaf=AdaptabilityBivar.kLeaf,
                                   ax1_alpha=alpha_SAA,
                                   ax2_alpha=alpha_PD,
                                   title=title1 + title2)
        w.generate(criteria)


def _stats_prepare(main_config: dict,
                   cmdopts: dict,
                   criteria: bc.IConcreteBatchCriteria,
                   inter_perf_ileaf: str,
                   oleaf: str,
                   kernel) -> None:
    for k in core.config.kStatsExtensions.keys():
        stat_ipath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  inter_perf_ileaf + core.config.kStatsExtensions[k])
        stat_opath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  oleaf + core.config.kStatsExtensions[k])
        if core.utils.path_exists(stat_ipath):
            stat_df = kernel(criteria,
                             main_config,
                             cmdopts,
                             core.config.kStatsExtensions[k],
                             core.utils.pd_csv_read(stat_ipath))
            core.utils.pd_csv_write(stat_df, stat_opath, index=False)


__api__ = [
    'AdaptabilityUnivar',
    'ReactivityUnivar'
]
