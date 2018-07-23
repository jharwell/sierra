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
from pipeline.exp_csv_averager import ExpCSVAverager


class BatchedExpCSVAverager:

    """
    Averages the .csv output files for each experiment in the specified batch directory.

    Attributes:
      batch_config_leaf(str): Leaf name (i.e. no preceding path) of the template config file used during input generation.
      batch_output_root(str): Directory for averaged .csv output (relative to current dir or absolu


    """

    def __init__(self, batch_config_leaf, batch_output_root):
        self.batch_output_root = os.path.abspath(batch_output_root)
        self.batch_config_leaf = batch_config_leaf

    def average_csvs(self):
        """Average .csv output files for all experiments in the batch."""
        print("- Averaging all experiment results...")
        for item in os.listdir(self.batch_output_root):
            path = os.path.join(self.batch_output_root, item)
            if os.path.isdir(path):
                ExpCSVAverager(self.batch_config_leaf, path).average_csvs()
