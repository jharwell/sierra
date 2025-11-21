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
import implements

# Project packages
from sierra.core import types
import sierra.core.variables.batch_criteria as bc


class IBatchShellCmdsGenerator(implements.Interface):
    """
    Interface for generating the shell cmds to run :term:`Batch Experiment`.

    This includes:

        - The cmds to run the prior to the batch experiment (before any
          :term:`Experimental Runs <Experimental Run>` are kicked off).

        - The cmds to run the experiment.

        - Any post-experiment cleanup cmds after all :term:`Experiments
          <Experiment>` finish.

    Arguments:
       cmdopts: Dictionary of parsed cmdline options.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        raise NotImplementedError

    def pre_batch_cmds(self) -> list[types.ShellCmdSpec]:
        """Generate shell commands to setup the environment for a :term:`Batch Experiment`.

        These commands can include setting up things which are common to/should
        be the same for all experiments within the batch, such as
        launching daemons/background processes needed by the engine, setting
        environment variables, etc.
        Called during stage 1.

        """
        raise NotImplementedError

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        """Generate shell commands to execute an :term:`Experiment`.

        These commands are run in the *same* sub-shell as the pre- and
        post-batch commands during stage 2.

        Called during stage 2.

        Arguments:
            exec_opts: A dictionary containing:

                       - ``jobroot_path`` - The root directory for the batch
                         experiment.

                       - ``exec_resume`` - Is this a resume of a previously run
                         experiment?

                       - ``joblog_path`` - The logfile for output for the
                         experiment run cmd (different than the :term:`Project`
                         code).

                       - ``cmdfile_stem_path`` - Stem of the file containing the
                         launch cmds to run (one per line), all the way up to
                         but not including the extension.

                       - ``cmdfile_ext`` - Extension of files containing the
                         launch cmds to run.

        """
        raise NotImplementedError

    def post_batch_cmds(self) -> list[types.ShellCmdSpec]:
        """Generate cmds to run after the :term:`Batch Experiment` has finished.

        Commands are run during stage 2 after all experiments have finished.
        These commands are run in the *same* sub-shell as the pre- and exec-exp
        commands.

        These commands include things like cleaning up/stopping background
        processes, visualization daemons, etc.

        Called during stage 1.
        """
        raise NotImplementedError


class IExpShellCmdsGenerator(implements.Interface):
    """
    Interface for generating the shell cmds to run for an :term:`Experiment`.

    This includes:

        - The cmds to run the prior to the experiment (before any
          :term:`Experimental Runs <Experimental Run>`).

        - The cmds to run the experiment.

        - Any post-experiment cleanup cmds before the next :term:`Experiment` is
          run.

    Arguments:

    cmdopts: Dictionary of parsed cmdline options.

    exp_num: The 0-based index of the experiment in the batch.
    """

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        raise NotImplementedError

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        """Generate shell commands to setup the environment for an :term:`Experiment`.

        These commands can include setting up things which are common to/should
        be the same for all experimental runs within the experiment, such as
        launching daemons/background processes needed by the engine, setting
        environment variables, etc.  These commands are run prior to each
        experiment in the batch during stage 2, in a `new` sub-shell which
        SIERRA uses to run all :term:`Experiment Runs <Experimental Run>` within
        the experiment.

        Called during stage 1.

        """
        raise NotImplementedError

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        """Generate shell commands to execute an :term:`Experiment`.

        This is (usually) a single GNU parallel command, but it does not have to
        be. These commands are run in the *same* sub-shell as the pre- and
        post-exp commands during stage 2.

        Called during stage 2.

        Arguments:

            exec_opts: A dictionary containing:

                       - ``jobroot_path`` - The root directory for the batch
                         experiment.

                       - ``exec_resume`` - Is this a resume of a previously run
                         experiment?

                       - ``n_jobs`` - How many parallel jobs are allowed per
                         node?

                       - ``joblog_path`` - The logfile for output for the
                         experiment run cmd (different than the :term:`Project`
                         code).

                       - ``cmdfile_stem_path`` - Stem of the file containing the
                         launch cmds to run (one per line), all the way up to
                         but not including the extension.

                       - ``cmdfile_ext`` - Extension of files containing the
                         launch cmds to run.

                       - ``nodefile`` - Path to file containing compute
                         resources for SIERRA to use to run experiments. See
                         ``--nodefile`` and :envvar:`SIERRA_NODEFILE` for
                         details.

        """
        raise NotImplementedError

    def post_exp_cmds(self) -> list[types.ShellCmdSpec]:
        """Generate shell cmds to run after an :term:`Experiment` has finished.

        Commands are run during stage 2 after all :term:`Experimental Runs
        <Experimental Run>` for an :term:`Experiment` have finished, but before
        the next experiment in the :term:`Batch Experiment` is launched.  These
        commands are run in the *same* sub-shell as the pre- and exec-exp
        commands.

        These commands include things like cleaning up/stopping background
        processes, visualization daemons, etc.

        Called during stage 1.
        """
        raise NotImplementedError


class IExpRunShellCmdsGenerator(implements.Interface):
    """Interface for generating the shell cmds to run for an :term:`Experimental Run`.

    This includes:

    - The cmds to run the prior to executing the run.

    - The cmds to execute the experimental run.

    - Any post-run cleanup cmds before the next run is executed.

    Depending on your environment, you may want to use :envvar:`SIERRA_ARCH`
    (either in this function or your dispatch) to chose a version of your
    simulator compiled for a given architecture for maximum performance.

    Arguments:

        cmdopts: Dictionary of parsed cmdline options.

        n_agents: The configured # of agents for the experimental run.

        exp_num: The 0-based index of the experiment in the batch.

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
        """Generate shell commands to setup the experimental run environment.

        These commands are run in stage 2 prior to each experimental run in the
        :term:`Experiment`; that is prior to the :func:`exec_run_cmds()`.  These
        commands can include setting up things which are unique to/should not be
        shared between experimental runs within the experiment, such as
        launching daemons/background processes, setting environment variables,
        etc.

        Called during stage 1.

        Arguments:

            input_fpath: Absolute path to the input/launch file for the
                         experimental run.

            run_num: The 0 based ID of the experimental run.

        """
        raise NotImplementedError

    def exec_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> list[types.ShellCmdSpec]:
        """Generate shell commands to execute a single :term:`Experimental Run`.

        This is (usually) a command to launch the simulation environment or
        start the controller code on a real robot, but it doesn't have to
        be. These commands are run during stage 2 after the
        :func:`pre_run_cmds()` for each experimental run in the
        :term:`Experiment`.

        Called during stage 1.

        Arguments:

            input_fpath: Absolute path to the input/launch file for the
                         experimental run.

            run_num: The 0 based ID of the experimental run.

        """
        raise NotImplementedError

    def post_run_cmds(
        self, host: str, run_output_root: pathlib.Path
    ) -> list[types.ShellCmdSpec]:
        """Generate shell commands to run after an experimental run has finished.

        These commands are run during stage 2 in the `same` sub-shell as the
        pre- and exec-run commands.  These commands can include things like
        cleaning up/stopping background processes, visualization daemons, etc.

        Called during stage 1.
        """
        raise NotImplementedError


