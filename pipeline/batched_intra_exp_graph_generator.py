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
from pipeline.intra_exp_graph_generator import IntraExpGraphGenerator


class BatchedIntraExpGraphGenerator:

    """
    Generates all intra-experiment graphs from a batch of experiments.

    Attributes:
    batch_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
    batch_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experimentsn.

    """

    def __init__(self, batch_output_root, batch_graph_root):
        self.batch_output_root = os.path.abspath(batch_output_root)
        self.batch_graph_root = batch_graph_root

    def __call__(self):
        """Generate all intra-experiment graphs for all experiments in the batch."""
        for item in os.listdir(self.batch_output_root):
            exp_output_root = os.path.join(self.batch_output_root, item)
            exp_graph_root = os.path.join(self.batch_graph_root, item)
            if os.path.isdir(exp_output_root) and 'collated-csvs' != item:
                IntraExpGraphGenerator(exp_output_root, exp_graph_root)()
