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
import pandas as pd
from graphs.batch_ranged_graph import BatchRangedGraph
import perf_measures.utils as pm_utils

kTargetCumCSV = "blocks-collected-cum.csv"


class Efficiency:
    """
    Calculates the per-robot efficiency in the following way for each experiment in a batch:

    Performance N robots / N

    Swarm sizes do not have to be powers of 2.

    Contains separate functions for returning the calculated measure and generating a graph of the
    calculated measure.
    """

    def __init__(self, cmdopts):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)

    def calculate(self):
        """
        Calculate efficiency metric for the givenn controller for each experiment in a
        batch.

        Return:
          Dataframe with the calculated metric in the first and only row for each experiment.
        """
        path = os.path.join(self.cmdopts["collate_root"], kTargetCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock']]
        df_new = pd.DataFrame(columns=scale_cols)
        self.cmdopts["n_exp"] = len(df.columns)
        swarm_sizes = pm_utils.batch_swarm_sizes(self.cmdopts)

        for i in range(0, len(scale_cols)):
            col = scale_cols[i]
            n_robots = swarm_sizes[i]
            df_new[col] = df.tail(1)[col] / n_robots

        return df_new

    def generate(self, df):
        """
        Generate an efficiency graph after calculating the metric.
        """

        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-scalability-norm")
        df.to_csv(cum_stem + ".csv", sep=';', index=False)
        self.cmdopts["n_exp"] = len(df.columns)

        BatchRangedGraph(inputy_fpath=cum_stem + ".csv",
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-efficiency.png"),
                         title="Swarm Efficiency (normalized)",
                         xlabel=pm_utils.batch_criteria_xlabel(self.cmdopts),
                         ylabel="Efficiency",
                         xvals=pm_utils.batch_criteria_xvals(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()


class ProjectivePerformanceComparison:
    """
    Calculates projective performance for each experiment i > 0 in the batch and productes a graph.
    """

    def __init__(self, cmdopts, projection_type):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.projection_type = projection_type

    def calculate(self):
        return pm_utils.ProjectivePerformance(self.cmdopts, self.projection_type).calculate()

    def generate(self, df):
        self.cmdopts["n_exp"] = len(df.columns) + 1
        cum_stem = os.path.join(self.cmdopts["collate_root"], "pm-pp-comp-" + self.projection_type)
        df.to_csv(cum_stem + ".csv", sep=';', index=False)
        xvals = pm_utils.batch_criteria_xvals(self.cmdopts)

        BatchRangedGraph(inputy_fpath=cum_stem + ".csv",
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-pp-comp-" + self.projection_type + ".png"),
                         title="Swarm Projective Performance Comparison ({0})".format(
                             self.projection_type),
                         xlabel=pm_utils.batch_criteria_xlabel(self.cmdopts),
                         ylabel="Observed-Projected Ratio",
                         xvals=xvals[1:],
                         legend=None,
                         polynomial_fit=-1).generate()


class ProjectivePerformanceComparisonPositive(ProjectivePerformanceComparison):
    def __init__(self, cmdopts):
        super().__init__(cmdopts, "positive")


class ProjectivePerformanceComparisonNegative(ProjectivePerformanceComparison):
    def __init__(self, cmdopts):
        super().__init__(cmdopts, "negative")


class FractionalPerformanceLoss:
    """
    Calculates the scalability of across an experiment batch using fractions of performance lost due
    to inter-robot interference as swarm size increases. Swarm sizes do not have to be a power of 2.
    """

    def __init__(self, cmdopts):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)

    def calculate(self):
        df = pm_utils.FractionalLosses(
            self.cmdopts["collate_root"], self.cmdopts["generation_root"]).calc()
        for c in df.columns:
            df[c] = 1.0 - df[c]
        return df

    def generate(self, df):
        path = os.path.join(self.cmdopts["collate_root"], "pm-scalability-fl.csv")
        df.to_csv(path, sep=';', index=False)

        self.cmdopts["n_exp"] = len(df.columns)
        BatchRangedGraph(inputy_fpath=path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-scalability-fl.png"),
                         title="Swarm Scalability: Fractional Performance Loss Due To Inter-robot Interference",
                         xlabel=pm_utils.batch_criteria_xlabel(self.cmdopts),
                         ylabel="Scalability Value",
                         xvals=pm_utils.batch_criteria_xvals(self.cmdopts),
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

    def __init__(self, cmdopts):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)

    def calculate(self):
        df = pm_utils.ProjectivePerformance(self.cmdopts, "positive").calculate()
        self.cmdopts["n_exp"] = len(df.columns) + 1

        # includes exp0 size which we don't want.
        sizes = pm_utils.batch_swarm_sizes(self.cmdopts)[1:]

        for i in range(0, len(df.columns)):
            c = df.columns[i]
            s = sizes[i]
            df[c] = (1.0 / df[c] - 1.0 / s) / (1 - 1.0 / s)

        return df

    def generate(self, df):
        path = os.path.join(self.cmdopts["collate_root"], "pm-karpflatt.csv")
        df.to_csv(path, sep=';', index=False)

        BatchRangedGraph(inputy_fpath=path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-karpflatt.png"),
                         title="Swarm Serial Fraction: Karp-Flatt Metric",
                         xlabel=pm_utils.batch_criteria_xlabel(self.cmdopts),
                         ylabel="",
                         xvals=pm_utils.batch_criteria_xvals(self.cmdopts)[1:],
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

    def generate(self):
        print("-- Scalability from {0}".format(self.cmdopts["collate_root"]))

        e = Efficiency(self.cmdopts)
        e.generate(e.calculate())

        p = ProjectivePerformanceComparisonPositive(self.cmdopts)
        p.generate(p.calculate())

        p = ProjectivePerformanceComparisonNegative(self.cmdopts)
        p.generate(p.calculate())

        f = FractionalPerformanceLoss(self.cmdopts)
        f.generate(f.calculate())

        k = KarpFlatt(self.cmdopts)
        k.generate(k.calculate())