class IExpConfigurer(implements.Interface):
    """Perform additional configuration after creating experiments in stage 1.

    E.g., creating directories store outputs in if they are not created by the
    simulator/:term:`Project` code.

    Arguments:
        cmdopts: Dictionary of parsed cmdline options.

    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        raise NotImplementedError

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        """
        Configure an :term:`Experiment`.

        Arguments:
            exp_input_root: Absolute path to the input directory for the
                            experiment.
        """
        raise NotImplementedError

    def for_exp_run(
        self, exp_input_root: pathlib.Path, run_output_root: pathlib.Path
    ) -> None:
        """
        Configure an :term:`Experimental Run`.

        Arguments:
            exp_input_root: Absolute path to the input directory for the
                            experiment.

            run_output_root: Absolute path to the output directory for the
                             experimental run.
        """
        raise NotImplementedError

    def parallelism_paradigm(self) -> str:
        """Get the paradigm to use when generating/running experiments.

        The returned value must be one of:

            - ``per-batch`` - A single cmdfile per :term:`Batch Experiment`,
              which contains the {pre,exec, post} commands to run each
              :term:`Experimental Run`, one per line.  This gives parallelism
              across all runs in all experiments in the batch.

            - ``per-exp`` - A single cmdfile per :term:`Experiment`, which
              contains the {pre, exec, post} cmds for each :term:`Experimental
              Run`, one per line.  This gives parallelism across all runs in
              each experiment; experiments are still run in sequenc.

            - ``per-run`` - A single cmdfile per :term:`Experimental Run`, which
              contains the {pre, exec, post} commands, one per line.  Multiple
              cmdfiles may be needed for a single run (e.g., for ROS1 master +
              slaves).  This gives parallelism *within* each run.

        The parallelism paradigm is part of the :term:`Engine` definition, and
        thus the "correct" paradigm to choose varies depending on the engine.
        See :ref:`tutorials/plugin/engine/config` for complete details and
        guidance.
        """
        raise NotImplementedError


__all__ = [
    "IBatchShellCmdsGenerator",
    "IExpConfigurer",
    "IExpRunShellCmdsGenerator",
    "IExpShellCmdsGenerator",
]
