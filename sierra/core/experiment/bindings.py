# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Container module for interfaces for things related to experiments.

Interfaces are implemented by {engines, exec envs}.
"""

# Core packages
import typing as tp
import pathlib

# 3rd party packages

# Project packages
from sierra.core import types
import sierra.core.variables.batch_criteria as bc


class IBatchShellCmdsGenerator:
    """Shell command generator for ``per-batch`` parallelism.

    See :ref:`arch/execution-model` for a full explanation of the parallelism
    paradigms and hook structure.

    Arguments:
        cmdopts: Dictionary of parsed cmdline options.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        raise NotImplementedError

    def pre_batch_cmds(self) -> list[types.ShellCmdSpec]:
        """Generate setup commands for the :term:`Batch Experiment`.

        Called during stage 1. Commands run before any experimental run is
        started: launching daemons, background processes, setting environment
        variables, etc. that should be common to all experiments in the batch.
        """
        raise NotImplementedError

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        """Generate the command to execute the :term:`Batch Experiment`.

        Called during stage 2. Runs in the same sub-shell as the pre- and
        post-batch commands.

        Arguments:
            exec_opts: A dictionary containing:

                       - ``jobroot_path`` - Root directory for the batch
                         experiment.

                       - ``exec_resume`` - Whether this resumes a previously
                         started experiment.

                       - ``joblog_path`` - Logfile for the experiment run
                         command (distinct from :term:`Project` code output).

                       - ``cmdfile_stem_path`` - Path to the cmdfile, excluding
                         extension.

                       - ``cmdfile_ext`` - Extension of the cmdfile.
        """
        raise NotImplementedError

    def post_batch_cmds(self) -> list[types.ShellCmdSpec]:
        """Generate cleanup commands for after the :term:`Batch Experiment`.

        Called during stage 1. Commands run after all experiments have
        finished: stopping background processes, visualization daemons, etc.
        Runs in the same sub-shell as the pre- and exec-batch commands.
        """
        raise NotImplementedError


class IExpShellCmdsGenerator:
    """Shell command generator for ``per-exp`` parallelism.

    See :ref:`arch/execution-model` for a full explanation of the parallelism
    paradigms and hook structure.

    Arguments:
        cmdopts: Dictionary of parsed cmdline options.
        exp_num: The 0-based index of the experiment in the batch.
    """

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        raise NotImplementedError

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        """Generate setup commands for an :term:`Experiment`.

        Called during stage 1. Commands run before any experimental run in
        the experiment starts, in a new sub-shell: launching daemons,
        background processes, setting environment variables, etc. that should
        be common to all runs within the experiment.
        """
        raise NotImplementedError

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        """Generate the command to execute an :term:`Experiment`.

        Typically a single GNU parallel invocation, but not required to be.
        Called during stage 2. Runs in the same sub-shell as the pre- and
        post-exp commands.

        .. NOTE:: The return value of this method is ignored when defined on
           an engine plugin. Execution environment plugins are always
           responsible for the actual parallel dispatch.

        Arguments:
            exec_opts: A dictionary containing:

                       - ``jobroot_path`` - Root directory for the batch
                         experiment.

                       - ``exec_resume`` - Whether this resumes a previously
                         started experiment.

                       - ``n_jobs`` - How many parallel jobs are allowed per
                         node.

                       - ``joblog_path`` - Logfile for the experiment run
                         command (distinct from :term:`Project` code output).

                       - ``cmdfile_stem_path`` - Path to the cmdfile, excluding
                         extension.

                       - ``cmdfile_ext`` - Extension of the cmdfile.

                       - ``nodefile`` - Path to the file containing compute
                         resources for SIERRA to use. See ``--nodefile`` and
                         :envvar:`SIERRA_NODEFILE` for details.
        """
        raise NotImplementedError

    def post_exp_cmds(self) -> list[types.ShellCmdSpec]:
        """Generate cleanup commands for after an :term:`Experiment`.

        Called during stage 1. Commands run after all :term:`Experimental
        Runs <Experimental Run>` in the experiment have finished but before
        the next experiment starts: stopping background processes, visualization
        daemons, etc. Runs in the same sub-shell as the pre- and exec-exp
        commands.
        """
        raise NotImplementedError


