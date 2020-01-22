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

import pandas as pd

from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import common
from core.variables import batch_criteria as bc
from core.variables import population as ss


class EfficiencyBivar:
    r"""
    Calculates the per-robot efficiency in the following way for each experiment in a bivariate
    batched experiment.

    Uses the following equation:

    .. math::
        E = \frac{P(N)}{N}

    Where :math:`P(N)` is an arbitrary performance measure, evaluated on a swarm of size :math:`N`.
    """

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.BatchCriteria):
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
        if os.path.exists(stddev_ipath):
            return (self.__calculate_metric(sc_ipath, batch_criteria),
                    self.__calculate_metric(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_metric(sc_ipath, batch_criteria), None)

    def generate(self, dfs: tp.Tuple[pd.DataFrame, pd.DataFrame], batch_criteria: bc.BatchCriteria):
        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-scalability-norm")
        metric_df, stddev_df = dfs

        metric_df.to_csv(cum_stem + ".csv", sep=';', index=False)
        if stddev_df is not None:
            stddev_df.to_csv(cum_stem + ".stddev", sep=';', index=False)

        Heatmap(input_fpath=cum_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-efficiency.png"),
                title='Swarm Efficiency (Normalized)',
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calculate_metric(self,
                           ipath: str,
                           batch_criteria: bc.BatchCriteria,
                           must_exist: bool = True):
        assert(not (must_exist and not os.path.exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = pd.read_csv(ipath, sep=';')
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)
        populations = batch_criteria.populations(self.cmdopts)
        for i in range(0, len(eff_df.index)):
            for j in range(0, len(eff_df.columns)):
                eff_df.iloc[i, j] = common.csv_3D_value_iloc(raw_df,
                                                             i,
                                                             j,
                                                             slice(-1, None)) / populations[i][j]
        return eff_df


class FractionalMaintenanceBivar:
    r"""
    Calculates fractional performance losses via
    :class:`~perf_measures.common.FractionalLossesBivar`, and uses that to compute the fraction of
    performance that is maintained as swarm sizes increase.

    Uses the following equation:

    .. math::
       M(N) = 1 - \frac{1}{e^{1 - FL(N)}}

    where :math:`FL(N)` is the fractional performance losses experienced by a swarm of size
    :math:`N`.

    """

    def __init__(self, cmdopts, inter_perf_csv, ca_in_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.ca_in_csv = ca_in_csv

    def calculate(self, batch_criteria):
        df = common.FractionalLossesBivar(self.cmdopts,
                                          self.inter_perf_csv,
                                          self.ca_in_csv,
                                          batch_criteria).calculate(batch_criteria)

        for i in range(0, len(df.index)):
            for c in df.columns:
                df.loc[i, c] = 1.0 - 1.0 / math.exp(1.0 - df.loc[i, c])

        return df

    def generate(self, df: pd.DataFrame, batch_criteria: bc.BatchCriteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-fm")

        df.to_csv(stem_path + '.csv', sep=';', index=False)
        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-scalability-fm.png"),
                title="Swarm Scalability: Fractional Performance Maintenance In The Presence Of Inter-robot Interference",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()


class KarpFlattBivar:
    r"""
    Given a swarm exhibiting speedup :math:`X` with N robots (N > 1), compute the serial fraction
    :math:`Y` of the swarm's performance. The lower the value of Y, the better the
    parallelization/scalability, suggesting that the addition of more robots will bring additional
    performance improvements.

    Uses the following equation:

    .. math::
        Y = \frac{\frac{1}{X} - \frac{1}{N}}{1 - \frac{1}{N}}

    Where $X$ is is the projective performance calculated via
    :class:`~perf_measures.common.ProjectivePerformanceCalculatorBivar`.

    """

    def __init__(self, cmdopts, inter_perf_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv

    def calculate(self, batch_criteria):
        df = common.ProjectivePerformanceCalculatorBivar(self.cmdopts,
                                                         self.inter_perf_csv,
                                                         "positive")(batch_criteria)

        sizes = batch_criteria.populations(self.cmdopts)
        xfactor = 0
        yfactor = 0

        # Swarm size is along rows (X), so the first column by definition has perfect scalability
        if isinstance(batch_criteria.criteria1, ss.Population):
            df.iloc[:, 0] = 0.0
            yfactor = 1

        # Swarm size is along rows (Y), so the first row by definition has perfect scalability
        else:
            df.iloc[0, :] = 0.0
            xfactor = 1

        for i in range(0 + xfactor, len(df.index)):
            for j in range(0 + yfactor, len(df.columns)):
                x = df.iloc[i, j]

                # We need to know which of the 2 variables was swarm size, in order to determine
                # the correct dimension along which to compute the metric, which depends on
                # performance between adjacent swarm sizes.
                if isinstance(batch_criteria.criteria1, ss.Population):
                    n = sizes[i + 1][j]
                else:
                    n = sizes[i][j + 1]

                df.iloc[i, j] = (1.0 / x - 1.0 / n) / (1 - 1.0 / n)
        return df

    def generate(self, df, batch_criteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-karpflatt")
        df.to_csv(stem_path + ".csv", sep=';', index=False)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-karpflatt.png"),
                title="Swarm Serial Fraction: Karp-Flatt Metric",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)[1:]).generate()


class ScalabilityBivarGenerator:
    """
    Calculates the scalability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in various ways.
    """

    def __call__(self, inter_perf_csv, ca_in_csv, cmdopts, batch_criteria):
        logging.info("Bivariate scalability from %s", cmdopts["collate_root"])

        e = EfficiencyBivar(cmdopts, inter_perf_csv)
        e.generate(e.calculate(batch_criteria), batch_criteria)

        f = FractionalMaintenanceBivar(cmdopts, inter_perf_csv, ca_in_csv)
        f.generate(f.calculate(batch_criteria), batch_criteria)

        k = KarpFlattBivar(cmdopts, inter_perf_csv)
        k.generate(k.calculate(batch_criteria), batch_criteria)


class EfficiencyUnivar:
    r"""
    Calculates the per-robot efficiency in the following way for each experiment in a univariate
    batched experiment.

    Uses the following equation:

    .. math::
       E = \frac{P(N)}{N}

    Where :math:`P(N)` is an arbitrary performance measure, evaluated on a swarm of size :math:`N`.
    """

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.BatchCriteria):
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
        if os.path.exists(stddev_ipath):
            return (self.__calculate_metric(sc_ipath, batch_criteria),
                    self.__calculate_metric(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_metric(sc_ipath, batch_criteria), None)

    def generate(self, dfs: tp.Tuple[pd.DataFrame, pd.DataFrame], batch_criteria: bc.BatchCriteria):
        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-scalability-norm")
        metric_df = dfs[0]
        stddev_df = dfs[1]
        metric_df.to_csv(cum_stem + ".csv", sep=';', index=False)
        if stddev_df is not None:
            stddev_df.to_csv(cum_stem + ".stddev", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=cum_stem,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-efficiency.png"),
                         title="Swarm Efficiency (normalized)",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Efficiency",
                         xvals=batch_criteria.graph_xticks(self.cmdopts)).generate()

    def __calculate_metric(self,
                           ipath: str,
                           batch_criteria: bc.BatchCriteria,
                           must_exist: bool = True):
        assert(not (must_exist and not os.path.exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = pd.read_csv(ipath, sep=';')
        eff_df = pd.DataFrame(columns=raw_df.columns
                              )
        populations = batch_criteria.populations(self.cmdopts)

        for i in range(0, len(eff_df.columns)):
            n_robots = populations[i]
            col = eff_df.columns[i]
            perf_N = raw_df.tail(1)[col]
            eff_df[col] = perf_N / n_robots
        return eff_df


class ProjectivePerformanceComparisonUnivar:
    """
    Calculates projective performance for each experiment i > 0 in the batch and productes a graph.
    """

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str, projection_type: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.projection_type = projection_type

    def calculate(self, batch_criteria: bc.BatchCriteria):
        return common.ProjectivePerformanceCalculatorUnivar(self.cmdopts,
                                                            self.inter_perf_csv,
                                                            self.projection_type)(batch_criteria)

    def generate(self, df: pd.DataFrame, batch_criteria: bc.BatchCriteria):
        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-pp-comp-" + self.projection_type)
        df.to_csv(cum_stem + ".csv", sep=';', index=False)
        xvals = batch_criteria.graph_xticks(self.cmdopts)

        BatchRangedGraph(inputy_stem_fpath=cum_stem + ".csv",
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-pp-comp-" + self.projection_type + ".png"),
                         title="Swarm Projective Performance Comparison ({0})".format(
                             self.projection_type),
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Observed-Projected Ratio",
                         xvals=xvals[1:]).generate()


class ProjectivePerformanceComparisonPositiveUnivar(ProjectivePerformanceComparisonUnivar):
    def __init__(self, cmdopts, inter_perf_csv):
        super().__init__(cmdopts, inter_perf_csv, "positive")


class ProjectivePerformanceComparisonNegativeUnivar(ProjectivePerformanceComparisonUnivar):
    def __init__(self, cmdopts, inter_perf_csv):
        super().__init__(cmdopts, inter_perf_csv, "negative")


class FractionalMaintenanceUnivar:
    """
    Calculates fractional performance losses via
    :class:`~perf_measures.common.FractionalLossesUnivar`, and uses that to compute the fraction of
    performance that is maintained as swarm sizes increase.

    Uses the following equation:

    .. math::
       M(N) = 1 - \frac{1}{e^{1 - FL(N)}}

    where :math:`FL(N)` is the fractional performance losses experienced by a swarm of size
    :math:`N`.

    """

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str, ca_in_csv: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.ca_in_csv = ca_in_csv

    def calculate(self, batch_criteria: bc.BatchCriteria):
        df = common.FractionalLossesUnivar(self.cmdopts,
                                           self.inter_perf_csv,
                                           self.ca_in_csv,
                                           batch_criteria).calculate(batch_criteria)

        for c in df.columns:
            df[c] = 1.0 - 1.0 / math.exp(1.0 - df[c])
        return df

    def generate(self, df: pd.DataFrame, batch_criteria: bc.BatchCriteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-fm")

        df.to_csv(stem_path + '.csv', sep=';', index=False)
        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-scalability-fm.png"),
                         title="Swarm Scalability: Fractional Performance Maintenance In The Presence Of Inter-robot Interference",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Scalability Value",
                         xvals=batch_criteria.graph_xticks(self.cmdopts)).generate()


class KarpFlattUnivar:
    r"""
    Given a swarm exhibiting speedup :math:`X` with N robots(N > 1), compute the serial fraction
    :math:`Y` of the swarm's performance. The lower the value of Y, the better the
    parallelization/scalability, suggesting that the addition of more robots will bring additional
    performance improvements:

    .. math::
        Y = \frac{\frac{1}{X} - \frac{1}{N}}{1 - \frac{1}{N}}

    Defined for swarms with N >=1 robots. For N=1, we obtain a Karp-Flatt value of 1.0 using
    L'Hospital's rule and taking the derivative with respect to N (1 - 1/N is giving the problem
    after all).

    """

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv

    def calculate(self, batch_criteria: bc.BatchCriteria):
        # Projective performance does not cover exp0, so we have to get the right column name from
        # the performance .csv again so we can add it to the Karp-Flatt dataframe.
        path = os.path.join(self.cmdopts["collate_root"], self.inter_perf_csv)
        columns = pd.read_csv(path, sep=';').columns
        projection = common.ProjectivePerformanceCalculatorUnivar(self.cmdopts,
                                                                  self.inter_perf_csv,
                                                                  "positive")(batch_criteria)
        df = pd.DataFrame(columns=columns, index=[0])
        sizes = batch_criteria.populations(self.cmdopts)

        # Perfect scalability with only 1 robot, from L'Hospital's rule
        df[df.columns[0]] = 1.0
        df[projection.columns] = projection[projection.columns]

        for i in range(1, len(df.columns)):
            c = df.columns[i]
            s = sizes[i]
            df[c] = (1.0 / df[c] - 1.0 / s) / (1 - 1.0 / s)

        return df

    def generate(self, df: pd.DataFrame, batch_criteria: bc.BatchCriteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-karpflatt")
        df.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-karpflatt.png"),
                         title="Swarm Serial Fraction: Karp-Flatt Metric",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xvals=batch_criteria.graph_xticks(self.cmdopts)).generate()


class ScalabilityUnivarGenerator:
    """
    Calculates the scalability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def __call__(self, inter_perf_csv, ca_in_csv, cmdopts, batch_criteria):
        logging.info("Univariate scalability from %s", cmdopts["collate_root"])

        e = EfficiencyUnivar(cmdopts, inter_perf_csv)
        e.generate(e.calculate(batch_criteria), batch_criteria)

        f = FractionalMaintenanceUnivar(cmdopts, inter_perf_csv, ca_in_csv)
        f.generate(f.calculate(batch_criteria), batch_criteria)

        k = KarpFlattUnivar(cmdopts, inter_perf_csv)
        k.generate(k.calculate(batch_criteria), batch_criteria)
