# Copyright 2018 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/


import os
import multiprocessing
import subprocess
import logging
import typing as tp
import variables.batch_criteria as bc
from .exp_runner import ExpRunner


class BatchedExpRunner:

    """
    Runs each experiment in the specified batch directory in sequence using GNU Parallel.

    Attributes:
        batch_exp_root: Absolute path to the root directory for the batch experiment
                        (i.e. experiment directories are placed in here).
        cmdopts: Dictionary of parsed cmdline options.
        criteria: Batch criteria for the experiment.
        exec_exp_range: The subset of experiments in the batch to run (can be None to run all
                        experiments in the batch).

    """

    def __init__(self, cmdopts: tp.Dict[str, str], criteria: bc.BatchCriteria):
        self.cmdopts = cmdopts
        self.criteria = criteria

        self.batch_exp_root = os.path.abspath(self.cmdopts['generation_root'])
        self.exec_exp_range = self.cmdopts['exec_exp_range']

    def run(self,
            exec_method: str,
            n_threads_per_sim: int,
            n_sims: int,
            exec_resume: bool,
            with_rendering: bool):
        """
        Runs experiments in the batch according to configuration.

        Arguments:
            exec_method: The method of running the experiments (HPC or on local machine).
            n_threads_per_sim: How many threads each ARGoS simulation will use. Not used in this
                               function except as diagnostic output (setting # threads used is done
                               in stage1).
            n_sims: How many ARGoS simulations will be run for each experiment. Not used in this
                    function except as diagnostic output (setting # simulations used is done in
                    stage1).
            exec_resume: Is this run of SIERRA resuming a previous run that failed/did not finish?

            with_rendering: Is ARGoS headless rendering enabled? If so, we will need to kill all the
                            Xvfb processes that get run for each simulation after all experiments
                            are finished.
        """
        n_jobs = min(n_sims, max(1, int(multiprocessing.cpu_count() / float(n_threads_per_sim))))
        logging.info("Stage2: Running batched experiment in {0}: ".format(self.batch_exp_root) +
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
            exp_to_run = exp_all

        # Verify environment
        assert os.environ.get(
            "ARGOS_PLUGIN_PATH") is not None, ("FATAL: You must have ARGOS_PLUGIN_PATH defined")
        assert os.environ.get(
            "LOG4CXX_CONFIGURATION") is not None, ("FATAL: You must LOG4CXX_CONFIGURATION defined")

        for exp in exp_to_run:
            ExpRunner(exp, exp_all.index(exp), self.cmdopts['hpc_env']).run(exec_method,
                                                                            n_jobs,
                                                                            exec_resume)

        # Cleanup Xvfb processes which were started in the background
        if with_rendering:
            subprocess.run(['killall', 'Xvfb'], check=True)
