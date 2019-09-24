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
from graphs.heatmap import Heatmap
import variables.swarm_density as sd
import utils


class PerformanceDensityHeatmap:
    """
    Generates a heatmap of swarm performance with axes of (swarm density, block density) across a
    batched experiment within the same scenario from collated .csv data.

    """

    def __init__(self, cmdopts, inter_perf_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def generate(self, batch_criteria):
        """
        Calculate the blocks collected metric for a given controller, and output a nice graph.
        """
        print("-- Performance Density Heatmap from {0}".format(self.cmdopts["collate_root"]))
        perf_ipath = os.path.join(self.cmdopts["collate_root"],
                                  "pm-" + self.inter_perf_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["graph_root"], "pm-density-hm")

        perf_df = pd.read_csv(perf_ipath, sep=';')
        sizes = batch_criteria.swarm_sizes(self.cmdopts)

        # Restriction: Arena dimensions must be the same for all exp!
        arena_dim = utils.get_arena_dims(self.cmdopts['generator'],
                                         batch_criteria.cmdline_str,
                                         0)
        swarm_densities = [sd.Calculate(sizes[i],
                                        arena_dim[0],
                                        arena_dim[1]) for i in range(0, len(sizes))]
        block_densities = [sd.Calculate(utils.get_n_blocks(self.cmdopts, batch_criteria, i),
                                        arena_dim[0],
                                        arena_dim[1]) for i in range(0, batch_criteria.n_exp())]

        out_df = pd.DataFrame(columns=swarm_densities,
                              index=[i for i in range(0, len(block_densities))])
        for i in range(0, len(block_densities)):
            for j in range(0, len(out_df.columns)):
                out_df.iloc[i, j] = perf_df.iloc[0, j]

        out_df.to_csv(perf_opath_stem + '.csv', sep=';', index=False)
        Heatmap(input_fpath=perf_opath_stem + '.csv',
                output_fpath=perf_opath_stem + '.png',
                title='Swarm Performance: Swarm Density vs Block Density',
                xlabel='Swarm Density',
                ylabel='Block Density',
                xtick_labels=swarm_densities,
                ytick_labels=block_densities).generate()
