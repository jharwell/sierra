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
import logging
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
from sierra.core.graphs.summary_line_graph import SummaryLinegraph
from sierra.core.graphs.heatmap import Heatmap
from sierra.core.perf_measures import vcs
import sierra.core.variables.batch_criteria as bc
import sierra.core.perf_measures.common as pmcommon
import sierra.core.variables.temporal_variance as tv
import sierra.core.utils
import sierra.core.config


class BaseSteadyStateReactivity:
    kLeaf = 'PM-ss-reactivity'


class BaseSteadyStateAdaptability:
    kLeaf = 'PM-ss-adaptability'

################################################################################
# Univariate Classes
################################################################################


class SteadyStateReactivityUnivar(BaseSteadyStateReactivity):
    """
    Calculates the reactivity of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data.
    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  main_config: tp.Dict[str, tp.Any],
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[pd.DataFrame, str]:
        rt_dfs = {}

        exp0 = list(collated_perf.keys())[0]
        exp0_perf_df = collated_perf[exp0]

        for i in range(1, criteria.n_exp()):
            expx = list(collated_perf.keys())[i]
            expx_perf_df = collated_perf[expx]
            rt_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns[1:],
                                        index=[0])  # Steady state

            for sim in expx_perf_df.columns:
                reactivity = vcs.ReactivityCS(main_config,
                                              cmdopts,
                                              criteria,
                                              ideal_num=0,
                                              exp_num=i).from_batch(ideal_perf_df=exp0_perf_df[sim],
                                                                    expx_perf_df=expx_perf_df[sim])
                rt_dfs[expx].loc[0, sim] = reactivity

        return rt_dfs

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate the reactivity metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.main_config, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + sierra.core.config.kImageExt)

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


class SteadyStateAdaptabilityUnivar(BaseSteadyStateAdaptability):
    """
    Calculates the adaptability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data.
    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  main_config: tp.Dict[str, tp.Any],
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[pd.DataFrame, str]:
        ad_dfs = {}

        exp0 = list(collated_perf.keys())[0]
        exp0_perf_df = collated_perf[exp0]

        for i in range(1, criteria.n_exp()):
            expx = list(collated_perf.keys())[i]
            expx_perf_df = collated_perf[expx]
            ad_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns[1:],
                                        index=[0])  # Steady state

            for sim in expx_perf_df.columns:
                adaptability = vcs.AdaptabilityCS(main_config,
                                                  cmdopts,
                                                  criteria).from_batch(ideal_num=0,
                                                                       ideal_perf_df=exp0_perf_df[sim],
                                                                       expx_perf_df=expx_perf_df[sim])
                ad_dfs[expx].loc[0, sim] = adaptability

        return ad_dfs

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate the adaptability metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.main_config, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + sierra.core.config.kImageExt)

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
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 main_config: tp.Dict[str, tp.Any],
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])
        perf_csv = main_config['perf']['intra_perf_csv']
        perf_col = main_config['perf']['intra_perf_col']

        SteadyStateReactivityUnivar(main_config, cmdopts, perf_csv, perf_col).from_batch(criteria)
        SteadyStateAdaptabilityUnivar(main_config, cmdopts, perf_csv, perf_col).from_batch(criteria)

################################################################################
# Bivariate Classes
################################################################################


