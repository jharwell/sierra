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
import math
import numpy as np
from graphs.stacked_line_graph import StackedLineGraph
from graphs.scalability_graph import ScalabilityGraph

kTargetIntCSV = "blocks-collected-int.csv"
kTargetCumCSV = "blocks-collected-cum.csv"


class ScalabilityMeasure:
    """
    Calculates the scalability of the swarm configuration across a sit of experiments within the
    same scenario from collated .csv data.

    Assumes:
    - The batch criteria used to generate the experiment definitions was swarm size, logarithmic,
      and that the swarm size for exp0 was 1.
    - The performance criteria is # blocks gathered.
    - (robustness): No robot failures occur, and no sensor/actuator noise is present.
    - (flexibility): Arena size/shape is the same across all experiments
    - (Reactivity): No temporal variance of environmental conditions/robot capabilities/etc is
                    present.

    """

    def __init__(self, batch_output_root, batch_graph_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller,
        and output a nice graph."""

        path = os.path.join(self.batch_output_root, kTargetIntCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock', 'exp0']]
        for c in scale_cols:
            df[c] = (df[c] / ((math.pow(2, int(c[3:]))) * df['exp0'])).replace(np.inf, 0)

        int_stem = os.path.join(self.batch_output_root, "pm-scalability-int")
        df.to_csv(int_stem + ".csv", sep=';', index=False)

        path = os.path.join(self.batch_output_root, kTargetCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock', 'exp0']]
        cum_stem = os.path.join(self.batch_output_root, "pm-scalability-cum")
        df_new = pd.DataFrame(columns=scale_cols)
        for c in scale_cols:
            df_new[c] = df.tail(1)[c] / (df.tail(1)['exp0'] * 2 ** (int(c[3:])))

        df_new.to_csv(cum_stem + ".csv", sep=';', index=False)

        StackedLineGraph(input_stem_fpath=int_stem,
                         output_fpath=os.path.join(self.batch_graph_root,
                                                   "pm-scalability-int.eps"),
                         cols=None,
                         title="Swarm Scalability (interval)",
                         legend=None,
                         xlabel="Timestep",
                         ylabel="Scalability").generate()

        ScalabilityGraph(inputy_fpath=cum_stem + ".csv",
                         output_fpath=os.path.join(self.batch_graph_root,
                                                   "pm-scalability-cum.eps")).generate()
