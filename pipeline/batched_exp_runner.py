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

    def __init__(self, batch_exp_root, batch_exp_num):
        self.batch_exp_root = os.path.abspath(batch_exp_root)
        self.batch_exp_num = batch_exp_num

    def run(self, exec_method):
        """Runs all experiments in the batch."""
        print("- Stage2: Running batched experiment in {0}...".format(self.batch_exp_root))

        experiments = []
        if self.batch_exp_num is not None:
            min_exp = int(self.batch_exp_num.split(':')[0])
            max_exp = int(self.batch_exp_num.split(':')[1])
            assert min_exp <= max_exp, "FATAL: Min batch exp >= max batch exp({0} vs. {1})".format(
                min_exp, max_exp)

            experiments = [os.path.join(self.batch_exp_root, "exp" + str(i)) for i in range(min_exp,
                                                                                            max_exp + 1)]
        else:
            # All dirs start with 'exp', so only sort on stuff after that. Running exp in order will
            # make collecting timing data/eyeballing runtimes much easier.
            sorted_dirs = sorted(os.listdir(self.batch_exp_root), key=lambda e: int(e[3:]))
            experiments = [os.path.join(self.batch_exp_root, item) for item in sorted_dirs
                           if os.path.isdir(os.path.join(self.batch_exp_root, item))]
        for exp in experiments:
            ExpRunner(exp, True).run(exec_method)
