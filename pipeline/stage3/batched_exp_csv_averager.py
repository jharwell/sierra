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
from .exp_csv_averager import ExpCSVAverager


class BatchedExpCSVAverager:

    """
    Averages the .csv output files for each experiment in the specified batch directory.

    Attributes:
      ro_params(dict): Dictionary of read-only parameters for batch averaging
      batch_output_root(str): Directory for averaged .csv output (relative to current dir or absolu

    """

    def __init__(self, ro_params, batch_output_root):

        self.ro_params = ro_params
        self.batch_output_root = batch_output_root

    def run(self):
        """Average .csv output files for all experiments in the batch."""
        # Ignore the folder for .csv files collated across experiments within a batch
        experiments = [item for item in os.listdir(self.batch_output_root) if item not in [
            self.ro_params['config']['sierra']['collate_csv_leaf']]]
        for exp in experiments:
            path = os.path.join(self.batch_output_root, exp)

            if os.path.isdir(path):
                ExpCSVAverager(self.ro_params, path).run()
