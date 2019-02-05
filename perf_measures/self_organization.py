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


class InterExpSelfOrganization:
    """
    Calculates the self-organization of the swarm configuration across a batched set of experiments
    within the same scenario from collated .csv data.

    """

    def __init__(self, cmdopts):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)

    def generate(self):
        """
        Calculate the self-org metric for a given controller, and generate a ranged_size_graph of
        the result.
        """

        print("-- Self-organization from {0}".format(self.cmdopts["collate_root"]))
        df = pm_utils.FractionalLosses(self.cmdopts["collate_root"],
                                       self.cmdopts["generation_root"]).calc()
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
        self.cmdopts["n_exp"] = len(df.columns)
        swarm_sizes = pm_utils.batch_swarm_sizes(self.cmdopts)

        df_new['exp0'] = df['exp0']
        for i in range(1, len(df.columns)):
            exp = -(df['exp' + str(i)] - float(swarm_sizes[i]) /
                    float(swarm_sizes[i - 1]) * df['exp' + str(i - 1)])
            df_new['exp' + str(i)] = swarm_sizes[i] / (exp / df['exp' + str(i)])

        path = os.path.join(self.cmdopts["collate_root"], "pm-self-org.csv")
        df_new = df_new.reindex(sorted(df_new.columns, key=lambda t: int(t[3:])), axis=1)
        df_new.to_csv(path, sep=';', index=False)

        BatchRangedGraph(inputy_fpath=path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-self-org.png"),
                         title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                         xlabel=pm_utils.batch_criteria_xlabel(self.cmdopts),
                         ylabel="",
                         xvals=pm_utils.batch_criteria_xvals(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()