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

r"""
Measures for swarm scalability in univariate and bivariate batched experiments.

. IMPORTANT:: The calculations performed by classes in this module make the following assumptions:

               - Different swarm sizes are used for at least `some` experiments in the batch.

               - exp0 has $\mathcal{N}=1$

               If these assumptions are violated, the calculations may still have some
               value/utility, but it will be reduced.
"""

# Core packages
import os
import logging
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
from core.graphs.summary_line_graph import SummaryLinegraph
from core.graphs.heatmap import Heatmap
import core.perf_measures.common as pmcommon
from core.variables import batch_criteria as bc
from core.variables import population_size
from core.variables import population_density
import core.utils
import core.config

################################################################################
# Base Classes
################################################################################


class BaseSteadyStateParallelFraction():
    r"""
    Given a swarm exhibiting speedup :math:`X` with :math:`m_i>1` robots relative to a swarm with
    fewer (:math:`N_1`) robots, compute the serial fraction :math:`e` of the swarm's
    performance. The lower the value of :math:`e`, the better the parallelization/scalability,
    suggesting that the addition of more robots will bring additional performance improvements:

    .. math::
       C(N_2,\kappa) = \sum_{t\in{T}}\theta_C(N_2,\kappa,t)

    or

    .. math::
       C(N_2,\kappa) = \sum_{t\in{T}}\frac{1}{1 + e^{-\theta_C(t)}} - \frac{1}{1 + e^{\theta_C(t)}}

    or

    .. math::
       C(N_2,\kappa) = -1 + 2\theta_C(t)

    where

    .. math::
       \theta_C(t) = 1.0 - \frac{\frac{1}{X} - \frac{1}{\frac{N_2}{N_1}}}{1 - \frac{1}{\frac{N_2}{N_1}}}

    depending on normalization configuration.

    Defined for swarms with :math:`N>1` robots. For :math:`N=1`, we obtain a Karp-Flatt value of 1.0
    using L'Hospital's rule and taking the derivative with respect to :math:`N`.

    Inspired by :xref:`Harwell2019`.
    """
    kLeaf = 'PM-ss-scalability-parallel-frac'

    @staticmethod
    def kernel(speedup_i: float,
               n_robots_i: int,
               n_robots_iminus1: int,
               normalize: bool,
               normalize_method: str) -> tp.Optional[float]:
        if n_robots_i > 1:
            size_ratio = float(n_robots_i) / float(n_robots_iminus1)
            e = (1.0 / speedup_i - 1.0 / size_ratio) / (1 - 1.0 / size_ratio)
        else:
            e = 1.0

        theta = 1.0 - e

        if normalize:
            if normalize_method == 'sigmoid':
                return core.utils.Sigmoid(theta)() - core.utils.Sigmoid(-theta)()
            else:
                return None
        else:
            return theta


class BaseSteadyStateNormalizedEfficiency():
    r"""
    Calculate for per-robot efficiency.

    .. math::
       E = \frac{P(N)}{N}

    Where :math:`P(N)` is an arbitrary performance measure, evaluated on a swarm of size
    :math:`N`.

    From :xref:`Hecker2015`.
    """
    kLeaf = 'PM-ss-scalability-efficiency'

    @staticmethod
    def kernel(perf_i: float, n_robots_i: int) -> float:
        return perf_i / float(n_robots_i)

################################################################################
# Univariate Classes
################################################################################


class SteadyStateNormalizedEfficiencyUnivar(BaseSteadyStateNormalizedEfficiency):
    r"""
    Univariate calculator for per-robot efficiency for each experiment in a batch
    (intra-experiment measure; no comparison across experiments in a batch is performed). See
    :class:`BaseSteadyStateNormalizedEfficiency` for calculations.
    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[pd.DataFrame, str]:
        populations = criteria.populations(cmdopts)
        sc_dfs = {}

        for i in range(0, criteria.n_exp()):
            n_robots_x = populations[i]
            expx = list(collated_perf.keys())[i]
            expx_perf_df = collated_perf[expx]
            sc_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                        index=[0])  # Steady state

            for sim in expx_perf_df.columns:
                perfN = expx_perf_df.loc[expx_perf_df.index[-1], sim]
                sc_dfs[expx].loc[0, sim] = BaseSteadyStateNormalizedEfficiency.kernel(perfN,
                                                                                      n_robots_x)

        return sc_dfs

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate efficiency metric for the given controller for each experiment in a
        batch. Calculated stats and/or metric model results are plotted along with the calculated
        metric, if they exist.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, False)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),

                         model_root=self.cmdopts['batch_model_root'],
                         title="Swarm Efficiency (normalized)",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="Efficiency",
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class SteadyStateParallelFractionUnivar(BaseSteadyStateParallelFraction):
    r"""
    Calculates the scalability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using the Karp-Flatt metric
    (See :class:`BaseSteadyStateParallelFraction`).
    """

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        size = len(criteria.gen_attr_changelist())
        sc_dfs = {}

        for i in range(1, size):
            expx = list(collated_perf.keys())[i]
            expx_df = collated_perf[expx]

            exp_iminus1 = list(collated_perf.keys())[i - 1]
            exp_iminus1_df = collated_perf[exp_iminus1]

            sc_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                        index=[0])  # Steady state

            for sim in collated_perf[expx].columns:
                perf_i = expx_df.loc[expx_df.index[-1], sim]
                n_robots_i = populations[i]

                perf_iminus1 = exp_iminus1_df.loc[exp_iminus1_df.index[-1], sim]
                n_robots_iminus1 = populations[i - 1]

                speedup_i = perf_i / perf_iminus1

                sc_dfs[expx].loc[0, sim] = BaseSteadyStateParallelFraction.kernel(speedup_i=speedup_i,
                                                                                  n_robots_i=n_robots_i,
                                                                                  n_robots_iminus1=n_robots_iminus1,
                                                                                  normalize=cmdopts['pm_scalability_normalize'],
                                                                                  normalize_method=cmdopts['pm_normalize_method'])
        return sc_dfs

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],
                         title="Swarm Parallel Performance Fraction",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class ScalabilityUnivarGenerator:
    """
    Calculates the scalability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 perf_csv: str,
                 perf_col: str,
                 cmdopts: tp.Dict[str, tp.Any],
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        SteadyStateNormalizedEfficiencyUnivar(cmdopts, perf_csv, perf_col).from_batch(criteria)
        SteadyStateParallelFractionUnivar(cmdopts, perf_csv, perf_col).from_batch(criteria)

