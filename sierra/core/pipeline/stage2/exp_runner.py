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
"""Classes for running and single :term:`Experiments <Experiment>` and
:term:`Batch Experiments <Batch Experiment>` via the configured method specified
on the cmdline.

"""

# Core packages
import os
import subprocess
import time
import sys
import datetime
import typing as tp
import logging  # type: tp.Any
import itertools

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import types, config, platform, utils
import sierra.core.plugin_manager as pm


class ExpShell():
    def __init__(self) -> None:
        self.tag = "Finished COMMAND"
        self.initial_env = os.environ
        self.env = self.initial_env
        self.logger = logging.getLogger(__name__)

    def run_from_spec(self, spec: types.ShellCmdSpec) -> bool:
        self.logger.trace("Cmd: %s", spec['cmd'])

        proc = subprocess.Popen(spec['cmd'],
                                shell=spec['shell'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        proc.wait()
        stdout = proc.stdout.read().decode('utf-8').splitlines()
        stderr = proc.stdout.read().decode('utf-8').splitlines()

        record = False
        cmd_stdout = ''
        for e in stdout:
            if record:
                e = e.strip().split('=')
                self.env[e[0]] = e[1]
            elif e.strip() == 'Finished COMMAND':
                record = True
            else:
                cmd_stdout += e

        cmd_stderr = ''
        for e in stderr:
            cmd_stderr += e

        self.logger.trace("Cmd stdout: %s", cmd_stdout)
        self.logger.trace("Cmd stderr: %s", cmd_stderr)

        return proc.returncode == 0


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

        module = pm.SIERRAPluginManager().get_plugin_module(
            self.cmdopts['platform'])
        module.pre_exp_diagnostics(self.cmdopts, self.logger)

        exp_all = [os.path.join(self.batch_exp_root, d)
                   for d in self.criteria.gen_exp_dirnames(self.cmdopts)]

        exp_to_run = utils.exp_range_calc(self.cmdopts,
                                          self.batch_exp_root,
                                          self.criteria)

        # Verify environment is OK before running anything
        platform.ExecEnvChecker(self.cmdopts)()

        # Calculate path for to file for logging execution times
        now = datetime.datetime.now()
        exec_times_fpath = os.path.join(self.batch_stat_exec_root,
                                        now.strftime("%Y-%m-%e-%H:%M"))

        # Start a new process for the experiment shell so pre-run commands have
        # an effect (if they set environment variables, etc.).
        shell = ExpShell()

        # Run the experiment!
        for exp in exp_to_run:
            exp_num = exp_all.index(exp)

            # Run cmds for platform-specific things to setup the experiment
            # (e.g., start daemons) if needed.
            generator = platform.ExpShellCmdsGenerator(self.cmdopts, exp_num)
            for spec in generator.pre_exp_cmds():
                shell.run_from_spec(spec)

            runner = ExpRunner(exp,
                               exp_num,
                               shell,
                               generator,
                               exec_times_fpath)
            runner(n_jobs, exec_resume, self.cmdopts['nodefile'])

        # Run cmds to cleanup platform-specific things now that the experiment
        # is done (if needed).
        for spec in generator.post_exp_cmds():
            shell.run_from_spec(spec)

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
                 shell: ExpShell,
                 generator: platform.ExpShellCmdsGenerator,
                 exec_times_fpath: str) -> None:
        self.exp_input_root = os.path.abspath(exp_input_root)
        self.exp_num = exp_num
        self.shell = shell
        self.generator = generator
        self.exec_times_fpath = exec_times_fpath
        self.logger = logging.getLogger(__name__)

    def __call__(self, n_jobs: int, exec_resume: bool, nodefile: str) -> None:
        """Executes experimental runs for a single experiment in parallel.

        Arguments:

            n_jobs: How many concurrent jobs are allowed?

            exec_resume: Is this run of SIERRA resuming a previous run that
                         failed/did not finish?

            nodefile: List of compute resources to use for the experiment.
        """

        self.logger.info("Running exp%s in '%s'",
                         self.exp_num,
                         self.exp_input_root)
        sys.stdout.flush()

        start = time.time()
        exec_opts = {

            # Root directory for the job. Chose the exp input
            # directory rather than the output directory in order to keep
            # run outputs separate from those for the framework used to
            # run the experiments.
            'jobroot_path': self.exp_input_root,
            'cmdfile_path': os.path.join(self.exp_input_root,
                                         config.kGNUParallel['cmdfile']),
            'joblog_path': os.path.join(self.exp_input_root, "parallel.log"),
            'exec_resume': exec_resume,
            'n_jobs': n_jobs,
            'nodefile': nodefile
        }
        for spec in self.generator.exec_exp_cmds(exec_opts):
            if not self.shell.run_from_spec(spec):
                self.logger.error("Check outputs in %s for details",
                                  exec_opts['jobroot_path'])

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info('Exp%s elapsed time: %s', self.exp_num, str(sec))

        with open(self.exec_times_fpath, 'a') as f:
            f.write('exp' + str(self.exp_num) + ': ' + str(sec) + '\n')
