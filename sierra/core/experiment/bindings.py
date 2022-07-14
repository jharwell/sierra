# Copyright 2021 John Harwell, All rights reserved.
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

# Core packages
import typing as tp
import argparse

# 3rd party packages
import implements

# Project packages
from sierra.core import types
import sierra.core.variables.batch_criteria as bc


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

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        raise NotImplementedError

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        """During stage 1, generate :term:`Platform`-specific shell commands to
        run during stage 2 to setup the :term:`Experiment` environment. These
        commands are run prior to each experiment in the batch, in a `new`
        sub-shell which SIERRA uses to run all :term:`Experiment Runs
        <Experimental Run>` within the experiment.

        These commands can include setting up things which are common to/should
        be the same for all experimental runs within the experiment, such as
        launching daemons/background processes needed by the platform, setting
        environment variables, etc.

        """
        raise NotImplementedError

    def exec_exp_cmds(self,
                      exec_opts: types.SimpleDict) -> tp.List[types.ShellCmdSpec]:
        """During stage 1, generate the :term:`Platform`-specific shell commands
        to run during stage 2 to execute a single :term:`Experiment` in a
        :term:`Batch Experiment`. This is (usually) a single GNU parallel
        command, but it does not have to be. These commands are run in the
        `same` sub-shell as the pre- and post-exp commands.

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

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        """During stage 1, generate :term:`Platform`-specific shell commands to
        run during stage 2 after all :term:`Experimental Runs <Experimental
        Run>` for an :term:`Experiment` have finished, but before the next
        experiment in the :term:`Batch Experiment` is launched. These commands
        are run in the `same` sub-shell as the pre- and exec-exp commands.

        These commands include things like cleaning up/stopping background
        processes, visualization daemons, etc.

        """
        raise NotImplementedError


class IExpRunShellCmdsGenerator(implements.Interface):
    """Interface for generating the shell cmds to run for an :term:`Experimental Run`.

    This includes:

    - The cmds to run the prior to the run.

    - The cmds to executed the experimental run.

    - Any post-run cleanup cmds before the next run is executed.

    Depending on your environment, you may want to use :envvar:`SIERRA_ARCH`
    (either in this function or your dispatch) to chose a version of your
    simulator compiled for a given architecture for maximum performance.

    Arguments:

        cmdopts: Dictionary of parsed cmdline options.

        n_robots: The configured # of robots for the experimental run.

        exp_num: The 0-based index of the experiment in the batch.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.IConcreteBatchCriteria,
                 n_robots: int,
                 exp_num: int) -> None:
        raise NotImplementedError

    def pre_run_cmds(self,
                     host: str,
                     input_fpath: str,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        """During stage 1, generate :term:`Platform`-specific shell commands to
        run during stage 2 to setup the :term:`Experimental Run`
        environment. These commands are run prior to each experimental run in
        the :term:`Experiment`; that is prior to the :func:`exec_run_cmds()`.

        These commands can include setting up things which are unique to/should
        not be shared between experimental runs within the experiment, such as
        launching daemons/background processes, setting environment variables,
        etc.

        Arguments:

            input_fpath: Absolute path to the input/launch file for the
                         experimental run.

            run_num: The 0 based ID of the experimental run.
        """
        raise NotImplementedError

    def exec_run_cmds(self,
                      host: str,
                      input_fpath: str,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        """During stage 1, generate the :term:`Platform`-specific shell commands
        to run during stage 2 to execute a single :term:`Experimental Run` in an
        :term:`Experiment`. This is (usually) a command to launch the simulation
        environment or start the controller code on a real robot, but it doesn't
        have to be. These commands are run after the :func:`pre_run_cmds()` for
        each experimental run in the :term:`Experiment`.

        Arguments:

            input_fpath: Absolute path to the input/launch file for the
                         experimental run.

            run_num: The 0 based ID of the experimental run.

        """
        raise NotImplementedError

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        """During stage 1, generate :term:`Platform`-specific shell commands to
        run during stage 2 after a given :term:`Experimental Run` for an
        :term:`Experiment` has finished. These commands are run in the
        `same` sub-shell as the pre- and exec-run commands.

        These commands include things like cleaning up/stopping background
        processes, visualization daemons, etc.

        """
        raise NotImplementedError


class IParsedCmdlineConfigurer(implements.Interface):
    """
    Modify arguments as needed for the platform or execution environment.
    """

    def __init__(self, exec_env: str) -> None:
        """
        Arguments:

            exec_env: Whatever was passed to ``--exec-env``.
        """
        raise NotImplementedError

    def __call__(self, args: argparse.Namespace) -> None:
        """

        Arguments:

            args: The parsed namespace of cmdline arguments.
        """
        raise NotImplementedError


class ICmdlineParserGenerator(implements.Interface):
    """
    Return the argparse object containing ALL options accessible/relevant to the
    platform.

    This includes the options for whatever ``--exec-env`` are valid for the
    platform, making use of the ``parents`` option for the cmdline.

    """

    def __call__(self) -> argparse.ArgumentParser:
        raise NotImplementedError


class IExecEnvChecker(implements.Interface):
    """Perform sanity checks for stage 2 execution environment.

    This is needed because stage 2 can run separate from stage 1, and we need to
    guarantee that the execution environment we verified during stage 1 is still
    valid.

    Arguments:

        cmdopts: Dictionary of parsed cmdline options.

    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        raise NotImplementedError

    def __call__(self) -> None:
        raise NotImplementedError


class IExpConfigurer(implements.Interface):
    """Perform addition configuration after creating :term:`Experiments
    <Experiment>`.

    e.g., creating directories store outputs in if they are not created by the
    simulator/:term:`Project` code.

    Arguments:

        cmdopts: Dictionary of parsed cmdline options.

    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        raise NotImplementedError

    def for_exp(self, exp_input_root: str) -> None:
        """
        Arguments:

            exp_input_root: Absolute path to the input directory for the
                            experiment.
        """
        raise NotImplementedError

    def for_exp_run(self, exp_input_root: str, run_output_root: str) -> None:
        """
        Arguments:

            exp_input_root: Absolute path to the input directory for the
                            experiment.

            run_output_root: Absolute path to the output directory for the
                             experimental run.
        """
        raise NotImplementedError

    def cmdfile_paradigm(self) -> str:
        """
        Return either 'per-exp' or 'per-run' depending if a single GNU parallel
        cmds file should be generated per experiment or per run.
        """
        raise NotImplementedError


__api__ = [
    'IParsedCmdlineConfigurer',
    'IExpRunShellCmdsGenerator',
    'IExpShellCmdsGenerator',
    'IExpConfigurer',
    'IExecEnvChecker',
    'ICmdlineParserGenerator'
]
