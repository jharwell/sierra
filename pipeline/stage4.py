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

from pipeline.intra_exp_graph_generator import IntraExpGraphGenerator
from pipeline.csv_collator import CSVCollator
from pipeline.batched_intra_exp_graph_generator import BatchedIntraExpGraphGenerator
from pipeline.inter_exp_graph_generator import InterExpGraphGenerator
from pipeline.inter_exp_targets import Linegraphs

import matplotlib as mpl
mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.rcParams['figure.max_open_warning'] = 10000
mpl.use('Agg')


class PipelineStage4:

    """

    Implements stage 4 of the experimental pipeline:

    Generate a user-defined set of graphs based on the averaged results for each
     experiment, and across experiments for batches.
    """

    def __init__(self, cmdopts):
        self.cmdopts = cmdopts

    def run(self):
        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'intra':
            self._gen_intra_graphs()

        # Collation must be after intra-experiment graph generation, so that all .csv files to be
        # collated have been generated/modified according to parameters.
        CSVCollator(self.cmdopts['output_root'],
                    Linegraphs.targets('depth2' in self.cmdopts['generator']))()
        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'inter':
            self._gen_inter_graphs()

    def _gen_inter_graphs(self):
        if self.cmdopts['criteria_category'] is not None:
            print("- Stage4: Generating inter-experiment graphs...")
            InterExpGraphGenerator(self.cmdopts)()
            print("- Stage4: Inter-experiment graph generation complete")

    def _gen_intra_graphs(self):
        if self.cmdopts['criteria_category'] is not None:

            intra_exp = BatchedIntraExpGraphGenerator(self.cmdopts)
        else:
            intra_exp = IntraExpGraphGenerator(self.cmdopts)

        print("- Stage4: Generating intra-experiment graphs...")
        intra_exp()
        print("- Stage4: Intra-experiment graph generation complete")