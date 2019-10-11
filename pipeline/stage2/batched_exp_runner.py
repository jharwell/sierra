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
import multiprocessing
import subprocess
from .exp_runner import ExpRunner


class BatchedExpRunner:

    """
    Runs each experiment in the specified batch directory in sequence using GNU Parallel.

    Attributes:
      batch_exp_root(str): Root directory for the batch experiment.

    """

    def __init__(self, cmdopts, criteria):
        self.cmdopts = cmdopts
        self.criteria = criteria

        self.batch_exp_root = os.path.abspath(self.cmdopts['generation_root'])
        self.exec_exp_range = self.cmdopts['exec_exp_range']

    def run(self, exec_method, n_threads_per_sim, n_sims, exec_resume, with_rendering):
        """Runs all experiments in the batch."""
        n_jobs = min(n_sims, max(1, int(multiprocessing.cpu_count() / float(n_threads_per_sim))))
        print("- Stage2: Running batched experiment in {0}: ".format(self.batch_exp_root) +
              "sims_per_exp={0},threads_per_sim={1},n_jobs={2}".format(n_sims,
                                                                       n_threads_per_sim,
                                                                       n_jobs))

        exp_all = [os.path.join(self.batch_exp_root, d)
                   for d in self.criteria.gen_exp_dirnames(self.cmdopts)]
        exp_to_run = []

        if self.exec_exp_range is not None:
            min_exp = int(self.exec_exp_range.split(':')[0])
            max_exp = int(self.exec_exp_range.split(':')[1])
            assert min_exp <= max_exp, "FATAL: Min batch exp >= max batch exp({0} vs. {1})".format(
                min_exp, max_exp)

            exp_to_run = exp_all[min_exp: max_exp + 1]
        else:
            # make collecting timing data/eyeballing runtimes much easier.
            exp_to_run = exp_all

        for exp in exp_to_run:
            ExpRunner(exp, exp_to_run.index(exp)).run(exec_method, n_jobs, exec_resume)

        # Cleanup Xvfb processes which were started in the background
        if with_rendering:
            subprocess.run(['killall', 'Xvfb'])
