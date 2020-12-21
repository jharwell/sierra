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
Measures for swarm scalability in univariate and bivariate batched experiments.
"""

# Core packages
import os
import copy
import logging
import math
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import common
from core.variables import batch_criteria as bc
from core.variables import population_size
from core.variables import population_density
import core.utils
import core.config

################################################################################
# Base Classes
################################################################################


class BaseParallelFraction():
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
    @staticmethod
    def kernel(speedup_i: float,
               n_robots_i: int,
               n_robots_iminus1: int,
               normalize: bool,
               normalize_method: str):
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


class BaseNormalizedEfficiency():
    r"""
    Calculate for per-robot efficiency.

    .. math::
       E = \frac{P(N)}{N}

    Where :math:`P(N)` is an arbitrary performance measure, evaluated on a swarm of size
    :math:`N`.

    From :xref:`Hecker2015`.
    """
    @staticmethod
    def kernel(perf_i: float, n_robots_i: int):
        return perf_i / float(n_robots_i)

################################################################################
# Univariate Classes
################################################################################


class InterRobotInterferenceUnivar:
    """
    Univariate calculator for the per-robot inter-robot interference for each experiment in a batch.

    """
    kCountLeaf = 'PM-scalability-interference-count'
    kDurationLeaf = 'PM-scalability-interference-duration'

    @staticmethod
    def df_kernel(df_t: pd.DataFrame) -> pd.DataFrame:
        df = pd.DataFrame(columns=df_t.columns, index=[0])

        for col in df_t:
            df[col] = df_t.loc[df_t.index[-1], col]

        return df

    def __init__(self, cmdopts: dict,
                 interference_count_csv: str,
                 interference_duration_csv: str) -> None:
        self.cmdopts = copy.deepcopy(cmdopts)
        self.interference_count_stem = interference_count_csv.split('.')[0]
        self.interference_duration_stem = interference_duration_csv.split('.')[0]

    def from_batch(self, batch_criteria: bc.IConcreteBatchCriteria):
        count_csv_istem = os.path.join(self.cmdopts["batch_collate_root"],
                                       self.interference_count_stem)
        duration_csv_istem = os.path.join(self.cmdopts["batch_collate_root"],
                                          self.interference_duration_stem)
        count_csv_ostem = os.path.join(self.cmdopts["batch_collate_root"], self.kCountLeaf)
        duration_csv_ostem = os.path.join(self.cmdopts["batch_collate_root"], self.kDurationLeaf)
        count_img_ostem = os.path.join(self.cmdopts["batch_collate_graph_root"], self.kCountLeaf)
        duration_img_ostem = os.path.join(
            self.cmdopts["batch_collate_graph_root"], self.kDurationLeaf)

        count_df = self.df_kernel(core.utils.pd_csv_read(count_csv_istem + '.csv'))
        core.utils.pd_csv_write(count_df, count_csv_ostem + '.csv', index=False)
        core.utils.pd_csv_write(count_df, count_csv_ostem + '.csv', index=False)

        duration_df = self.df_kernel(core.utils.pd_csv_read(duration_csv_istem + '.csv'))
        core.utils.pd_csv_write(duration_df, duration_csv_ostem + '.csv', index=False)
        core.utils.pd_csv_write(duration_df, duration_csv_ostem + '.csv', index=False)

        BatchRangedGraph(input_fpath=count_csv_ostem + '.csv',
                         output_fpath=count_img_ostem + core.config.kImageExt,
                         title="Swarm Inter-Robot Interference Counts",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Average # Robots",
                         xticks=batch_criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale']).generate()

        BatchRangedGraph(input_fpath=duration_csv_ostem + '.csv',
                         output_fpath=duration_img_ostem + core.config.kImageExt,
                         title="Swarm Average Inter-Robot Interference Duration",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="# Timesteps",
                         xticks=batch_criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale']).generate()


class NormalizedEfficiencyUnivar(BaseNormalizedEfficiency):
    r"""
    Univariate calculator for per-robot efficiency for each experiment in a batch
    (intra-experiment measure; no comparison across experiments in a batch is performed). See
    :func:`efficiency_calculate()` for calculations.
    """
    kLeaf = 'PM-scalability-efficiency'

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  perf_df: pd.DataFrame) -> pd.DataFrame:
        eff_df = pd.DataFrame(columns=perf_df.columns
                              )
        populations = criteria.populations(cmdopts)

        for i in range(0, len(eff_df.columns)):
            n_robots = populations[i]
            col = eff_df.columns[i]
            perf_N = perf_df.tail(1)[col]
            eff_df[col] = BaseNormalizedEfficiency.kernel(perf_N, n_robots)
        return eff_df

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        """
        Calculate efficiency metric for the given controller for each experiment in a
        batch. If stddev or a model of the metric exists, they are plotted along with the calculated
        metric.
        """
        # We always calculate the actual metric
        perf_idf = core.utils.pd_csv_read(os.path.join(self.cmdopts["batch_collate_root"],
                                                       self.inter_perf_stem + '.csv'))
        metric_odf = self.df_kernel(criteria, self.cmdopts, perf_idf)
        ostem = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        core.utils.pd_csv_write(metric_odf, ostem + ".csv", index=False)

        # Stddev might not have been calculated in stage 3
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')
        if core.utils.path_exists(stddev_ipath):
            stddev_idf = core.utils.pd_csv_read(stddev_ipath)
            stddev_odf = self.df_kernel(criteria, self.cmdopts, stddev_idf)
            core.utils.pd_csv_write(stddev_odf, ostem + ".stddev", index=False)

        BatchRangedGraph(input_fpath=ostem + '.csv',
                         stddev_fpath=ostem + '.stddev',
                         model_fpath=os.path.join(self.cmdopts['batch_model_root'],
                                                  self.kLeaf + '.model'),
                         model_legend_fpath=os.path.join(self.cmdopts['batch_model_root'],
                                                         self.kLeaf + '.legend'),
                         output_fpath=os.path.join(self.cmdopts["batch_collate_graph_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         title="Swarm Efficiency (normalized)",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="Efficiency",
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale']).generate()


class ParallelFractionUnivar(BaseParallelFraction):
    r"""
    Calculates the scalability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using the Karp-Flatt metric
    (See :func:`parallel_fraction_calculate()`).

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    """
    kLeaf = 'PM-scalability-parallel-frac'

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  perf_df: pd.DataFrame) -> pd.DataFrame:
        res_df = pd.DataFrame(columns=perf_df.columns, index=[0])
        sizes = criteria.populations(cmdopts)

        idx = perf_df.index[-1]

        for i in range(0, len(perf_df.columns)):
            perf_i = perf_df.loc[idx, perf_df.columns[i]]
            n_robots_i = sizes[i]

            if cmdopts['pm_scalability_from_exp0']:
                n_robots_iminus1 = sizes[0]
                perf_iminus1 = perf_df.loc[idx, perf_df.columns[0]]
            else:
                n_robots_iminus1 = sizes[i - 1]
                perf_iminus1 = perf_df.loc[idx, perf_df.columns[i - 1]]

            speedup_i = perf_i / perf_iminus1
            res_df[res_df.columns[i]] = BaseParallelFraction.kernel(speedup_i=speedup_i,
                                                                    n_robots_i=n_robots_i,
                                                                    n_robots_iminus1=n_robots_iminus1,
                                                                    normalize=cmdopts['pm_scalability_normalize'],
                                                                    normalize_method=cmdopts['pm_normalize_method'])
        return res_df

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        # We always calculate the metric
        perf_idf = core.utils.pd_csv_read(os.path.join(self.cmdopts["batch_collate_root"],
                                                       self.inter_perf_stem + '.csv'))
        perf_odf = self.df_kernel(criteria, self.cmdopts, perf_idf)
        ostem = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)

        core.utils.pd_csv_write(perf_odf, ostem + ".csv", index=False)

        # Stddev might not have been calculated in stage 3
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')
        if core.utils.path_exists(stddev_ipath):
            stddev_idf = core.utils.pd_csv_read(stddev_ipath)
            stddev_odf = self.df_kernel(criteria, self.cmdopts, stddev_idf)
            core.utils.pd_csv_write(stddev_odf, ostem + ".stddev", index=False)

        BatchRangedGraph(input_fpath=ostem + '.csv',
                         stddev_fpath=ostem + '.stddev',
                         model_fpath=os.path.join(self.cmdopts['batch_model_root'],
                                                  self.kLeaf + '.model'),
                         model_legend_fpath=os.path.join(self.cmdopts['batch_model_root'],
                                                         self.kLeaf + '.legend'),
                         output_fpath=os.path.join(self.cmdopts["batch_collate_graph_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         title="Swarm Parallel Performance Fraction",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                         ylabel="",
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale']).generate()


class ScalabilityUnivarGenerator:
    """
    Calculates the scalability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 interference_duration_csv: str,
                 cmdopts: dict,
                 criteria: bc.IConcreteBatchCriteria):
        self.logger.info("Univariate scalability from %s", cmdopts["batch_collate_root"])

        InterRobotInterferenceUnivar(cmdopts, interference_count_csv,
                                     interference_duration_csv).from_batch(criteria)
        NormalizedEfficiencyUnivar(cmdopts, inter_perf_csv).from_batch(criteria)
        ParallelFractionUnivar(cmdopts, inter_perf_csv).from_batch(criteria)

