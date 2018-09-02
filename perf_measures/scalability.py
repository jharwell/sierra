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
from graphs.ranged_size_graph import RangedSizeGraph
from perf_measures.utils import FractionalLosses

kTargetCumCSV = "blocks-collected-cum.csv"


class Comparative:
    """
    Calculates the following scalability measure for each experiment in a batch:

    Performance N robots
    --------------------
    N * performance 1 robot
    """

    def __init__(self, batch_output_root, batch_graph_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller,
        and output a nice graph."""

        path = os.path.join(self.batch_output_root, kTargetCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock', 'exp0']]
        cum_stem = os.path.join(self.batch_output_root, "pm-scalability-comp")
        df_new = pd.DataFrame(columns=scale_cols)
        for c in scale_cols:
            df_new[c] = df.tail(1)[c] / (df.tail(1)['exp0'] * 2 ** int(c[3:]))

        df_new.to_csv(cum_stem + ".csv", sep=';', index=False)

        RangedSizeGraph(inputy_fpath=cum_stem + ".csv",
                        output_fpath=os.path.join(self.batch_graph_root,
                                                  "pm-scalability-comp.eps"),
                        title="Swarm Comparitive Scalability",
                        ylabel="Scalability Value",
                        legend=None).generate()


class Normalized:
    """
    Calculates the following scalability measure for each experiment in a batch:

    Performance N robots / N
    """

    def __init__(self, batch_output_root, batch_graph_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller,
        and output a nice graph."""

        path = os.path.join(self.batch_output_root, kTargetCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock']]
        cum_stem = os.path.join(self.batch_output_root, "pm-scalability-norm")
        df_new = pd.DataFrame(columns=scale_cols)
        for c in scale_cols:
            df_new[c] = df.tail(1)[c] / (2 ** (int(c[3:])))

        df_new.to_csv(cum_stem + ".csv", sep=';', index=False)

        RangedSizeGraph(inputy_fpath=cum_stem + ".csv",
                        output_fpath=os.path.join(self.batch_graph_root,
                                                  "pm-scalability-norm.eps"),
                        title="Swarm Normalized Scalability",
                        ylabel="Scalability Value",
                        legend=None).generate()


class FractionalPerformanceLoss:
    """
    Calculates the scalability of across an experiment batch using fractions of performance lost due
    to inter-robot interference as swarm size increases.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller,
        and output a nice graph."""

        df = FractionalLosses(self.batch_output_root, self.batch_generation_root).calc()
        for c in df.columns:
            df[c] = 1.0 - df[c]

        int_path = os.path.join(self.batch_output_root, "pm-scalability-fl.csv")
        df.to_csv(int_path, sep=';', index=False)

        RangedSizeGraph(inputy_fpath=int_path,
                        output_fpath=os.path.join(self.batch_graph_root,
                                                  "pm-scalability-fl.eps"),
                        title="Swarm Scalability: Fractional Performance Loss Due To Inter-robot Interference",
                        legend=None,
                        ylabel="").generate()


class InterExpScalability:
    """
    Calculates the scalability of the swarm configuration across a batched set of experiments within
    the same scenario from collated .csv data.

    Assumes:
    - The batch criteria used to generate the experiment definitions was swarm size, logarithmic,
      and that the swarm size for exp0 was 1.
    - The performance criteria is # blocks gathered.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller,
        and output a nice graph."""

        Comparative(self.batch_output_root, self.batch_graph_root).generate()
        Normalized(self.batch_output_root, self.batch_graph_root).generate()
        FractionalPerformanceLoss(self.batch_output_root, self.batch_graph_root,
                                  self.batch_generation_root).generate()
