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
import pandas as pd
from graphs.batch_ranged_graph import BatchRangedGraph
import perf_measures.utils as pm_utils
import variables.swarm_density as rho

kTargetCumCSV = "blocks-collected-cum.csv"


class Comparative:
    """
    Calculates the following scalability measure for each experiment in a batch:

    Performance N robots
    --------------------
    N * performance 1 robot

    Swarm sizes do not have to be a power of 2.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root,
                 batch_criteria):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root
        self.batch_criteria = batch_criteria

    def generate(self):
        """
        Calculate the scalability metric within each interval for a given controller.
        """

        path = os.path.join(self.batch_output_root, kTargetCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock', 'exp0']]
        cum_stem = os.path.join(self.batch_output_root, "pm-scalability-comp")
        df_new = pd.DataFrame(columns=scale_cols)

        df_new['exp0'] = 1  # Perfect scalability with 1 robot
        swarm_sizes = pm_utils.batch_swarm_sizes(self.batch_criteria,
                                                 self.batch_generation_root,
                                                 len(df.columns))
        for i in range(0, len(scale_cols)):
            col = scale_cols[i]
            n_robots = swarm_sizes[i]
            df_new[col] = df.tail(1)[col] / (df.tail(1)['exp0'] * n_robots)

        df_new = df_new.reindex(sorted(df_new.columns, key=lambda t: int(t[3:])), axis=1)
        df_new.to_csv(cum_stem + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_fpath=cum_stem + ".csv",
                         output_fpath=os.path.join(self.batch_graph_root,
                                                   "pm-scalability-comp.png"),
                         title="Swarm Comparitive Scalability",
                         xlabel=pm_utils.batch_criteria_xlabel(self.batch_criteria),
                         ylabel="Scalability Value",
                         xvals=pm_utils.batch_criteria_xvals(self.batch_criteria,
                                                             self.batch_generation_root,
                                                             len(df.columns)),
                         legend=None,
                         polynomial_fit=-1).generate()


class Normalized:
    """
    Calculates the following scalability measure for each experiment in a batch:

    Performance N robots / N

    Swarm sizes do not have to be powers of 2.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root, batch_criteria):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root
        self.batch_criteria = batch_criteria

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller."""

        path = os.path.join(self.batch_output_root, kTargetCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock']]
        cum_stem = os.path.join(self.batch_output_root, "pm-scalability-norm")
        df_new = pd.DataFrame(columns=scale_cols)
        swarm_sizes = pm_utils.batch_swarm_sizes(self.batch_criteria,
                                                 self.batch_generation_root,
                                                 len(df.columns))

        for i in range(0, len(scale_cols)):
            col = scale_cols[i]
            n_robots = swarm_sizes[i]
            df_new[col] = df.tail(1)[col] / n_robots

        df_new.to_csv(cum_stem + ".csv", sep=';', index=False)
        BatchRangedGraph(inputy_fpath=cum_stem + ".csv",
                         output_fpath=os.path.join(self.batch_graph_root,
                                                   "pm-scalability-norm.png"),
                         title="Swarm Scalability (normalized)",
                         xlabel=pm_utils.batch_criteria_xlabel(self.batch_criteria),
                         ylabel="Scalability Value",
                         xvals=pm_utils.batch_criteria_xvals(self.batch_criteria,
                                                             self.batch_generation_root,
                                                             len(df.columns)),
                         legend=None,
                         polynomial_fit=-1).generate()


class FractionalPerformanceLoss:
    """
    Calculates the scalability of across an experiment batch using fractions of performance lost due
    to inter-robot interference as swarm size increases. Swarm sizes do not have to be a power of 2.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root, batch_criteria):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root
        self.batch_criteria = batch_criteria

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller."""

        df = pm_utils.FractionalLosses(self.batch_output_root, self.batch_generation_root).calc()
        for c in df.columns:
            df[c] = 1.0 - df[c]

        path = os.path.join(self.batch_output_root, "pm-scalability-fl.csv")
        df.to_csv(path, sep=';', index=False)

        BatchRangedGraph(inputy_fpath=path,
                         output_fpath=os.path.join(self.batch_graph_root,
                                                   "pm-scalability-fl.png"),
                         title="Swarm Scalability: Fractional Performance Loss Due To Inter-robot Interference",
                         xlabel=pm_utils.batch_criteria_xlabel(self.batch_criteria),
                         ylabel="Scalability Value",
                         xvals=pm_utils.batch_criteria_xvals(self.batch_criteria,
                                                             self.batch_generation_root,
                                                             len(df.columns)),
                         legend=None,
                         polynomial_fit=-1).generate()


class InterExpScalability:
    """
    Calculates the scalability of the swarm configuration across a batched set of experiments within
    the same scenario from collated .csv data.

    Assumes:
    - The performance criteria is # blocks gathered.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root, batch_criteria):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root
        self.batch_criteria = batch_criteria

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller,
        and output a nice graph."""
        print("-- Scalability from {0}".format(self.batch_output_root))
        Comparative(self.batch_output_root, self.batch_graph_root,
                    self.batch_generation_root, self.batch_criteria).generate()
        Normalized(self.batch_output_root, self.batch_graph_root,
                   self.batch_generation_root, self.batch_criteria).generate()
        FractionalPerformanceLoss(self.batch_output_root, self.batch_graph_root,
                                  self.batch_generation_root, self.batch_criteria).generate()
