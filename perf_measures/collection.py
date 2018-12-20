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

kBlocksGatheredCumCSV = "blocks-collected-cum.csv"


class InterExpBlockCollection:
    """
    Generates a nice graph from the cumulative blocks collected count of the swarm configuration
    across a batched set of experiments within the same scenario from collated .csv data.

    """

    def __init__(self, cmdopts):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)

    def generate(self):
        """
        Calculate the blocks collected metric for a given controller, and output a nice graph.
        """
        print("-- Block collection from {0}".format(self.cmdopts["collate_root"]))

        path = os.path.join(self.cmdopts["collate_root"], kBlocksGatheredCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        blocks = pd.read_csv(path, sep=';')
        scale_cols = [c for c in blocks.columns if c not in ['clock']]
        final_collect_count = pd.DataFrame(columns=scale_cols)

        for c in scale_cols:
            final_collect_count[c] = blocks.tail(1)[c]
        opath = os.path.join(self.cmdopts["collate_root"], "pm-blocks-collected.csv")
        final_collect_count.to_csv(opath, sep=';', index=False)

        self.cmdopts["n_exp"] = len(final_collect_count.columns)

        BatchRangedGraph(inputy_fpath=opath,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-blocks-collected.png"),
                         title="Swarm Blocks Collected",
                         xlabel=pm_utils.batch_criteria_xlabel(self.cmdopts),
                         ylabel="# Blocks",
                         xvals=pm_utils.batch_criteria_xvals(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()
