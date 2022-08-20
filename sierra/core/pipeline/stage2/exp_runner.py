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
"""Classes for executing experiments via the specified ``--exec-env``.

"""

# Core packages
import os
import subprocess
import time
import sys
import datetime
import logging
import pathlib
import typing as tp

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import types, config, platform, utils
import sierra.core.plugin_manager as pm


class ExpShell():
    """Launch a shell which persists across experimental runs.

    Having a persistent shell is necessary so that running pre- and post-run
    shell commands have an effect on the actual commands to execute the run. If
    you set an environment variable before the simulator launches (for example),
    and then the shell containing that change exits, and the simulator launches
    in a new shell, then the configuration has no effect. Thus, a persistent
    shell.

    """

    def __init__(self, exec_strict: bool) -> None:
        self.env = os.environ.copy()
        self.logger = logging.getLogger(__name__)
        self.procs = []  # type: tp.List[subprocess.Popen]
        self.exec_strict = exec_strict

    def run_from_spec(self, spec: types.ShellCmdSpec) -> bool:
        self.logger.trace("Cmd: %s", spec.cmd)   # type: ignore

        # We use a special marker at the end of the cmd's output to know when
        # the environment dump starts.
        if spec.env:
            spec.cmd += ' && echo ~~~~ENV_START~~~~ && env'

        proc = subprocess.Popen(spec.cmd,
                                shell=spec.shell,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env=self.env)

        if not spec.wait:
            self.procs.append(proc)
            return True

        # We use communicate(), not wait() to avoid issues with IO buffers
        # becoming full (i.e., you get deadlocks with wait() regularly).
        stdout_raw, stderr_raw = proc.communicate()

        # Update the environment for all commands
        if spec.env:
            self._update_env(stdout_raw)

        # Only show output if the process failed (i.e., did not return 0)
        if proc.returncode != 0:
            self.logger.error("Cmd '%s' failed!", spec.cmd)
            stdout_str = stdout_raw.decode("ascii")
            stderr_str = stderr_raw.decode("ascii")

            if spec.env:
                stdout_str = stdout_str.split("~~~~ENV_START~~~~", maxsplit=1)[0]
                stderr_str = stderr_str.split("~~~~ENV_START~~~~", maxsplit=1)[0]

            self.logger.error("Cmd stdout (last 10 lines): %s",
                              '\n + ''\n'.join(stdout_str.split('\n')[-10:]))
            self.logger.error("Cmd stderr (last 10 lines): %s",
                              '\n' + '\n'.join(stderr_str.split('\n')[-10:]))

            if self.exec_strict:
                raise RuntimeError(("Command failed and strict checking was "
                                    "requested"))

            return False
        else:
            return True

    def _update_env(self, stdout) -> None:
        record = False
        for e in stdout.decode('ascii').split("\n"):
            if record:
                candidate = e.strip().split('=')
                if len(candidate) != 2:
                    continue

                key = candidate[0]
                value = candidate[1]

                if key not in self.env or self.env[key] != value:
                    self.logger.debug("Update experiment environment: %s=%s",
                                      key,
                                      value)
                    self.env[key] = value
            elif e.strip() == '~~~~ENV_START~~~~':
                record = True


class BatchExpRunner:
    """Runs each :term:`Experiment` in :term:`Batch Experiment` in sequence.

    Attributes:

        batch_exp_root: Absolute path to the root directory for the batch
                        experiment inputs (i.e. experiment directories are
                        placed in here).

        batch_stat_root: Absolute path to the root directory for statistics
                         which are computed in stage {3,4} (i.e. experiment
                         directories are placed in here).

        batch_stat_exec_root: Absolute path to the root directory for statistics
                              which are generated as experiments run during
                              stage 2 (e.g., how long each experiment took).

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

        self.batch_exp_root = pathlib.Path(self.cmdopts['batch_input_root'])
        self.batch_stat_root = pathlib.Path(self.cmdopts['batch_stat_root'])
        self.batch_stat_exec_root = pathlib.Path(self.batch_stat_root / 'exec')
        self.batch_scratch_root = pathlib.Path(self.cmdopts['batch_scratch_root'])
        self.exec_exp_range = self.cmdopts['exp_range']

        self.logger = logging.getLogger(__name__)

        utils.dir_create_checked(self.batch_stat_exec_root, exist_ok=True)
        utils.dir_create_checked(self.batch_scratch_root, exist_ok=True)

    def __call__(self) -> None:
        """
        Execute experiments in the batch according to configuration.

        """
        self.logger.info("Platform='%s' exec_env='%s'",
                         self.cmdopts['platform'],
                         self.cmdopts['exec_env'])

        module = pm.pipeline.get_plugin_module(self.cmdopts['platform'])

        # Output some useful information before running
        if hasattr(module, 'pre_exp_diagnostics'):
            module.pre_exp_diagnostics(self.cmdopts, self.logger)

        exp_all = [self.batch_exp_root / d
                   for d in self.criteria.gen_exp_names(self.cmdopts)]

        exp_to_run = utils.exp_range_calc(self.cmdopts,
                                          self.batch_exp_root,
                                          self.criteria)

        # Verify environment is OK before running anything
        if hasattr(platform, 'ExecEnvChecker'):
            self.logger.debug("Checking execution environment")
            platform.ExecEnvChecker(self.cmdopts)()
        else:
            self.logger.debug("Skip execution environment checking--not needed")

        # Calculate path for to file for logging execution times
        now = datetime.datetime.now()
        exec_times_fpath = self.batch_stat_exec_root / now.strftime("%Y-%m-%e-%H:%M")

        # Start a new process for the experiment shell so pre-run commands have
        # an effect (if they set environment variables, etc.).
        shell = ExpShell(self.cmdopts['exec_strict'])

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


class ExpRunner:
    """
    Execute each :term:`Experimental Run` in an :term:`Experiment`.

    In parallel if the selected execution environment supports it, otherwise
    sequentially.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exec_times_fpath: pathlib.Path,
                 generator: platform.ExpShellCmdsGenerator,
                 shell: ExpShell) -> None:

        self.exec_times_fpath = exec_times_fpath
        self.shell = shell
        self.generator = generator
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 exp_input_root: pathlib.Path,
                 exp_num: int) -> None:
        """Execute experimental runs for a single experiment.
        """

        self.logger.info("Running exp%s in '%s'",
                         exp_num,
                         exp_input_root)
        sys.stdout.flush()

        wd = exp_input_root.relative_to(pathlib.Path().home())
        start = time.time()

        scratch_root = self.cmdopts['batch_scratch_root'] / exp_input_root.name
        utils.dir_create_checked(scratch_root, exist_ok=True)

        assert self.cmdopts['exec_jobs_per_node'] is not None, \
            "# parallel jobs can't be None"

        exec_opts = {
            'exp_input_root': str(exp_input_root),
            'work_dir': str(wd),
            'scratch_dir': str(scratch_root),
            'cmdfile_stem_path': str(exp_input_root / config.kGNUParallel['cmdfile_stem']),
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

        with utils.utf8open(self.exec_times_fpath, 'a') as f:
            f.write('exp' + str(exp_num) + ': ' + str(sec) + '\n')


__api__ = [
    'BatchExpRunner',
    'ExpRunner',
    'ExpShell'


]
