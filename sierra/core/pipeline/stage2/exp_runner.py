# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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
"""
Classes for running and single and batch experiments via the configured method specified on
the cmdline (usually GNU parallel).
"""

# Core packages
import os
import subprocess
import time
import sys
import datetime
import typing as tp
import logging  # type: tp.Any

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import types
from sierra.core import config
from sierra.core import platform
from sierra.core import utils


class BatchExpRunner:
    """
    Runs each experiment in the specified batch experiment directory in sequence
    using GNU Parallel.

    Attributes:

        batch_exp_root: Absolute path to the root directory for the batch
                        experiment (i.e. experiment directories are placed in
                        here).

        cmdopts: Dictionary of parsed cmdline options.

        criteria: Batch criteria for the experiment.

        exec_exp_range: The subset of experiments in the batch to run (can be
                        None to run all experiments in the batch).

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.BatchCriteria) -> None:
        self.cmdopts = cmdopts
        self.criteria = criteria

        self.batch_exp_root = os.path.abspath(self.cmdopts['batch_input_root'])
        self.batch_stat_root = os.path.abspath(self.cmdopts['batch_stat_root'])
        self.batch_stat_exec_root = os.path.join(self.batch_stat_root, 'exec')
        self.exec_exp_range = self.cmdopts['exp_range']

        self.logger = logging.getLogger(__name__)

        utils.dir_create_checked(self.batch_stat_exec_root, exist_ok=True)

    def __call__(self) -> None:
        """
        Runs experiments in the batch according to configuration.

        """
        exec_resume = self.cmdopts['exec_resume']
        n_jobs = self.cmdopts['exec_jobs_per_node']

        self.logger.info("Platform='%s' exec_env='%s'",
                         self.cmdopts['platform'],
                         self.cmdopts['exec_env'])

        self._prerun_diagnostics()

        exp_all = [os.path.join(self.batch_exp_root, d)
                   for d in self.criteria.gen_exp_dirnames(self.cmdopts)]

        exp_to_run = utils.exp_range_calc(self.cmdopts,
                                          self.batch_exp_root,
                                          self.criteria)

        # Verify environment is OK before running anything
        platform.ExecEnvChecker(self.cmdopts['platform'],
                                self.cmdopts['exec_env'])()

        # Calculate path for to file for logging execution times
        now = datetime.datetime.now()
        exec_times_fpath = os.path.join(self.batch_stat_exec_root,
                                        now.strftime("%Y-%m-%e-%H:%M"))

        for exp in exp_to_run:
            runner = ExpRunner(exp,
                               exp_all.index(exp),
                               self.cmdopts['platform'],
                               self.cmdopts['exec_env'],
                               exec_times_fpath)
            runner(n_jobs, exec_resume)

        # Cleanup platform-specific things now that the experiment is done (if
        # needed).
        if self.cmdopts['platform_vc']:
            platform.PostExpVCCleanup(self.cmdopts['platform'])()

    def _prerun_diagnostics(self) -> None:
        if self.cmdopts['platform'] in ['platform.argos', 'platform.rosgazebo']:
            n_threads_per_job = self.cmdopts['physics_n_threads']
            n_runs = self.cmdopts['n_runs']
            n_jobs = self.cmdopts['exec_jobs_per_node']
            s = "batch_exp_root='%s',runs/exp=%s,threads/job=%s,n_jobs=%s"
            self.logger.info(s,
                             self.cmdopts['batch_root'],
                             n_runs,
                             n_threads_per_job,
                             n_jobs)
        else:
            assert False


class ExpRunner:
    """Runs the specified # of :term:`Experimental Runs <Experimental Run>` in
    parallel using GNU Parallel on a provided set of hosts in an HPC
    environment, or on the current local machine.

    Attributes:

        exp_input_root: Absolute path to the root directory for all generated
                        run input files for the experiment (i.e. an
                        experiment directory within the batch experiment root).

        exp_num: Experiment number in the batch.

    """

    def __init__(self,
                 exp_input_root: str,
                 exp_num: int,
                 platform: str,
                 exec_env: str,
                 exec_times_fpath: str) -> None:
        self.exp_input_root = os.path.abspath(exp_input_root)
        self.exp_num = exp_num
        self.platform = platform
        self.exec_env = exec_env
        self.exec_times_fpath = exec_times_fpath
        self.logger = logging.getLogger(__name__)

    def __call__(self, n_jobs: int, exec_resume: bool) -> None:
        """Executes experimental runs for a single experiment in parallel.

        Arguments:

            n_jobs: How many concurrent jobs are allowed? (Don't want
                    to oversubscribe the machine).

            exec_resume: Is this run of SIERRA resuming a previous run that
                         failed/did not finish?
        """

        self.logger.info("Running exp%s in '%s'",
                         self.exp_num,
                         self.exp_input_root)
        sys.stdout.flush()

        start = time.time()
        parallel_opts = {

            # Root directory for the job. Chose the exp input
            # directory rather than the output directory in order to keep
            # run outputs separate from those for the framework used to
            # run the experiments.
            'jobroot_path': self.exp_input_root,
            'cmdfile_path': os.path.join(self.exp_input_root,
                                         config.kGNUParallel['cmdfile']),
            'joblog_path': os.path.join(self.exp_input_root, "parallel.log"),
            'exec_resume': exec_resume,
            'n_jobs': n_jobs
        }
        try:
            cmd = platform.GNUParallelCmdGenerator()(self.platform,
                                                     self.exec_env,
                                                     parallel_opts)
            self.logger.trace("GNU Parallel: %s", cmd)
            subprocess.run(cmd, shell=True, check=True)

        # Catch the exception but do not raise it again so that additional
        # experiments can still be run if possible
        except subprocess.CalledProcessError as e:
            self.logger.error("Experiment failed! rc=%s", e.returncode)
            self.logger.error("Check GNU parallel outputs in %s for details",
                              parallel_opts['jobroot_path'])

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info('Exp%s elapsed time: %s', self.exp_num, str(sec))

        with open(self.exec_times_fpath, 'a') as f:
            f.write('exp' + str(self.exp_num) + ': ' + str(sec) + '\n')
