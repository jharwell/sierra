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


import os
import copy
import yaml
import pandas as pd
from graphs.batch_ranged_graph import BatchRangedGraph
import perf_measures.common as common
import math


class EfficiencyUnivar:
    """
    Calculates the per-robot efficiency in the following way for each experiment in a univariate
    batched experiment:

    Performance N robots / N

    Contains separate functions for returning the calculated measure and generating a graph of the
    calculated measure.
    """

    def __init__(self, cmdopts, inter_perf_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria):
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

    def generate(self, dfs, batch_criteria):
        """
        Generate an efficiency graph after calculating the metric.
        """

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
                         xvals=batch_criteria.graph_xticks(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()

    # Private functions
    def __calculate_metric(self, ipath, batch_criteria, must_exist=True):
        assert(not (must_exist and not os.path.exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = pd.read_csv(ipath, sep=';')
        eff_df = pd.DataFrame(columns=raw_df.columns
                              )
        swarm_sizes = batch_criteria.swarm_sizes(self.cmdopts)

        for i in range(0, len(eff_df.columns)):
            n_robots = swarm_sizes[i]
            col = eff_df.columns[i]
            perf_N = raw_df.tail(1)[col]
            eff_df[col] = perf_N / n_robots
        return eff_df


class ProjectivePerformanceComparisonUnivar:
    """
    Calculates projective performance for each experiment i > 0 in the batch and productes a graph.
    """

    def __init__(self, cmdopts, inter_perf_csv, projection_type):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.projection_type = projection_type

    def calculate(self, batch_criteria):
        return common.ProjectivePerformanceCalculatorUnivar(self.cmdopts,
                                                            self.inter_perf_csv,
                                                            self.projection_type)(batch_criteria)

    def generate(self, df, batch_criteria):
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
                         xvals=xvals[1:],
                         legend=None,
                         polynomial_fit=-1).generate()


class ProjectivePerformanceComparisonPositiveUnivar(ProjectivePerformanceComparisonUnivar):
    def __init__(self, cmdopts, inter_perf_csv):
        super().__init__(cmdopts, inter_perf_csv, "positive")


class ProjectivePerformanceComparisonNegativeUnivar(ProjectivePerformanceComparisonUnivar):
    def __init__(self, cmdopts, inter_perf_csv):
        super().__init__(cmdopts, inter_perf_csv, "negative")


class FractionalPerformanceLossUnivar:
    """
    Calculates the scalability of across an experiment batch using fractions of performance lost due
    to inter-robot interference as swarm size increases. Swarm sizes do not have to be a power of 2.
    """

    def __init__(self, cmdopts, inter_perf_csv, ca_in_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.ca_in_csv = ca_in_csv

    def calculate(self, batch_criteria):
        df = common.FractionalLossesUnivar(self.cmdopts,
                                           self.inter_perf_csv,
                                           self.ca_in_csv,
                                           batch_criteria).calculate(batch_criteria)

        for c in df.columns:
            df[c] = 1.0 - 1.0 / math.exp(1.0 - df[c])
        return df

    def generate(self, df, batch_criteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-fl")

        df.to_csv(stem_path + '.csv', sep=';', index=False)
        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-scalability-fl.png"),
                         title="Swarm Scalability: Fractional Performance Loss Due To Inter-robot Interference",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Scalability Value",
                         xvals=batch_criteria.graph_xticks(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()


class KarpFlattUnivar:
    """
    Given a swarm exhibiting speedup X with N robots(N > 1), compute the serial fraction Y of the
    swarm's performance. The lower the value of Y, the better the parallelization/scalability,
    suggesting that the addition of more robots will bring additional performance improvements:

    Y = 1/X - 1/N
        ---------
        1 - 1/N
    """

    def __init__(self, cmdopts, inter_perf_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv

    def calculate(self, batch_criteria):
        df = common.ProjectivePerformanceCalculatorUnivar(self.cmdopts,
                                                          self.inter_perf_csv,
                                                          "positive")(batch_criteria)

        sizes = batch_criteria.swarm_sizes(self.cmdopts)

        # Perfect scalability with only 1 robot
        df[df.columns[0]] = 0.0

        for i in range(1, len(df.columns)):
            c = df.columns[i]
            s = sizes[i]
            df[c] = (1.0 / df[c] - 1.0 / s) / (1 - 1.0 / s)

        return df

    def generate(self, df, batch_criteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-karpflatt")
        df.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-karpflatt.png"),
                         title="Swarm Serial Fraction: Karp-Flatt Metric",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xvals=batch_criteria.graph_xticks(self.cmdopts)[1:],
                         legend=None,
                         polynomial_fit=-1).generate()


class ScalabilityUnivar:
    """
    Calculates the scalability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def generate(self, cmdopts, batch_criteria):
        print("-- Univariate scalability from {0}".format(cmdopts["collate_root"]))

        main_config = yaml.load(open(os.path.join(cmdopts['config_root'], 'main.yaml')))

        inter_perf_csv = main_config['sierra']['perf']['inter_perf_csv']
        ca_in_csv = main_config['sierra']['perf']['ca_in_csv']

        e = EfficiencyUnivar(cmdopts, inter_perf_csv)
        e.generate(e.calculate(batch_criteria), batch_criteria)

        f = FractionalPerformanceLossUnivar(cmdopts, inter_perf_csv, ca_in_csv)
        f.generate(f.calculate(batch_criteria), batch_criteria)

        k = KarpFlattUnivar(cmdopts, inter_perf_csv)
        k.generate(k.calculate(batch_criteria), batch_criteria)
