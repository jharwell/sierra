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
from perf_measures import vcs


class InterExpReactivity:
    """
    Calculates the reactivity of the swarm configuration across a batched set of experiments
    within the same scenario from collated .csv data. Can be generated for any batched experiment,
    but will only make sense for temporal_variance batch criteria.

    """

    def __init__(self, cmdopts):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us.
        self.cmdopts = copy.deepcopy(cmdopts)

    def generate(self, batch_criteria):
        """
        Calculate the reactivity metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """

        print("-- Reactivity from {0}".format(self.cmdopts["collate_root"]))
        self.cmdopts["n_exp"] = batch_criteria.n_exp()
        batch_exp_dirnames = batch_criteria.gen_exp_dirnames(self.cmdopts)
        df = pd.DataFrame(columns=batch_exp_dirnames[1:self.cmdopts["n_exp"]], index=[0])

        for i in range(1, self.cmdopts["n_exp"]):
            df[batch_exp_dirnames] = vcs.ReactivityCS(self.cmdopts, i)()

        stem_opath = os.path.join(self.cmdopts["collate_root"], "pm-reactivity")

        # Write .csv to file
        df.to_csv(stem_opath + '.csv', sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_opath,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-reactivity.png"),
                         title="Swarm Reactivity",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel=vcs.method_ylabel(self.cmdopts["reactivity_cs_method"],
                                                  'reactivity'),
                         xvals=batch_criteria.graph_xvals(self.cmdopts)[1:],
                         legend=None,
                         polynomial_fit=-1).generate()
