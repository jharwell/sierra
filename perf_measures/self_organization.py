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


class InterExpSelfOrganization:
    """
    Calculates the self-organization of the swarm configuration across a batched set of experiments within
    the same scenario from collated .csv data.

    Assumes:
    - The batch criteria used to generate the experiment definitions was swarm size, logarithmic,
      and that the swarm size for exp0 was 1.
    - The performance criteria is # blocks gathered.
    - The only source of interference is that from collision avoidance.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root

    def generate(self):
        """
        Calculate the self-org metric for a given controller, and output a
        nice graph.
        """

        df = FractionalLosses(self.batch_output_root, self.batch_generation_root).calc()
        df_new = pd.DataFrame(columns=[c for c in df.columns if c not in ['exp0']])

        for i in range(1, len(df.columns)):
            df_new['exp' + str(i)] = - (df['exp' + str(i)] - 2 * df['exp' + str(i - 1)])

        int_path = os.path.join(self.batch_output_root, "pm-self-org.csv")
        df.to_csv(int_path, sep=';', index=False)

        RangedSizeGraph(inputy_fpath=int_path,
                        output_fpath=os.path.join(self.batch_graph_root,
                                                  "pm-self-org.eps"),
                        title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                        legend=None,
                        ylabel="").generate()
