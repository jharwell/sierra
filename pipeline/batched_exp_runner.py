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
from pipeline.exp_runner import ExpRunner


class BatchedExpRunner:

    """
    Runs each experiment in the specified batch directory in sequence using GNU Parallel.

    Attributes:
      batch_exp_root(str): Root directory for the batch experiment.

    """

    def __init__(self, batch_exp_root):
        self.batch_exp_root = os.path.abspath(batch_exp_root)

    def run(self, no_msi=False):
        """Runs all experiments in the batch."""
        print("- Stage2: Running batched experiment in {0}...".format(self.batch_exp_root))
        for item in os.listdir(self.batch_exp_root):
            path = os.path.join(self.batch_exp_root, item)
            if os.path.isdir(path):
                ExpRunner(path, True).run(no_msi)
