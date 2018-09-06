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
import perf_measures.utils as pm_utils


class InterExpSelfOrganization:
    """
    Calculates the self-organization of the swarm configuration across a batched set of experiments within
    the same scenario from collated .csv data.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root, batch_criteria):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root
        self.batch_criteria = batch_criteria

    def generate(self):
        """
        Calculate the self-org metric for a given controller, and output a
        nice graph.
        """
        print("-- Self-organization from {0}".format(self.batch_output_root))
        df = pm_utils.FractionalLosses(self.batch_output_root, self.batch_generation_root).calc()
        df_new = pd.DataFrame(columns=[c for c in df.columns if c not in ['exp0']])

        # This is a tricky measure to calculate. It has 4 parts:
        #
        # 1. The difference between the performance loss observed at swarm size i and at swarm size
        #    i/2. If this difference is sub-linear (i.e. double the swarm size does not result in 2x
        #    the performance losses), then we conclude that self-organization occurred.
        #
        # 2. We take the negative inverse of this value in order to (1) be able to easily show that
        #      super-linear losses occurred (i.e. negative values), (2) magnify small differences
        #      (as the swarm size is increased logarithmically, even small sublinearities can be
        #      significant)
        #
        # 3. We multiply by log(swarm size) in order to give more weight to values at higher swarm
        #      sizes, where self organization is more reliably observed as well as more important.
        #
        # 4. We divide by the performance loss observed at swarm size i so that approaches with a
        #    smaller average performance loss (even if they have similar slopes as a function of
        #    population size as approaches with greater average performance loss) score more
        #    favorably at higher population sizes.
        for i in range(1, len(df.columns)):
            exp = -(df['exp' + str(i)] - 2 * df['exp' + str(i - 1)])
            df_new['exp' + str(i)] = (2**i) / (exp / df['exp' + str(i)])

        path = os.path.join(self.batch_output_root, "pm-self-org.csv")
        df_new.to_csv(path, sep=';', index=False)

        if "swarm_size" in self.batch_criteria:
            RangedSizeGraph(inputy_fpath=path,
                            output_fpath=os.path.join(self.batch_graph_root,
                                                      "pm-self-org.eps"),
                            title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                            ylabel="",
                            xvals=[2**x for x in range(0, len(df_new.columns))],
                            legend=None).generate()
        elif "swarm_density" in self.batch_criteria:
            sizes = []
            for i in range(0, len(df_new.columns)):
                exp_def = pm_utils.unpickle_exp_def(os.path.join(
                    self.batch_generation_root, "exp" + str(i), "exp_def.pkl"))
                for e in exp_def:
                    if 'arena.entity.quantity' in e[0]:
                        sizes.append(int(e[1]))

            RangedSizeGraph(inputy_fpath=path,
                            output_fpath=os.path.join(self.batch_graph_root,
                                                      "pm-self-org.eps"),
                            title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                            ylabel="",
                            xvals=sizes,
                            legend=None).generate()
