# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Classes for executing experiments via the specified ``--execenv``."""

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
from sierra.core import types, config, engine, utils, batchroot, execenv
import sierra.core.plugin as pm


class ExpShell:
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
        self.logger.trace("Cmd: %s", spec.cmd)

        # We use a special marker at the end of the cmd's output to know when
        # the environment dump starts.
        if spec.env:
            spec.cmd += " && echo ~~~~ENV_START~~~~ && env"

        proc = subprocess.Popen(
            spec.cmd,
            shell=spec.shell,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
        )

        if not spec.wait:
            self.procs.append(proc)
            return True

        # We use communicate(), not wait() to avoid issues with IO buffers
        # becoming full (e.g., you get deadlocks with wait() regularly).
        stdout_raw, stderr_raw = proc.communicate()

        # Update the environment for all commands
        if spec.env:
            self._update_env(stdout_raw)

        # Only show output if the process failed (i.e., did not return 0)
        if proc.returncode != 0:
            self.logger.error("Cmd '%s' failed!", spec.cmd)
            stdout_str = stdout_raw.decode("utf-8")
            stderr_str = stderr_raw.decode("utf-8")

            if spec.env:
                stdout_str = stdout_str.split("~~~~ENV_START~~~~", maxsplit=1)[0]
                stderr_str = stderr_str.split("~~~~ENV_START~~~~", maxsplit=1)[0]

            self.logger.error(
                "Cmd stdout (last 10 lines): %s",
                "\n + " "\n".join(stdout_str.split("\n")[-10:]),
            )
            self.logger.error(
                "Cmd stderr (last 10 lines): %s",
                "\n" + "\n".join(stderr_str.split("\n")[-10:]),
            )
            if self.exec_strict:
                raise RuntimeError("Command failed and strict checking was requested")

            return False

        return True

    def _update_env(self, stdout) -> None:
        record = False
        for e in stdout.decode("utf-8").split("\n"):
            if record:
                candidate = e.strip().split("=")
                if len(candidate) != 2:
                    continue

                key = candidate[0]
                value = candidate[1]

                if key not in self.env or self.env[key] != value:
                    self.logger.debug(
                        "Update experiment environment: %s=%s", key, value
                    )
                    self.env[key] = value
            elif e.strip() == "~~~~ENV_START~~~~":
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

    def __init__(
        self,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
        criteria: bc.XVarBatchCriteria,
    ) -> None:
        self.cmdopts = cmdopts
        self.criteria = criteria
        self.pathset = pathset
        self.exec_exp_range = self.cmdopts["exp_range"]

        self.logger = logging.getLogger(__name__)

        utils.dir_create_checked(self.pathset.stat_exec_root, exist_ok=True)
        utils.dir_create_checked(self.pathset.scratch_root, exist_ok=True)

    def __call__(self) -> None:
        """
        Execute experiments in the batch according to configuration.

        """
        self.logger.info(
            "Engine=%s, execenv=%s",
            self.cmdopts["engine"],
            self.cmdopts["execenv"],
        )

        module = pm.pipeline.get_plugin_module(self.cmdopts["engine"])

        # Output some useful information before running
        if hasattr(module, "pre_exp_diagnostics"):
            module.pre_exp_diagnostics(self.cmdopts, self.pathset, self.logger)

        exp_all = [self.pathset.input_root / d for d in self.criteria.gen_exp_names()]

        exp_to_run = utils.exp_range_calc(
            self.cmdopts["exp_range"],
            self.pathset.input_root,
            self.criteria.gen_exp_names(),
        )

        # Verify environment is OK before running anything
        self.logger.debug("Checking --engine execution environment")
        engine.execenv_check(self.cmdopts)

        self.logger.debug("Checking --execenv execution environment")
        execenv.execenv_check(self.cmdopts)

        # Calculate path for to file for logging execution times
        now = datetime.datetime.now()
        exec_times_fpath = self.pathset.stat_exec_root / now.strftime("%Y-%m-%e-%H:%M")

        # Start a new process for the experiment shell so pre-run commands have
        # an effect (if they set environment variables, etc.).
        shell = ExpShell(self.cmdopts["exec_strict"])

        if self.cmdopts["exec_parallelism_paradigm"] is not None:
            self.logger.warning(
                "Overriding engine=%s parallelism paradigm with %s",
                self.cmdopts["engine"],
                self.cmdopts["exec_parallelism_paradigm"],
            )
            parallelism_paradigm = self.cmdopts["exec_parallelism_paradigm"]
        else:
            configurer = engine.ExpConfigurer(self.cmdopts)
            parallelism_paradigm = configurer.parallelism_paradigm()

        if parallelism_paradigm == "per-batch":
            ParallelRunner(
                self.pathset, self.cmdopts, exec_times_fpath, exp_all, shell
            )(exp_to_run)

        else:
            # Run the experiment!
            for exp in exp_to_run:
                exp_num = exp_all.index(exp)

                # Run cmds for engine-specific things to setup the experiment
                # (e.g., start daemons) if needed.
                engine_generator = engine.ExpShellCmdsGenerator(self.cmdopts, exp_num)
                execenv_generator = execenv.ExpShellCmdsGenerator(self.cmdopts, exp_num)

                for spec in execenv_generator.pre_exp_cmds():
                    shell.run_from_spec(spec)

                for spec in engine_generator.pre_exp_cmds():
                    shell.run_from_spec(spec)

                runner = SequentialRunner(
                    self.pathset,
                    self.cmdopts,
                    exec_times_fpath,
                    execenv_generator,
                    shell,
                )
                runner(exp.name, exp_num)

                # Run cmds to cleanup {execenv, engine}-specific things now that
                # the experiment is done (if needed).
                for spec in execenv_generator.post_exp_cmds():
                    shell.run_from_spec(spec)

                for spec in engine_generator.post_exp_cmds():
                    shell.run_from_spec(spec)


