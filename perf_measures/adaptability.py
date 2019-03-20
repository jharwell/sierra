"""
 Copyright 2019 John Harwell, All rights reserved.

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
from perf_measures import vcs
import perf_measures.utils as pm_utils


class InterExpAdaptability:
    """
    Calculates the adaptability of the swarm configuration across a batched set of experiments
    within the same scenario from collated .csv data. Can be generated for any batched experiment,
    but will only make sense for temporal_variance batch criteria.

    """

    def __init__(self, cmdopts):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us.
        self.cmdopts = copy.deepcopy(cmdopts)

    def generate(self):
        """
        Calculate the adaptability metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """

        print("-- Adaptability from {0}".format(self.cmdopts["collate_root"]))
        self.cmdopts["n_exp"] = pm_utils.n_exp(self.cmdopts)
        df = pd.DataFrame(columns=["exp" + str(i)
                                   for i in range(1, self.cmdopts["n_exp"])], index=[0])

        for i in range(1, self.cmdopts["n_exp"]):
            df['exp' + str(i)] = vcs.AdaptabilityCS(self.cmdopts, i)()

        opath = os.path.join(self.cmdopts["collate_root"], "pm-adaptability.csv")

        # Write .csv to file
        df.to_csv(opath, sep=';', index=False)

        BatchRangedGraph(inputy_fpath=opath,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-adaptability.png"),
                         title="Swarm Adaptability",
                         xlabel=pm_utils.batch_criteria_xlabel(self.cmdopts),
                         ylabel=vcs.method_ylabel(self.cmdopts["adaptability_cs_method"],
                                                  'adaptability'),
                         xvals=pm_utils.batch_criteria_xvals(self.cmdopts)[1:],
                         legend=None,
                         polynomial_fit=-1).generate()
