"""
 Copyright 2018 John Harwell, All rights reserved.

This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

import os
import copy
import yaml
import pandas as pd
import numpy as np
from graphs.heatmap import Heatmap
import perf_measures.common as common
import math


class EfficiencyBivar:
    """
    Calculates the per-robot efficiency in the following way for each experiment in a bivariate
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

    def generate(self, dfs, batch_criteria):
        """
        Generate an efficiency graph after calculating the metric.
        """
        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-scalability-norm")
        metric_df, stddev_df = dfs

        metric_df.to_csv(cum_stem + ".csv", sep=';', index=False)
        if stddev_df is not None:
            stddev_df.to_csv(cum_stem + ".stddev", sep=';', index=False)

        Heatmap(input_fpath=cum_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-efficiency.png"),
                title='Swarm Efficiency (Normalized)',
                xlabel=batch_criteria.graph_ylabel(self.cmdopts),
                ylabel=batch_criteria.graph_xlabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_yvals(self.cmdopts),
                ytick_labels=batch_criteria.graph_xvals(self.cmdopts)).generate()

    # Private functions
    def __calculate_metric(self, ipath, batch_criteria, must_exist=True):
        assert(not (must_exist and not os.path.exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = pd.read_csv(ipath, sep=';')
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)
        swarm_sizes = batch_criteria.swarm_sizes(self.cmdopts)

        for i in range(0, len(eff_df.index)):
            for j in range(0, len(eff_df.columns)):
                # When collated, the column of data is written as a numpy array to string, so we
                # have to reparse it as an actual array
                arr = np.fromstring(raw_df.iloc[i, j][1:-1], dtype=np.float, sep=' ')

                # We want the CUMULATIVE count of blocks, which will be the last element in this
                # array. The second index is an artifact of how numpy represents scalars (1 element
                # arrays).
                eff_df.iloc[i, j] = arr[-1:][0] / swarm_sizes[i][j]
        return eff_df


class FractionalPerformanceLossBivar:
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
        df = common.FractionalLossesBivar(self.cmdopts,
                                          self.inter_perf_csv,
                                          self.ca_in_csv,
                                          batch_criteria).calculate(batch_criteria)

        for i in range(0, len(df.index)):
            for c in df.columns:
                df.loc[i, c] = 1.0 - 1.0 / math.exp(1.0 - df.loc[i, c])
        return df

    def generate(self, df, batch_criteria):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-fl")

        df.to_csv(stem_path + '.csv', sep=';', index=False)
        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-scalability-fl.png"),
                title="Swarm Scalability: Fractional Performance Loss Due To Inter-robot Interference",
                xlabel=batch_criteria.graph_ylabel(self.cmdopts),
                ylabel=batch_criteria.graph_xlabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_yvals(self.cmdopts),
                ytick_labels=batch_criteria.graph_xvals(self.cmdopts)).generate()


class KarpFlattBivar:
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
        import variables.swarm_size as ss
        df = common.ProjectivePerformanceCalculatorBivar(self.cmdopts,
                                                         self.inter_perf_csv,
                                                         "positive")(batch_criteria)

        # +1 because karp-flatt is only defined for exp >= 1
        sizes = batch_criteria.swarm_sizes(self.cmdopts)

        for i in range(0, len(df.index)):
            for j in range(0, len(df.columns)):
                x = df.iloc[i, j]
                n = sizes[i][j]

                # We need to know which of the 2 variables was swarm size, in order to determine
                # the correct dimension along which to compute the metric, which depends on
                # performance between adjacent swarm sizes.
                if isinstance(batch_criteria.criteria1, ss.SwarmSize):
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
                xlabel=batch_criteria.graph_ylabel(self.cmdopts),
                ylabel=batch_criteria.graph_xlabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_yvals(self.cmdopts),
                ytick_labels=batch_criteria.graph_xvals(self.cmdopts)[1:]).generate()


class ScalabilityBivar:
    """
    Calculates the scalability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in various ways.
    """

    def generate(self, cmdopts, batch_criteria):
        print("-- Bivariate scalability from {0}".format(cmdopts["collate_root"]))

        main_config = yaml.load(open(os.path.join(cmdopts['config_root'], 'main.yaml')))

        inter_perf_csv = main_config['sierra']['perf']['inter_perf_csv']
        ca_in_csv = main_config['sierra']['perf']['ca_in_csv']

        e = EfficiencyBivar(cmdopts, inter_perf_csv)
        e.generate(e.calculate(batch_criteria), batch_criteria)

        f = FractionalPerformanceLossBivar(cmdopts, inter_perf_csv, ca_in_csv)
        f.generate(f.calculate(batch_criteria), batch_criteria)

        k = KarpFlattBivar(cmdopts, inter_perf_csv)
        k.generate(k.calculate(batch_criteria), batch_criteria)