class SequentialRunner:
    """
    Execute each :term:`Experimental Run` in an :term:`Experiment`.

    Runs are executed parallel if the selected execution environment supports
    it, otherwise sequentially. This class is meant for executing experiments
    within a batch sequentially.
    """

    def __init__(
        self,
        pathset: batchroot.PathSet,
        cmdopts: types.Cmdopts,
        exec_times_fpath: pathlib.Path,
        generator: execenv.ExpShellCmdsGenerator,
        shell: ExpShell,
    ) -> None:

        self.exec_times_fpath = exec_times_fpath
        self.shell = shell
        self.generator = generator
        self.cmdopts = cmdopts
        self.pathset = pathset
        self.logger = logging.getLogger(__name__)

    def __call__(self, exp_name: str, exp_num: int) -> None:
        """Execute experimental runs for a single experiment."""
        exp_input_root = self.pathset.input_root / exp_name
        exp_scratch_root = self.pathset.scratch_root / exp_name
        self.logger.info(
            "Running exp%s in <batchroot>/%s",
            exp_num,
            exp_input_root.relative_to(self.pathset.root),
        )
        sys.stdout.flush()

        start = time.time()

        utils.dir_create_checked(exp_scratch_root, exist_ok=True)

        # TODO: This restriction should be removed/pushed down to execution
        # environments that require it.
        assert (
            self.cmdopts["exec_jobs_per_node"] is not None
        ), "# parallel jobs can't be None"

        exec_opts = {
            "exp_input_root": str(exp_input_root),
            "work_dir": exp_input_root,
            "exp_scratch_root": str(exp_scratch_root),
            "cmdfile_stem_path": str(
                exp_input_root / config.GNU_PARALLEL["cmdfile_stem"]
            ),
            "cmdfile_ext": config.GNU_PARALLEL["cmdfile_ext"],
            "exec_resume": self.cmdopts["exec_resume"],
            "n_jobs": self.cmdopts["exec_jobs_per_node"],
            "nodefile": self.cmdopts["nodefile"],
        }

        for spec in self.generator.exec_exp_cmds(exec_opts):
            if not self.shell.run_from_spec(spec):
                self.logger.error(
                    "Check outputs in %s for full details",
                    exec_opts["exp_scratch_root"],
                )

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Exp%s elapsed time: %s", exp_num, sec)

        with utils.utf8open(self.exec_times_fpath, "a") as f:
            f.write("exp" + str(exp_num) + ": " + str(sec) + "\n")


class ParallelRunner:
    """
    Execute all runs in all :term:`Experiments <Experiment>` in parallel.

    This class is meant for executing experiments within a batch concurrently.
    """

    def __init__(
        self,
        pathset: batchroot.PathSet,
        cmdopts: types.Cmdopts,
        exec_times_fpath: pathlib.Path,
        exp_all: list[pathlib.Path],
        shell: ExpShell,
    ) -> None:

        self.exec_times_fpath = exec_times_fpath
        self.shell = shell
        self.exp_all = exp_all
        self.cmdopts = cmdopts
        self.pathset = pathset
        self.logger = logging.getLogger(__name__)

    def __call__(self, exp_to_run: list[pathlib.Path]) -> None:
        """Execute all experimental runs for all experiments."""

        self.logger.info("Kicking off all experiments in <batchroot>")
        sys.stdout.flush()

        start = time.time()

        exp_scratch_root = self.pathset.scratch_root
        utils.dir_create_checked(exp_scratch_root, exist_ok=True)
        exec_opts = {
            "batch_root": str(self.pathset.root),
            "work_dir": str(self.pathset.root),
            "batch_scratch_root": str(self.pathset.scratch_root),
            "cmdfile_stem_path": str(
                self.pathset.root / config.GNU_PARALLEL["cmdfile_stem"]
            ),
            "cmdfile_ext": config.GNU_PARALLEL["cmdfile_ext"],
            "exec_resume": self.cmdopts["exec_resume"],
            "n_jobs": self.cmdopts["exec_jobs_per_node"],
        }

        # Run cmds for engine-specific things to setup the experiment
        # (e.g., start daemons) if needed.
        engine_generator = engine.BatchShellCmdsGenerator(self.cmdopts)
        execenv_generator = execenv.BatchShellCmdsGenerator(self.cmdopts)

        for spec in execenv_generator.pre_batch_cmds():
            self.shell.run_from_spec(spec)

        for spec in engine_generator.pre_batch_cmds():
            self.shell.run_from_spec(spec)

        for spec in execenv_generator.exec_batch_cmds(exec_opts):
            if not self.shell.run_from_spec(spec):
                self.logger.error(
                    "Check outputs in %s for full details",
                    exec_opts["batch_scratch_root"],
                )

        # Run cmds to cleanup {execenv, engine}-specific things now that
        # the experiment is done (if needed).
        for spec in execenv_generator.post_batch_cmds():
            self.shell.run_from_spec(spec)

        for spec in engine_generator.post_batch_cmds():
            self.shell.run_from_spec(spec)

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Elapsed time: %s", sec)

        with utils.utf8open(self.exec_times_fpath, "a") as f:
            f.write(": " + str(sec) + "\n")


__all__ = ["BatchExpRunner", "ExpShell", "ParallelRunner", "SequentialRunner"]