class SteadyStateReactivityBivar(BaseSteadyStateReactivity):
    """
    Calculates the reactivity of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data.

    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  main_config: tp.Dict[str, tp.Any],
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        exp_dirs = criteria.gen_exp_dirnames(cmdopts)
        rt_dfs = {}

        for i in range(axis == 0, xsize):
            for j in range(axis == 1, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_perf_df = collated_perf[expx]
                rt_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state
                for sim in expx_perf_df.columns:
                    if axis == 0:
                        exp_ideal = list(collated_perf.keys())[j]  # exp0 in first row with i=0
                        ideal_perf_df = collated_perf[exp_ideal]

                        reactivity = vcs.ReactivityCS(main_config,
                                                      cmdopts,
                                                      criteria,
                                                      ideal_num=j,
                                                      exp_num=i).from_batch(ideal_perf_df=ideal_perf_df[sim],
                                                                            expx_perf_df=expx_perf_df[sim],
                                                                            exp_dirs=exp_dirs)
                    else:
                        # exp0 in first col with j=0
                        exp_ideal = list(collated_perf.keys())[i * ysize]
                        ideal_perf_df = collated_perf[exp_ideal]

                        if axis == 0:
                            reactivity = vcs.ReactivityCS(main_config,
                                                          cmdopts,
                                                          criteria.criteria1,
                                                          ideal_num=i * ysize,
                                                          exp_num=i * ysize + j).from_batch(ideal_perf_df=ideal_perf_df[sim],
                                                                                            expx_perf_df=expx_perf_df[sim],
                                                                                            exp_dirs=exp_dirs)
                        else:
                            reactivity = vcs.ReactivityCS(main_config,
                                                          cmdopts,
                                                          criteria.criteria2,
                                                          ideal_num=i * ysize,
                                                          exp_num=i * ysize + j).from_batch(ideal_perf_df=ideal_perf_df[sim],
                                                                                            expx_perf_df=expx_perf_df[sim],
                                                                                            exp_dirs=exp_dirs)
                    rt_dfs[expx].loc[0, sim] = reactivity

        return rt_dfs

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate a reactivity graph for a given controller in a given scenario by computing the
        value of the reactivity metric for each experiment within the batch, and plot
        a :class:`~sierra.core.graphs.heatmap.Heatmap` of the reactivity variable vs. the other one.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        # We need to know which of the 2 variables was temporal variance, in order to
        # determine the correct dimension along which to compute the metric.
        axis = sierra.core.utils.get_primary_axis(criteria,
                                                  [tv.TemporalVariance],
                                                  self.cmdopts)

        pm_dfs = self.df_kernel(criteria, self.main_config, self.cmdopts, axis, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True, axis)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                             self.kLeaf + sierra.core.config.kStatsExtensions['mean'])
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + sierra.core.config.kImageExt)

        axis = sierra.core.utils.get_primary_axis(criteria, [tv.TemporalVariance], self.cmdopts)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title='Swarm Reactivity',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class SteadyStateAdaptabilityBivar(BaseSteadyStateAdaptability):
    """
    Calculates the adaptability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data.

    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  main_config: tp.Dict[str, tp.Any],
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        exp_dirs = criteria.gen_exp_dirnames(cmdopts)
        ad_dfs = {}

        for i in range(axis == 0, xsize):
            for j in range(axis == 1, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_perf_df = collated_perf[expx]
                ad_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state
                for sim in expx_perf_df.columns:
                    if axis == 0:
                        exp_ideal = list(collated_perf.keys())[j]  # exp0 in first row with i=0
                        ideal_perf_df = collated_perf[exp_ideal]

                        adaptability = vcs.AdaptabilityCS(main_config,
                                                          cmdopts,
                                                          criteria).from_batch(ideal_num=j,
                                                                               ideal_perf_df=ideal_perf_df[sim],
                                                                               expx_perf_df=expx_perf_df[sim],
                                                                               exp_dirs=exp_dirs)
                    else:
                        # exp0 in first col with j=0
                        exp_ideal = list(collated_perf.keys())[i * ysize]
                        ideal_perf_df = collated_perf[exp_ideal]

                        adaptability = vcs.AdaptabilityCS(main_config,
                                                          cmdopts,
                                                          criteria).from_batch(ideal_num=i * ysize,
                                                                               ideal_perf_df=ideal_perf_df[sim],
                                                                               expx_perf_df=expx_perf_df[sim],
                                                                               exp_dirs=exp_dirs)
                    ad_dfs[expx].loc[0, sim] = adaptability
        return ad_dfs

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate a adaptability graph for a given controller in a given scenario by computing the
        value of the adaptability metric for each experiment within the batch, and plot
        a: class: `~sierra.core.graphs.heatmap.Heatmap` of the adaptability variable vs. the other one.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        # We need to know which of the 2 variables was temporal variance, in order to
        # determine the correct dimension along which to compute the metric.
        axis = sierra.core.utils.get_primary_axis(criteria,
                                                  [tv.TemporalVariance],
                                                  self.cmdopts)

        pm_dfs = self.df_kernel(criteria, self.main_config, self.cmdopts, axis, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True, axis)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                             self.kLeaf + sierra.core.config.kStatsExtensions['mean'])
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + sierra.core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title='Swarm Adaptability',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class FlexibilityBivarGenerator:
    """
    Calculates the flexibility of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in the following ways:

    - Reactivity
    - Adaptability
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 main_config: tp.Dict[str, tp.Any],
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])
        perf_csv = main_config['perf']['intra_perf_csv']
        perf_col = main_config['perf']['intra_perf_col']

        SteadyStateReactivityBivar(main_config, cmdopts, perf_csv, perf_col).from_batch(criteria)
        SteadyStateAdaptabilityBivar(main_config, cmdopts, perf_csv, perf_col).from_batch(criteria)


__api__ = [
    'BaseSteadyStateAdaptability',
    'BaseSteadyStateReactivity',

    'SteadyStateAdaptabilityUnivar',
    'SteadyStateReactivityUnivar',

    'SteadyStateAdaptabilityBivar',
    'SteadyStateReactivityBivar'
]
