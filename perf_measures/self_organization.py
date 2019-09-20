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
import batch_utils as butils
import math


class InterExpSelfOrganization:
    """
    Calculates the self-organization of the swarm configuration across a batched set of experiments
    within the same scenario from collated .csv data.

    """

    def __init__(self, cmdopts, blocks_collected_csv, ca_in_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_csv = blocks_collected_csv
        self.ca_in_csv = ca_in_csv

    def generate(self):
        """
        Calculate the self-org metric for a given controller, and generate a batched_range_graph of
        the result.
        """

        print("-- Self-organization from {0}".format(self.cmdopts["collate_root"]))
        batch_exp_dirnames = butils.exp_dirnames(self.cmdopts)
        fl = pm_utils.FractionalLosses(self.cmdopts,
                                       self.blocks_collected_csv,
                                       self.ca_in_csv).calc()
        df_new = pd.DataFrame(columns=[c for c in fl.columns if c not in batch_exp_dirnames[0]])

        self.cmdopts["n_exp"] = len(fl.columns)
        swarm_sizes = butils.swarm_sizes(self.cmdopts)

        for i in range(1, len(fl.columns)):
            theta = fl[batch_exp_dirnames[i]] - \
                float(swarm_sizes[i]) / float(swarm_sizes[i - 1]) * fl[batch_exp_dirnames[i - 1]]
            df_new.loc[0, batch_exp_dirnames[i]] = 1.0 - 1.0 / math.exp(-theta)

        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-self-org")
        df_new.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-self-org.png"),
                         title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                         xlabel=butils.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xvals=butils.graph_xvals(self.cmdopts)[1:],
                         legend=None,
                         polynomial_fit=-1).generate()
