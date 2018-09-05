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
from models.collision_avoidance import CAModelEnter

kTargetCumCSV = "entered-avoidance-cum-avg.csv"


class InterExpCAModelEnterGraph:
    """
    Plots analytical prediction vs empirical counts of # robots entering collision avoidance each
    timestep across swarm sizes.

    Assumes:
    - The batch criteria used to generate the experiment definitions was swarm size, logarithmic,
      and that the swarm size for exp0 was 1.
    - The performance criteria is # blocks gathered.
    - (robustness): No robot failures occur, and no sensor/actuator noise is present.
    - (flexibility): Arena size/shape is the same across all experiments
    - (Reactivity): No temporal variance of environmental conditions/robot capabilities/etc is
                    present.

    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root

    def generate(self):
        path = os.path.join(self.batch_output_root, kTargetCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock']]
        cum_stem = os.path.join(self.batch_output_root, "model-ca-enter-cum")
        df_new = pd.DataFrame(columns=scale_cols)
        model = CAModelEnter(self.batch_generation_root).calc()

        # Row 0 is analytical prediction, row 1 is empirical data
        df_new.loc[0] = model
        df_new.loc[1] = df.tail(1)[scale_cols].values[0]
        df_new.to_csv(cum_stem + ".csv", sep=';', index=False)
        RangedSizeGraph(inputy_fpath=cum_stem + ".csv",
                        output_fpath=os.path.join(self.batch_graph_root,
                                                  "model-ca-enter-cum.eps"),
                        title="Analytic Prediction vs Empirical Measurements of CA Entry",
                        ylabel="# Robots Entering CA",
                        legend=["Analytic", "Empirical"]).generate()
