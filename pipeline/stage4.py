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
import pipeline.inter_exp_targets


class PipelineStage4:

    """

    Implements stage 4 of the experimental pipeline:

    Generate a user-defined set of graphs based on the averaged results for each
     experiment, and across experiments for batches.
    """

    def __init__(self, args):
        self.args = args

    def run(self):
        if self.args.batch_criteria is not None:
            CSVCollator(self.args.output_root,
                        pipeline.inter_exp_targets.Linegraphs.targets())()
            intra_exp = BatchedIntraExpGraphGenerator(self.args.output_root,
                                                      self.args.graph_root)
        else:
            intra_exp = IntraExpGraphGenerator(self.args.output_root,
                                               self.args.graph_root)
        print("- Generating intra-experiment graphs...")
        intra_exp()
        print("- Intra-experiment graph generation complete")

        if self.args.batch_criteria is not None:
            print("- Generating inter-experiment graphs...")
            InterExpGraphGenerator(self.args.output_root,
                                   self.args.graph_root,
                                   self.args.generation_root)()
            print("- Inter-experiment graph generation complete")