################################################################################
# Bivariate Classes
################################################################################


class InterRobotInterferenceBivar:
    """
    Bivariate calculator for the per-robot inter-robot interference for each experiment in a batch.

    """
    kCountLeaf = 'PM-scalability-interference-count'
    kDurationLeaf = 'PM-scalability-interference-duration'

    @staticmethod
    def df_kernel(raw_df: pd.DataFrame) -> pd.DataFrame:
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)
        for i in range(0, len(eff_df.index)):
            for j in range(0, len(eff_df.columns)):
                eff_df.iloc[i, j] = common.csv_3D_value_iloc(raw_df,
                                                             i,
                                                             j,
                                                             slice(-1, None))
        return eff_df

    def __init__(self, cmdopts: dict,
                 interference_count_csv: str,
                 interference_duration_csv: str) -> None:
        self.cmdopts = copy.deepcopy(cmdopts)
        self.interference_count_stem = interference_count_csv.split('.')[0]
        self.interference_duration_stem = interference_duration_csv.split('.')[0]

    def from_batch(self, batch_criteria: bc.IConcreteBatchCriteria):
        count_csv_istem = os.path.join(self.cmdopts["batch_collate_root"],
                                       self.interference_count_stem)
        duration_csv_istem = os.path.join(self.cmdopts["batch_collate_root"],
                                          self.interference_duration_stem)
        count_csv_ostem = os.path.join(self.cmdopts["batch_collate_root"], self.kCountLeaf)
        duration_csv_ostem = os.path.join(self.cmdopts["batch_collate_root"], self.kDurationLeaf)
        count_img_ostem = os.path.join(self.cmdopts["batch_collate_graph_root"], self.kCountLeaf)
        duration_img_ostem = os.path.join(self.cmdopts["batch_collate_graph_root"],
                                          self.kDurationLeaf)

        count_idf = core.utils.pd_csv_read(count_csv_istem + '.csv')
        count_odf = self.df_kernel(count_idf)
        core.utils.pd_csv_write(count_odf, count_csv_ostem + '.csv', index=False)

        duration_idf = core.utils.pd_csv_read(duration_csv_istem + '.csv')
        duration_odf = self.df_kernel(duration_idf)
        core.utils.pd_csv_write(duration_odf, duration_csv_ostem + '.csv', index=False)

        Heatmap(input_fpath=count_csv_ostem + ".csv",
                output_fpath=count_img_ostem + core.config.kImageExt,
                title='Swarm Inter-Robot Interference Counts',
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

        Heatmap(input_fpath=duration_csv_ostem + ".csv",
                output_fpath=duration_img_ostem + core.config.kImageExt,
                title='Swarm Average Inter-Robot Interference Duration',
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()


class NormalizedEfficiencyBivar(BaseNormalizedEfficiency):
    """
    Bivariate calculator for per-robot efficiency for each experiment in a batch
    (intra-experiment measure; no comparison across experiments in a batch is performed). See
    :func:`efficiency_calculate()` for calculations.
    """
    kLeaf = 'PM-scalability-efficiency'

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  raw_df: pd.DataFrame) -> pd.DataFrame:
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)
        populations = criteria.populations(cmdopts)
        for i in range(0, len(eff_df.index)):
            for j in range(0, len(eff_df.columns)):
                perf_i = common.csv_3D_value_iloc(raw_df,
                                                  i,
                                                  j,
                                                  slice(-1, None))
                eff_df.iloc[i, j] = BaseNormalizedEfficiency.kernel(perf_i, populations[i][j])
        return eff_df

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        """
        Calculate efficiency metric for the given controller for each experiment in a
        batch.
        """
        # We always calculate the metric
        perf_idf = core.utils.pd_csv_read(os.path.join(self.cmdopts["batch_collate_root"],
                                                       self.inter_perf_stem + '.csv'))
        perf_odf = self.df_kernel(criteria, self.cmdopts, perf_idf)
        ostem = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)

        core.utils.pd_csv_write(perf_odf, ostem + ".csv", index=False)

        # Stddev might not have been calculated in stage 3
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')
        if core.utils.path_exists(stddev_ipath):
            stddev_idf = core.utils.pd_csv_read(stddev_ipath)
            stddev_odf = self.df_kernel(criteria, self.cmdopts, stddev_idf)
            core.utils.pd_csv_write(stddev_odf, ostem + ".stddev", index=False)

        Heatmap(input_fpath=ostem + '.csv',
                output_fpath=os.path.join(
                    self.cmdopts["batch_collate_graph_root"], self.kLeaf + core.config.kImageExt),
                title='Swarm Efficiency (Normalized)',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


class ParallelFractionBivar(BaseParallelFraction):
    """
    Calculates the scalability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using the Karp-Flatt metric
    (See :func:`parallel_fraction_calculate()`).

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    """
    kLeaf = 'PM-scalability-parallel-frac'

    @staticmethod
    def df_kernel(batch_criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  perf_df: pd.DataFrame) -> pd.DataFrame:
        sc_df = pd.DataFrame(columns=perf_df.columns, index=perf_df.index)

        sizes = batch_criteria.populations(cmdopts)

        for i in range(0, len(sc_df.index)):
            for j in range(0, len(sc_df.columns)):
                perf_x = common.csv_3D_value_iloc(perf_df,
                                                  i,
                                                  j,
                                                  slice(-1, None))
                n_robots_x = sizes[i][j]
                # We need to know which of the 2 variables was swarm size, in order to determine the
                # correct dimension along which to compute the metric, which depends on performance
                # between adjacent swarm sizes.
                axis = core.utils.get_primary_axis(batch_criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   cmdopts)
                if axis == 0:
                    perf_xminus1 = common.csv_3D_value_iloc(perf_df,
                                                            i - 1,
                                                            j,
                                                            slice(-1, None))

                    if cmdopts['pm_scalability_from_exp0']:
                        n_robots_xminus1 = sizes[0][j]
                    else:
                        n_robots_xminus1 = sizes[i - 1][j]
                else:
                    perf_xminus1 = common.csv_3D_value_iloc(perf_df,
                                                            i,
                                                            j - 1,
                                                            slice(-1, None))
                    if cmdopts['pm_scalability_from_exp0']:
                        n_robots_xminus1 = sizes[0][j]
                    else:
                        n_robots_xminus1 = sizes[i][j - 1]

                speedup_i = perf_x / perf_xminus1
                sc_df.iloc[i, j] = BaseParallelFraction.kernel(speedup_i=speedup_i,
                                                               n_robots_i=n_robots_x,
                                                               n_robots_iminus1=n_robots_xminus1,
                                                               normalize=cmdopts['pm_scalability_normalize'],
                                                               normalize_method=cmdopts['pm_normalize_method'])

        return sc_df

    def __init__(self, cmdopts, inter_perf_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        """
        Calculate efficiency metric for the given controller for each experiment in a
        batch. If stddev or a model of the metric exists, they are plotted along with the calculated
        metric.
        """
        # We always calculate the actual metric
        perf_idf = core.utils.pd_csv_read(os.path.join(self.cmdopts["batch_collate_root"],
                                                       self.inter_perf_stem + '.csv'))
        metric_odf = self.df_kernel(criteria, self.cmdopts, perf_idf)
        ostem = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        core.utils.pd_csv_write(metric_odf, ostem + ".csv", index=False)

        # Stddev might not have been calculated in stage 3
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')
        if core.utils.path_exists(stddev_ipath):
            stddev_idf = core.utils.pd_csv_read(stddev_ipath)
            stddev_odf = self.df_kernel(criteria, self.cmdopts, stddev_idf)
            core.utils.pd_csv_write(stddev_odf, ostem + ".stddev", index=False)

        Heatmap(input_fpath=ostem + '.csv',
                output_fpath=os.path.join(self.cmdopts["batch_collate_graph_root"],
                                          self.kLeaf + core.config.kImageExt),
                title="Swarm Parallel Performance Fraction",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


class ScalabilityBivarGenerator:
    """
    Calculates the scalability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in various ways.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 interference_duration_csv: str,
                 cmdopts: dict,
                 criteria: bc.IConcreteBatchCriteria):
        self.logger.info("Bivariate scalability from %s", cmdopts["batch_collate_root"])

        NormalizedEfficiencyBivar(cmdopts, inter_perf_csv).from_batch(criteria)

        InterRobotInterferenceBivar(cmdopts,
                                    interference_count_csv,
                                    interference_duration_csv).from_batch(criteria)

        ParallelFractionBivar(cmdopts, inter_perf_csv).from_batch(criteria)


__api__ = [
    'InterRobotInterferenceUnivar',
    'NormalizedEfficiencyUnivar',
    'FractionalMaintenanceUnivar',
    'ParallelFractionUnivar',
    'InterRobotInterferenceBivar',
    'NormalizedEfficiencyBivar',
    'FractionalMaintenanceBivar',
    'ParallelFractionBivar',
    'efficiency_calculate',
    'parallel_fraction_calculate'
]
