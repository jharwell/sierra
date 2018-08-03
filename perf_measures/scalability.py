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

kTargetCSV = "blocks-collected.csv"


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

    def __init__(self, collate_root, batch_graph_root):
        self.collate_root = collate_root
        self.batch_graph_root = batch_graph_root

    def calc(self):
        """Calculate the scalability metric within each interval, as well as a cumulative average,
        and output a nice graph."""
        assert(os.path.exists(kTargetCSV))
        df = pd.read_csv(kTargetCSV, sep=';')
        new_cols = ['clock'] + sorted([c for c in df.columns if c not in ['clock']],
                                      key=lambda t: (int(t[3:])))
        df = df.reindex(new_cols, axis=1)
        scale_cols = [c for c in df.columns if c not in ['clock', 'exp0']]
        for c in scale_cols:
            df[c] = df[c].apply(lambda x: x / (math.pow(2, int(c[3:])) *
                                               df[df.loc[df[c] == x]['exp0']]))
