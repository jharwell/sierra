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
from pipeline.intra_exp_graph_generator import IntraExpGraphGenerator


class BatchedIntraExpGraphGenerator:

    """
    Generates all intra-experiment graphs from a batch of experiments.

    Attributes:
    cmdopts(dict): Dictionary commandline attributes used during intra-experiment graph generation.
    """

    def __init__(self, cmdopts):
        self.cmdopts = copy.deepcopy(cmdopts)

    def __call__(self):
        """Generate all intra-experiment graphs for all experiments in the batch."""
        batch_output_root = self.cmdopts["output_root"]
        batch_graph_root = self.cmdopts["graph_root"]
        batch_generation_root = self.cmdopts['generation_root']

        for item in os.listdir(batch_output_root):

            # Roots need to be modified for each experiment for cor
            self.cmdopts["generation_root"] = os.path.join(batch_generation_root, item)
            self.cmdopts["output_root"] = os.path.join(batch_output_root, item)
            self.cmdopts["graph_root"] = os.path.join(batch_graph_root, item)
            if os.path.isdir(self.cmdopts["output_root"]) and 'collated-csvs' != item:
                IntraExpGraphGenerator(self.cmdopts)()