################################################################################
# Bivariate Classes
################################################################################


class SteadyStateNormalizedEfficiencyBivar(BaseSteadyStateNormalizedEfficiency):
    """
    Bivariate calculator for per-robot efficiency for each experiment in a batch
    (intra-experiment measure; no comparison across experiments in a batch is performed). See
    :class:`BaseSteadyStateNormalizedEfficiency` for calculations.
    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:

        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        populations = criteria.populations(cmdopts)
        sc_dfs = {}

        for i in range(0, xsize):
            for j in range(0, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_df = collated_perf[expx]
                sc_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state

                for sim in expx_df.columns:
                    perf_x = expx_df.loc[expx_df.index[-1], sim]  # steady state
                    sc_dfs[expx].loc[0, sim] = BaseSteadyStateNormalizedEfficiency.kernel(perf_x,
                                                                                          populations[i][j])
        return sc_dfs

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate efficiency metric for the given controller for each experiment in a
        batch.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, False)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                             self.kLeaf + core.config.kStatsExtensions['mean'])
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title='Swarm Efficiency (Normalized)',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


class SteadyStateParallelFractionBivar(BaseSteadyStateParallelFraction):
    """
    Calculates the scalability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using the Karp-Flatt metric
    (See :class:`BaseSteadyStateParallelFraction`).
    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:

        populations = criteria.populations(cmdopts)
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        sc_dfs = {}

        for i in range(0, xsize):
            for j in range(0, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_df = collated_perf[expx]
                sc_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state
                for sim in expx_df.columns:
                    perf_x = expx_df.loc[expx_df.index[-1], sim]  # steady state

                    n_robots_x = populations[i][j]

                    if axis == 0:
                        exp_xminus1 = list(collated_perf.keys())[(i - 1) * ysize + j]
                        n_robots_xminus1 = populations[i - 1][j]
                    else:
                        exp_xminus1 = list(collated_perf.keys())[i * ysize + j - 1]
                        n_robots_xminus1 = populations[i][j - 1]

                    exp_xminus1_df = collated_perf[exp_xminus1]
                    perf_xminus1 = exp_xminus1_df.loc[exp_xminus1_df.index[-1], sim]  # steady state

                    speedup_i = perf_x / perf_xminus1
                    parallel_frac = BaseSteadyStateParallelFraction.kernel(speedup_i=speedup_i,
                                                                           n_robots_i=n_robots_x,
                                                                           n_robots_iminus1=n_robots_xminus1,
                                                                           normalize=cmdopts['pm_scalability_normalize'],
                                                                           normalize_method=cmdopts['pm_normalize_method'])
                    sc_dfs[expx].loc[0, sim] = parallel_frac

        return sc_dfs

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate efficiency metric for the given controller for each experiment in a
        batch. Calculated stats and/or metric model results are plotted along with the calculated
        metric, if they exist.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.

        axis = core.utils.get_primary_axis(criteria,
                                           [population_size.PopulationSize,
                                            population_density.PopulationConstantDensity],
                                           self. cmdopts)
        pm_dfs = self.df_kernel(criteria, self.cmdopts, axis, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True, axis)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                             self.kLeaf + core.config.kStatsExtensions['mean'])
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title="Swarm Parallel Performance Fraction",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class ScalabilityBivarGenerator:
    """
    Calculates the scalability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in various ways.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 perf_csv: str,
                 perf_col: str,
                 cmdopts: tp.Dict[str, tp.Any],
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        SteadyStateNormalizedEfficiencyBivar(cmdopts, perf_csv, perf_col).from_batch(criteria)

        SteadyStateParallelFractionBivar(cmdopts, perf_csv, perf_col).from_batch(criteria)


__api__ = [
    'SteadyStateNormalizedEfficiencyUnivar',
    'SteadyStateParallelFractionUnivar',
    'SteadyStateNormalizedEfficiencyBivar',
    'SteadyStateParallelFractionBivar',
    'BaseSteadyStateParallelFraction',
    'BaseSteadyStateNormalizedEfficiency'
]
