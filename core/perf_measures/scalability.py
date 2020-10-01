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

import os
import copy
import logging
import math
import typing as tp

import pandas as pd  # type: ignore

from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import common
from core.variables import batch_criteria as bc
from core.variables import population_size
from core.variables import population_density
import core.utils

################################################################################
# Univariate Classes
################################################################################


class InterRobotInterferenceUnivar:
    """
    Univariate calculator for the per-robot inter-robot interference for each experiment in a batch
    (intra-experiment measure; no comparison across experiments in a batch is performed).

    """
    kCountLeaf = 'pm-interference-count'
    kDurationLeaf = 'pm-interference-duration'

    def __init__(self, cmdopts: dict,
                 interference_count_csv: str,
                 interference_duration_csv: str) -> None:
        self.cmdopts = copy.deepcopy(cmdopts)
        self.interference_count_stem = interference_count_csv.split('.')[0]
        self.interference_duration_stem = interference_duration_csv.split('.')[0]

    def generate(self, batch_criteria: bc.IConcreteBatchCriteria):
        count_csv_istem = os.path.join(self.cmdopts["collate_root"],
                                       self.interference_count_stem)
        duration_csv_istem = os.path.join(self.cmdopts["collate_root"],
                                          self.interference_duration_stem)
        count_csv_ostem = os.path.join(self.cmdopts["collate_root"], self.kCountLeaf)
        duration_csv_ostem = os.path.join(self.cmdopts["collate_root"], self.kDurationLeaf)
        count_png_ostem = os.path.join(self.cmdopts["graph_root"], self.kCountLeaf)
        duration_png_ostem = os.path.join(self.cmdopts["graph_root"], self.kDurationLeaf)

        count_df = self.__calculate_measure(count_csv_istem + ".csv", batch_criteria)
        core.utils.pd_csv_write(count_df, count_csv_ostem + '.csv', index=False)

        duration_df = self.__calculate_measure(duration_csv_istem + ".csv", batch_criteria)
        core.utils.pd_csv_write(duration_df, duration_csv_ostem + '.csv', index=False)

        BatchRangedGraph(inputy_stem_fpath=count_csv_ostem,
                         output_fpath=count_png_ostem + '.png',
                         title="Swarm Inter-Robot Interference Counts",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Average # Robots",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()

        BatchRangedGraph(inputy_stem_fpath=duration_csv_ostem,
                         output_fpath=duration_png_ostem + '.png',
                         title="Swarm Average Inter-Robot Interference Duration",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="# Timesteps",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()

    def __calculate_measure(self, ipath: str, batch_criteria: bc.IConcreteBatchCriteria):
        assert(core.utils.path_exists(ipath)), "FATAL: {0} does not exist".format(ipath)
        raw_df = core.utils.pd_csv_read(ipath)
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=[0])

        populations = batch_criteria.populations(self.cmdopts)
        for i in range(0, len(raw_df.columns)):
            eff_df[raw_df.columns[i]] = efficiency_calculate(
                raw_df[raw_df.columns[i]], populations[i])

        return eff_df


class NormalizedEfficiencyUnivar:
    r"""
    Univariate calculator for per-robot efficiency for each experiment in a batch
    (intra-experiment measure; no comparison across experiments in a batch is performed). See
    :func:`efficiency_calculate()` for calculations.
    """

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.IConcreteBatchCriteria):
        """
        Calculate efficiency metric for the givenn controller for each experiment in a
        batch.

        Return:
          (Calculated metric dataframe, stddev dataframe) if stddev was collected.
          (Calculated metric datafram, None) otherwise.
        """
        sc_ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.inter_perf_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation,
        if core.utils.path_exists(stddev_ipath):
            return (self.__calculate_measure(sc_ipath, batch_criteria),
                    self.__calculate_measure(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_measure(sc_ipath, batch_criteria), None)

    def generate(self,
                 dfs: tp.Tuple[pd.DataFrame, pd.DataFrame],
                 batch_criteria: bc.IConcreteBatchCriteria):
        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-scalability-norm")
        metric_df = dfs[0]
        stddev_df = dfs[1]
        core.utils.pd_csv_write(metric_df, cum_stem + ".csv", index=False)
        if stddev_df is not None:
            core.utils.pd_csv_write(stddev_df, cum_stem + ".stddev", index=False)

        BatchRangedGraph(inputy_stem_fpath=cum_stem,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-efficiency.png"),
                         title="Swarm Efficiency (normalized)",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Efficiency",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()

    def __calculate_measure(self,
                            ipath: str,
                            batch_criteria: bc.IConcreteBatchCriteria,
                            must_exist: bool = True):
        assert(not (must_exist and not core.utils.path_exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = core.utils.pd_csv_read(ipath)
        eff_df = pd.DataFrame(columns=raw_df.columns
                              )
        populations = batch_criteria.populations(self.cmdopts)

        for i in range(0, len(eff_df.columns)):
            n_robots = populations[i]
            col = eff_df.columns[i]
            perf_N = raw_df.tail(1)[col]
            eff_df[col] = perf_N / n_robots
        return eff_df


class FractionalMaintenanceUnivar:
    r"""
    Univariate calculator for fractional performance maintenance via
    :class:`~core.perf_measures.common.FractionalLossesUnivar` (basically the inverse of the
    losses).

    Uses the following equation:

    .. math::
       M(N) = 1 - \frac{1}{e^{1 - FL(N)}}

    where :math:`FL(N)` is the fractional performance losses experienced by a swarm of size
    :math:`N` (see :eq:`pm-fractional-losses`).

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.
    """

    def __init__(self, cmdopts: dict, inter_perf_csv: str, interference_count_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.interference_count_csv = interference_count_csv

    def calculate(self, batch_criteria: bc.IConcreteBatchCriteria):
        df = common.FractionalLossesUnivar(self.cmdopts,
                                           self.inter_perf_csv,
                                           self.interference_count_csv,
                                           batch_criteria).calculate(batch_criteria)

        for c in df.columns:
            df[c] = 1.0 - 1.0 / math.exp(1.0 - df[c])
        return df

    def generate(self, df: pd.DataFrame, batch_criteria: bc.IConcreteBatchCriteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-fm")

        core.utils.pd_csv_write(df, stem_path + '.csv', index=False)
        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-scalability-fm.png"),
                         title="Swarm Scalability: Fractional Performance Maintenance In The Presence Of Inter-robot Interference",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Scalability Value",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()


class ParallelFractionUnivar:
    r"""
    Calculates the scalability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using the Karp-Flatt metric
    (See :func:`parallel_fraction_calculate()`).

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    """

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv

    def calculate(self, batch_criteria: bc.IConcreteBatchCriteria):
        perf_df = core.utils.pd_csv_read(os.path.join(self.cmdopts["collate_root"],
                                                      self.inter_perf_csv))
        sc_df = pd.DataFrame(columns=perf_df.columns, index=[0])
        sizes = batch_criteria.populations(self.cmdopts)

        idx = perf_df.index[-1]

        for i in range(0, len(perf_df.columns)):
            perf_i = perf_df.loc[idx, perf_df.columns[i]]
            n_robots_i = sizes[i]

            if self.cmdopts['pm_scalability_from_exp0']:
                n_robots_iminus1 = sizes[0]
                perf_iminus1 = perf_df.loc[idx, perf_df.columns[0]]
            else:
                n_robots_iminus1 = sizes[i - 1]
                perf_iminus1 = perf_df.loc[idx, perf_df.columns[i - 1]]

            speedup_i = perf_i / perf_iminus1

            sc_df[sc_df.columns[i]] = parallel_fraction_calculate(speedup_i=speedup_i,
                                                                  n_robots_i=n_robots_i,
                                                                  n_robots_iminus1=n_robots_iminus1,
                                                                  normalize=self.cmdopts['pm_scalability_normalize'],
                                                                  normalize_method=self.cmdopts['pm_normalize_method'])

        return sc_df

    def generate(self, df: pd.DataFrame, batch_criteria: bc.IConcreteBatchCriteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-parallel-frac")
        core.utils.pd_csv_write(df, stem_path + ".csv", index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-scalability-parallel-frac.png"),
                         title="Swarm Parallel Performance Fraction",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                         ylabel="",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()


class ScalabilityUnivarGenerator:
    """
    Calculates the scalability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def __call__(self,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 interference_duration_csv: str,
                 cmdopts: dict,
                 batch_criteria: bc.IConcreteBatchCriteria):
        logging.info("Univariate scalability from %s", cmdopts["collate_root"])

        e = NormalizedEfficiencyUnivar(cmdopts, inter_perf_csv)
        e.generate(e.calculate(batch_criteria), batch_criteria)

        i = InterRobotInterferenceUnivar(cmdopts,
                                         interference_count_csv,
                                         interference_duration_csv)
        i.generate(batch_criteria)

        f = FractionalMaintenanceUnivar(cmdopts, inter_perf_csv, interference_count_csv)
        f.generate(f.calculate(batch_criteria), batch_criteria)

        k = ParallelFractionUnivar(cmdopts, inter_perf_csv)
        k.generate(k.calculate(batch_criteria), batch_criteria)

################################################################################
# Bivariate Classes
################################################################################


class InterRobotInterferenceBivar:
    """
    Bivariate calculator for the per-robot inter-robot interference for each experiment in a batch
    (intra-experiment measure; no comparison across experiments in a batch is performed).

    """
    kCountLeaf = 'pm-interference-count'
    kDurationLeaf = 'pm-interference-duration'

    def __init__(self, cmdopts: dict,
                 interference_count_csv: str,
                 interference_duration_csv: str) -> None:
        self.cmdopts = copy.deepcopy(cmdopts)
        self.interference_count_stem = interference_count_csv.split('.')[0]
        self.interference_duration_stem = interference_duration_csv.split('.')[0]

    def generate(self, batch_criteria: bc.IConcreteBatchCriteria):
        count_csv_istem = os.path.join(self.cmdopts["collate_root"],
                                       self.interference_count_stem)
        duration_csv_istem = os.path.join(self.cmdopts["collate_root"],
                                          self.interference_duration_stem)
        count_csv_ostem = os.path.join(self.cmdopts["collate_root"], self.kCountLeaf)
        duration_csv_ostem = os.path.join(self.cmdopts["collate_root"], self.kDurationLeaf)
        count_png_ostem = os.path.join(self.cmdopts["graph_root"], self.kCountLeaf)
        duration_png_ostem = os.path.join(self.cmdopts["graph_root"], self.kDurationLeaf)

        count_df = self.__calculate_measure(count_csv_istem + ".csv")
        core.utils.pd_csv_write(count_df, count_csv_ostem + '.csv', index=False)

        duration_df = self.__calculate_measure(duration_csv_istem + ".csv")
        core.utils.pd_csv_write(duration_df, duration_csv_ostem + '.csv', index=False)

        Heatmap(input_fpath=count_csv_ostem + ".csv",
                output_fpath=count_png_ostem + ".png",
                title='Swarm Inter-Robot Interference Counts',
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

        Heatmap(input_fpath=duration_csv_ostem + ".csv",
                output_fpath=duration_png_ostem + ".png",
                title='Swarm Average Inter-Robot Interference Duration',
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    @staticmethod
    def __calculate_measure(ipath: str):
        assert(core.utils.path_exists(ipath)), "FATAL: {0} does not exist".format(ipath)
        raw_df = core.utils.pd_csv_read(ipath)
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)
        for i in range(0, len(eff_df.index)):
            for j in range(0, len(eff_df.columns)):
                eff_df.iloc[i, j] = common.csv_3D_value_iloc(raw_df,
                                                             i,
                                                             j,
                                                             slice(-1, None))
        return eff_df


class NormalizedEfficiencyBivar:
    """
    Bivariate calculator for per-robot efficiency for each experiment in a batch
    (intra-experiment measure; no comparison across experiments in a batch is performed). See
    :func:`efficiency_calculate()` for calculations.
    """

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.IConcreteBatchCriteria):
        """
        Calculate efficiency metric for the given controller for each experiment in a
        batch.

        Return:
          (Calculated metric dataframe, stddev dataframe) if stddev was collected
          (Calculated metric datafram, None) otherwise.
        """
        sc_ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.inter_perf_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation,
        if core.utils.path_exists(stddev_ipath):
            return (self.__calculate_measure(sc_ipath, batch_criteria),
                    self.__calculate_measure(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_measure(sc_ipath, batch_criteria), None)

    def generate(self,
                 dfs: tp.Tuple[pd.DataFrame, pd.DataFrame],
                 batch_criteria: bc.IConcreteBatchCriteria):
        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-scalability-norm")
        metric_df, stddev_df = dfs

        core.utils.pd_csv_write(metric_df, cum_stem + ".csv", index=False)
        if stddev_df is not None:
            core.utils.pd_csv_write(stddev_df, cum_stem + ".stddev", index=False)

        Heatmap(input_fpath=cum_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-efficiency.png"),
                title='Swarm Efficiency (Normalized)',
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calculate_measure(self,
                            ipath: str,
                            batch_criteria: bc.IConcreteBatchCriteria,
                            must_exist: bool = True):
        assert(not (must_exist and not core.utils.path_exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = core.utils.pd_csv_read(ipath)
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)
        populations = batch_criteria.populations(self.cmdopts)
        for i in range(0, len(eff_df.index)):
            for j in range(0, len(eff_df.columns)):
                perf_i = common.csv_3D_value_iloc(raw_df,
                                                  i,
                                                  j,
                                                  slice(-1, None))
                eff_df.iloc[i, j] = efficiency_calculate(perf_i, populations[i][j])
        return eff_df


class FractionalMaintenanceBivar:
    r"""
    Bivariate calculator for fractional performance maintenance via
    :class:`~core.perf_measures.common.FractionalLossesBivar` (basically the inverse of the losses).
    See :class:`~core.perf_measures.scalability.FractionalMaintenanceUnivar` for a description of
    the mathematical calculations performed by this class.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.
    """

    def __init__(self, cmdopts, inter_perf_csv, interference_count_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.interference_count_csv = interference_count_csv

    def calculate(self, batch_criteria):
        df = common.FractionalLossesBivar(self.cmdopts,
                                          self.inter_perf_csv,
                                          self.interference_count_csv,
                                          batch_criteria).calculate(batch_criteria)

        for i in range(0, len(df.index)):
            for c in df.columns:
                df.loc[i, c] = 1.0 - 1.0 / math.exp(1.0 - df.loc[i, c])

        return df

    def generate(self, df: pd.DataFrame, batch_criteria: bc.IConcreteBatchCriteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-fm")

        core.utils.pd_csv_write(df, stem_path + '.csv', index=False)
        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-scalability-fm.png"),
                title="Swarm Scalability: Fractional Performance Maintenance In The Presence Of Inter-robot Interference",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()


class ParallelFractionBivar:
    """
    Calculates the scalability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using the Karp-Flatt metric
    (See :func:`parallel_fraction_calculate()`).

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    """

    def __init__(self, cmdopts, inter_perf_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv

    def calculate(self, batch_criteria):
        perf_df = core.utils.pd_csv_read(os.path.join(self.cmdopts["collate_root"],
                                                      self.inter_perf_csv))
        sc_df = pd.DataFrame(columns=perf_df.columns, index=perf_df.index)

        sizes = batch_criteria.populations(self.cmdopts)

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
                                                   self.cmdopts)
                if axis == 0:
                    perf_xminus1 = common.csv_3D_value_iloc(perf_df,
                                                            i - 1,
                                                            j,
                                                            slice(-1, None))

                    if self.cmdopts['pm_scalability_from_exp0']:
                        n_robots_xminus1 = sizes[0][j]
                    else:
                        n_robots_xminus1 = sizes[i - 1][j]
                else:
                    perf_xminus1 = common.csv_3D_value_iloc(perf_df,
                                                            i,
                                                            j - 1,
                                                            slice(-1, None))
                    if self.cmdopts['pm_scalability_from_exp0']:
                        n_robots_xminus1 = sizes[0][j]
                    else:
                        n_robots_xminus1 = sizes[i][j - 1]

                speedup_i = perf_x / perf_xminus1
                sc_df.iloc[i, j] = parallel_fraction_calculate(speedup_i=speedup_i,
                                                               n_robots_i=n_robots_x,
                                                               n_robots_iminus1=n_robots_xminus1,
                                                               normalize=self.cmdopts['pm_scalability_normalize'],
                                                               normalize_method=self.cmdopts['pm_normalize_method'])

        return sc_df

    def generate(self, df, batch_criteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-parallel-fraction")
        core.utils.pd_csv_write(df, stem_path + ".csv", index=False)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-parallel-fraction.png"),
                title="Swarm Parallel Performance Fraction",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()


class ScalabilityBivarGenerator:
    """
    Calculates the scalability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in various ways.
    """

    def __call__(self,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 interference_duration_csv: str,
                 cmdopts: dict,
                 batch_criteria: bc.IConcreteBatchCriteria):
        logging.info("Bivariate scalability from %s", cmdopts["collate_root"])

        e = NormalizedEfficiencyBivar(cmdopts, inter_perf_csv)
        e.generate(e.calculate(batch_criteria), batch_criteria)

        i = InterRobotInterferenceBivar(cmdopts,
                                        interference_count_csv,
                                        interference_duration_csv)
        i.generate(batch_criteria)

        f = FractionalMaintenanceBivar(cmdopts, inter_perf_csv, interference_count_csv)
        f.generate(f.calculate(batch_criteria), batch_criteria)

        k = ParallelFractionBivar(cmdopts, inter_perf_csv)
        k.generate(k.calculate(batch_criteria), batch_criteria)


################################################################################
# Calculation Functions
################################################################################

def parallel_fraction_calculate(speedup_i: float,
                                n_robots_i: int,
                                n_robots_iminus1: int,
                                normalize: bool,
                                normalize_method: str):
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


def efficiency_calculate(perf_i: float, n_robots_i: int):
    r"""
    Calculate for per-robot efficiency.

    .. math::
       E = \frac{P(N)}{N}

    Where :math:`P(N)` is an arbitrary performance measure, evaluated on a swarm of size :math:`N`.

    From :xref:`Hecker2015`.
    """
    return perf_i / float(n_robots_i)


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