class IExpRunShellCmdsGenerator:
    """Shell command generator for ``per-run`` parallelism.

    See :ref:`arch/execution-model` for a full explanation of the parallelism
    paradigms and hook structure.

    You may want to use :envvar:`SIERRA_ARCH` (in this class or your dispatch)
    to select a version of your simulator compiled for a specific architecture.

    Arguments:
        cmdopts: Dictionary of parsed cmdline options.
        criteria: The batch criteria for the experiment.
        exp_num: The 0-based index of the experiment in the batch.
        n_agents: The configured number of agents for the run, if known.
    """

    def __init__(
        self,
        cmdopts: types.Cmdopts,
        criteria: bc.XVarBatchCriteria,
        exp_num: int,
        n_agents: tp.Optional[int],
    ) -> None:
        raise NotImplementedError

    def pre_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> list[types.ShellCmdSpec]:
        """Generate setup commands for an :term:`Experimental Run`.

        Called during stage 1. Commands run in stage 2 before each run:
        launching per-run daemons, background processes, or anything that
        should not be shared between runs. The ``host`` argument identifies
        which machine these commands will execute on.

        Arguments:
            host: The machine these commands will run on.
            input_fpath: Absolute path to the input/launch file for the run.
            run_num: The 0-based ID of the experimental run.
        """
        raise NotImplementedError

    def exec_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> list[types.ShellCmdSpec]:
        """Generate the command to execute a single :term:`Experimental Run`.

        Called during stage 1. Typically the simulator launch command or
        the robot controller startup command. Runs in stage 2 after
        :func:`pre_run_cmds` for each run.

        Arguments:
            host: The machine these commands will run on.
            input_fpath: Absolute path to the input/launch file for the run.
            run_num: The 0-based ID of the experimental run.
        """
        raise NotImplementedError

    def post_run_cmds(
        self, host: str, run_output_root: pathlib.Path
    ) -> list[types.ShellCmdSpec]:
        """Generate cleanup commands for after an :term:`Experimental Run`.

        Called during stage 1. Commands run in stage 2 in the same sub-shell
        as the pre- and exec-run commands: stopping background processes,
        collecting remote outputs, etc.

        Arguments:
            host: The machine these commands will run on.
            run_output_root: Absolute path to the output directory for the run.
        """
        raise NotImplementedError


class IExpConfigurer:
    """Perform additional configuration after creating experiments in stage 1.

    E.g., creating directories to store outputs in if they are not created by
    the simulator/:term:`Project` code.

    Arguments:
        cmdopts: Dictionary of parsed cmdline options.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        raise NotImplementedError

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        """Configure an :term:`Experiment`.

        Arguments:
            exp_input_root: Absolute path to the input directory for the
                            experiment.
        """
        raise NotImplementedError

    def for_exp_run(
        self, exp_input_root: pathlib.Path, run_output_root: pathlib.Path
    ) -> None:
        """Configure an :term:`Experimental Run`.

        Arguments:
            exp_input_root: Absolute path to the input directory for the
                            experiment.
            run_output_root: Absolute path to the output directory for the
                             experimental run.
        """
        raise NotImplementedError

    def parallelism_paradigm(self) -> str:
        """Return the parallelism paradigm for this engine.

        Must return one of ``per-batch``, ``per-exp``, or ``per-run``. See
        :ref:`arch/execution-model` for full details and guidance on which
        to choose.
        """
        raise NotImplementedError


__all__ = [
    "IBatchShellCmdsGenerator",
    "IExpConfigurer",
    "IExpRunShellCmdsGenerator",
    "IExpShellCmdsGenerator",
]
