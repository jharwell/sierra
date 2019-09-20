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
from graphs.batch_ranged_graph import BatchRangedGraph
import perf_measures.utils as pm_utils
import batch_utils as butils
import math


class Efficiency:
    """
    Calculates the per-robot efficiency in the following way for each experiment in a batch:

    Performance N robots / N

    Swarm sizes do not have to be powers of 2.

    Contains separate functions for returning the calculated measure and generating a graph of the
    calculated measure.
    """

    def __init__(self, cmdopts, blocks_collected_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_stem = blocks_collected_csv.split('.')[0]

    def calculate(self):
        """
        Calculate efficiency metric for the givenn controller for each experiment in a
        batch.

        Return:
          (Calculated metric dataframe, stddev dataframe) if stddev was collected, (Calculated
          metric datafram, None) otherwise.
        """
        sc_ipath = os.path.join(self.cmdopts["collate_root"], self.blocks_collected_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation,
        if os.path.exists(stddev_ipath):
            return (self._calculate_metric(sc_ipath, True), self._calculate_metric(stddev_ipath,
                                                                                   False))
        else:
            return (self._calculate_metric(sc_ipath, True), None)

    def generate(self, dfs):
        """
        Generate an efficiency graph after calculating the metric.
        """

        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-scalability-norm")
        metric_df = dfs[0]
        stddev_df = dfs[1]
        metric_df.to_csv(cum_stem + ".csv", sep=';', index=False)
        if stddev_df is not None:
            stddev_df.to_csv(cum_stem + ".stddev", sep=';', index=False)

        self.cmdopts["n_exp"] = len(metric_df.columns)

        BatchRangedGraph(inputy_stem_fpath=cum_stem,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-efficiency.png"),
                         title="Swarm Efficiency (normalized)",
                         xlabel=butils.graph_xlabel(self.cmdopts),
                         ylabel="Efficiency",
                         xvals=butils.graph_xvals(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()

    def _calculate_metric(self, ipath, must_exist):
        assert(not (must_exist and not os.path.exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        df = pd.read_csv(ipath, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock']]
        df_new = pd.DataFrame(columns=scale_cols)
        self.cmdopts["n_exp"] = len(df.columns)
        swarm_sizes = butils.swarm_sizes(self.cmdopts)

        for i in range(0, len(scale_cols)):
            col = scale_cols[i]
            n_robots = swarm_sizes[i]
            df_new[col] = df.tail(1)[col] / n_robots
        return df_new


class ProjectivePerformanceComparison:
    """
    Calculates projective performance for each experiment i > 0 in the batch and productes a graph.
    """

    def __init__(self, cmdopts, blocks_collected_csv, projection_type):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_csv = blocks_collected_csv
        self.projection_type = projection_type

    def calculate(self):
        return pm_utils.ProjectivePerformance(self.cmdopts,
                                              self.blocks_collected_csv,
                                              self.projection_type).calculate()

    def generate(self, df):
        self.cmdopts["n_exp"] = len(df.columns) + 1
        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-pp-comp-" + self.projection_type)
        df.to_csv(cum_stem + ".csv", sep=';', index=False)
        xvals = butils.graph_xvals(self.cmdopts)

        BatchRangedGraph(inputy_stem_fpath=cum_stem + ".csv",
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-pp-comp-" + self.projection_type + ".png"),
                         title="Swarm Projective Performance Comparison ({0})".format(
                             self.projection_type),
                         xlabel=butils.graph_xlabel(self.cmdopts),
                         ylabel="Observed-Projected Ratio",
                         xvals=xvals[1:],
                         legend=None,
                         polynomial_fit=-1).generate()


class ProjectivePerformanceComparisonPositive(ProjectivePerformanceComparison):
    def __init__(self, cmdopts, blocks_collected_csv):
        super().__init__(cmdopts, blocks_collected_csv, "positive")


class ProjectivePerformanceComparisonNegative(ProjectivePerformanceComparison):
    def __init__(self, cmdopts, blocks_collected_csv):
        super().__init__(cmdopts, blocks_collected_csv, "negative")


class FractionalPerformanceLoss:
    """
    Calculates the scalability of across an experiment batch using fractions of performance lost due
    to inter-robot interference as swarm size increases. Swarm sizes do not have to be a power of 2.
    """

    def __init__(self, cmdopts, blocks_collected_csv, ca_in_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_csv = blocks_collected_csv
        self.ca_in_csv = ca_in_csv

    def calculate(self):
        df = pm_utils.FractionalLosses(self.cmdopts,
                                       self.blocks_collected_csv,
                                       self.ca_in_csv).calc()

        for c in df.columns:
            df[c] = 1.0 - 1.0 / math.exp(1.0 - df[c])
        return df

    def generate(self, df):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-fl")

        df.to_csv(stem_path + '.csv', sep=';', index=False)
        self.cmdopts["n_exp"] = len(df.columns)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-scalability-fl.png"),
                         title="Swarm Scalability: Fractional Performance Loss Due To Inter-robot Interference",
                         xlabel=butils.graph_xlabel(self.cmdopts),
                         ylabel="Scalability Value",
                         xvals=butils.graph_xvals(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()


class KarpFlatt:
    """
    Given a swarm exhibiting speedup X with N robots(N > 1), compute the serial fraction Y of the
    swarm's performance. The lower the value of Y, the better the parallelization/scalability,
    suggesting that the addition of more robots will bring additional performance improvements:

    Y = 1/X - 1/N
        ---------
        1 - 1/N
    """

    def __init__(self, cmdopts, blocks_collected_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_csv = blocks_collected_csv

    def calculate(self):
        df = pm_utils.ProjectivePerformance(self.cmdopts,
                                            self.blocks_collected_csv,
                                            "positive").calculate()

        self.cmdopts["n_exp"] = len(df.columns) + 1

        # +1 because karp-flatt is only defined for exp >= 1
        sizes = butils.swarm_sizes(self.cmdopts)[1:]

        for i in range(0, len(df.columns)):
            c = df.columns[i]
            s = sizes[i]
            df[c] = (1.0 / df[c] - 1.0 / s) / (1 - 1.0 / s)

        return df

    def generate(self, df):
        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-karpflatt")
        df.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-karpflatt.png"),
                         title="Swarm Serial Fraction: Karp-Flatt Metric",
                         xlabel=butils.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xvals=butils.graph_xvals(self.cmdopts)[1:],
                         legend=None,
                         polynomial_fit=-1).generate()


class InterExpScalability:
    """
    Calculates the scalability of the swarm configuration across a batched set of experiments within
    the same scenario from collated .csv data.

    Assumes:
    - The performance criteria is  # blocks gathered.
    """

    def __init__(self, cmdopts):
        self.cmdopts = cmdopts
        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')))

    def generate(self):
        print("-- Scalability from {0}".format(self.cmdopts["collate_root"]))

        blocks_collected_csv = self.main_config['sierra']['perf']['blocks_collected_csv']
        ca_in_csv = self.main_config['sierra']['perf']['ca_in_csv']

        e = Efficiency(self.cmdopts, blocks_collected_csv)
        e.generate(e.calculate())

        p = ProjectivePerformanceComparisonPositive(self.cmdopts, blocks_collected_csv)
        p.generate(p.calculate())

        p = ProjectivePerformanceComparisonNegative(self.cmdopts, blocks_collected_csv)
        p.generate(p.calculate())

        f = FractionalPerformanceLoss(self.cmdopts, blocks_collected_csv, ca_in_csv)
        f.generate(f.calculate())

        k = KarpFlatt(self.cmdopts, blocks_collected_csv)
        k.generate(k.calculate())
