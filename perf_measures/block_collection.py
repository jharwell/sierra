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


class InterExpBlockCollection:
    """
    Generates a nice graph from the cumulative blocks collected count of the swarm configuration
    across a batched set of experiments within the same scenario from collated .csv data.

    """

    def __init__(self, cmdopts, blocks_collected_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_stem = blocks_collected_csv.split('.')[0]

    def generate(self, batch_criteria):
        """
        Calculate the blocks collected metric for a given controller, and output a nice graph.
        """
        print("-- Block collection from {0}".format(self.cmdopts["collate_root"]))
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["collate_root"], self.blocks_collected_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["collate_root"],
                                       "pm-" + self.blocks_collected_stem)

        if os.path.exists(stddev_ipath):
            self._generate_collected_stddev(stddev_ipath, stddev_opath)
        collected_df = self._generate_collected_csv(perf_ipath, perf_opath_stem + '.csv')

        self.cmdopts["n_exp"] = len(collected_df.columns)
        BatchRangedGraph(inputy_stem_fpath=perf_opath_stem,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-" + self.blocks_collected_stem + ".png"),
                         title="Swarm Blocks Collected",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="# Blocks",
                         xvals=batch_criteria.graph_xvals(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()

    def _generate_collected_stddev(self, ipath, opath):
        blocks_stddev_df = pd.DataFrame()
        blocks_stddev_df = pd.read_csv(ipath, sep=';')

        scale_cols = [c for c in blocks_stddev_df.columns if c not in ['clock']]
        collected_stddev_df = pd.DataFrame(columns=scale_cols)

        for c in scale_cols:
            collected_stddev_df[c] = blocks_stddev_df.tail(1)[c]

        collected_stddev_df.to_csv(opath, sep=';', index=False)

    def _generate_collected_csv(self, ipath, opath):
        assert(os.path.exists(ipath)), "FATAL: {0} does not exist".format(ipath)
        blocks_df = pd.read_csv(ipath, sep=';')

        scale_cols = [c for c in blocks_df.columns if c not in ['clock']]
        collected_df = pd.DataFrame(columns=scale_cols)

        for c in scale_cols:
            collected_df[c] = blocks_df.tail(1)[c]

        collected_df.to_csv(opath, sep=';', index=False)
        return collected_df
