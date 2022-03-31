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
    """
    Launch a shell which persists across experimental runs so that running pre-
    and post-run commands has an effect on the actual commands to execute the
    run.

    """

    def __init__(self) -> None:
        self.initial_env = os.environ
        self.env = self.initial_env
        self.logger = logging.getLogger(__name__)

    def run_from_spec(self, spec: types.ShellCmdSpec) -> bool:
        self.logger.trace("Cmd: %s", spec['cmd'])
        proc = subprocess.Popen(spec['cmd'],
                                shell=spec['shell'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        if not spec['wait']:
            return True

        # We use communicate(), not wait() to avoid issues with IO buffers
        # becoming full (i.e., you get deadlocks with wait() regularly).
        stdout, stderr = proc.communicate()

        # Only show output if the process failed (i.e., did not return 0)
        if proc.returncode != 0:
            self.logger.error("Cmd '%s' failed!", spec['cmd'])
            stdout = '\n' + '\n'.join(stdout.decode('ascii').split('\n')[-10:])
            stderr = '\n' + '\n'.join(stderr.decode('ascii').split('\n')[-10:])
            self.logger.error("Cmd stdout (last 10 lines): %s", stdout)
            self.logger.error("Cmd stderr (last 10 lines): %s", stderr)
            return False
        else:
            return True


class BatchExpRunner:
    """
    Runs each :term:`Experiment` in :term:`Batch Experiment` in sequence.

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
        self.batch_scratch_root = os.path.abspath(
            self.cmdopts['batch_scratch_root'])
        self.exec_exp_range = self.cmdopts['exp_range']

        self.logger = logging.getLogger(__name__)

        utils.dir_create_checked(self.batch_stat_exec_root, exist_ok=True)
        utils.dir_create_checked(self.batch_scratch_root, exist_ok=True)

    def __call__(self) -> None:
        """
        Runs experiments in the batch according to configuration.

        """
        self.logger.info("Platform='%s' exec_env='%s'",
                         self.cmdopts['platform'],
                         self.cmdopts['exec_env'])

        module = pm.pipeline.get_plugin_module(
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
            generator = platform.ExpShellCmdsGenerator(self.cmdopts,
                                                       exp_num)
            for spec in generator.pre_exp_cmds():
                shell.run_from_spec(spec)

            runner = ExpRunner(self.cmdopts,
                               exec_times_fpath,
                               generator,
                               shell)
            runner(exp, exp_num)

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
    """
    Execute each :term:`Experimental Run` in a :term:`Experiment`.

    In parallel if the selected execution environment supports it, otherwise
    sequentially.

    Attributes:

        exp_input_root: Absolute path to the root directory for all generated
                        run input files for the experiment (i.e. an
                        experiment directory within the batch experiment root).

        exp_num: Experiment number in the batch.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exec_times_fpath: str,
                 generator: platform.ExpShellCmdsGenerator,
                 shell: ExpShell) -> None:

        self.exec_times_fpath = exec_times_fpath
        self.shell = shell
        self.generator = generator
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 exp_input_root: str,
                 exp_num: int) -> None:
        """Executes experimental runs for a single experiment in parallel.

        Arguments:

            n_jobs: How many concurrent jobs are allowed?

            exec_resume: Is this run of SIERRA resuming a previous run that
                         failed/did not finish?

            nodefile: List of compute resources to use for the experiment.
        """

        self.logger.info("Running exp%s in '%s'",
                         exp_num,
                         exp_input_root)
        sys.stdout.flush()

        wd = os.path.relpath(exp_input_root, os.path.expanduser("~"))
        start = time.time()
        _, exp = os.path.split(exp_input_root)

        scratch_root = os.path.join(self.cmdopts['batch_scratch_root'],
                                    exp)
        utils.dir_create_checked(scratch_root, exist_ok=True)
        exec_opts = {
            'exp_input_root': exp_input_root,
            'work_dir': wd,
            'scratch_dir': scratch_root,
            'cmdfile_stem_path': os.path.join(exp_input_root,
                                              config.kGNUParallel['cmdfile_stem']),
            'cmdfile_ext': config.kGNUParallel['cmdfile_ext'],
            'exec_resume': self.cmdopts['exec_resume'],
            'n_jobs': self.cmdopts['exec_jobs_per_node'],
            'nodefile': self.cmdopts['nodefile']
        }
        for spec in self.generator.exec_exp_cmds(exec_opts):
            if not self.shell.run_from_spec(spec):
                self.logger.error("Check outputs in %s for full details",
                                  exec_opts['scratch_dir'])

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info('Exp%s elapsed time: %s', exp_num, sec)

        with open(self.exec_times_fpath, 'a') as f:
            f.write('exp' + str(exp_num) + ': ' + str(sec) + '\n')


__api__ = [
    'BatchExpRunner',
    'ExpRunner',
    'ExpShell'
]
