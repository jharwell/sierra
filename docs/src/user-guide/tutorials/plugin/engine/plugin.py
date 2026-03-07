import typing as tp
import argparse
import logging
import pathlib

import implements

from sierra.core.experiment import bindings, definition
from sierra.core.variables import batch_criteria as bc
from sierra.core import types, utils
from sierra.plugins.execenv import hpc

from engine.matrix import cmdline as cmd


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """A class that conforms to
    :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`.
    """

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        pass

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator:
    """A class that conforms to
    :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`.
    """

    def __init__(
        self,
        cmdopts: types.Cmdopts,
        criteria: bc.BatchCriteria,
        exp_num: int,
        n_agents: tp.Optional[int],
    ) -> None:
        pass

    def pre_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_run_cmds(
        self, host: str, run_output_root: pathlib.Path
    ) -> tp.List[types.ShellCmdSpec]:
        return []


@implements.implements(bindings.IExpConfigurer)
class ExpConfigurer:
    """A class that conforms to
    :class:`~sierra.core.experiment.bindings.IExpConfigurer`.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

    def for_exp_run(
        self, exp_input_root: pathlib.Path, run_output_root: pathlib.Path
    ) -> None:
        pass

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        pass

    def parallelism_paradigm(self) -> str:
        return "per-exp"


def cmdline_parser() -> argparse.ArgumentParser:
    """
    Get a cmdline parser supporting the engine. The returned parser
    should extend :class:`~sierra.core.cmdline.BaseCmdline`.

    This example extends :class:`~sierra.core.cmdline.BaseCmdline` with:

    - :class:`~sierra.plugins.hpc.execenv.cmdline.HPCCmdline` (HPC common)
    - :class:`~cmd.EngineCmdline` (engine specifics)

    assuming this engine can run on HPC environments.
    """
    # Initialize all stages and return the initialized
    # parser to SIERRA for use.
    parser = hpc.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
    return cmd.EngineCmdline(parents=[parser], stages=[-1, 1, 2, 3, 4, 5]).parser


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Additional configuration and/or validation of the passed cmdline
    arguments pertaining to this engine. Validation should be performed
    with assert(), and the parsed argument object should be returned with any
    modifications/additions.
    """


def exec_env_check(cmdopts: types.Cmdopts):
    """
    Check the software environment (envvars, PATH, etc.) for this engine
    plugin prior to running anything in stage 2.
    """


def population_size_from_pickle(
    exp_def: tp.Union[definition.AttrChangeSet, definition.ElementAddList],
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
) -> int:
    """
    Given an experiment definition, main configuration, and cmdopts,
    get the # agents in the experiment.Size can be obtained from added
    tags or changed attributes; engine specific.

    Arguments:

        exp_def: *Part* of the pickled experiment definition object.

        main_config: Main project configuration.

        cmdopts: Dictionary of parsed cmdline options.

    """


def population_size_from_def(
    exp_def: definition.BaseExpDef, main_config: types.YAMLDict, cmdopts: types.Cmdopts
) -> int:
    """
    Arguments:

        exp_def: The *entire* experiment definition object.

        main_config: Main project configuration.

        cmdopts: Dictionary of parsed cmdline options.

    """


def agent_prefix_extract(main_config: types.YAMLDict, cmdopts: types.Cmdopts) -> str:
    """
    Arguments:

        main_config: Parsed dictionary of main YAML configuration.

        cmdopts: Dictionary of parsed command line options.
    """


def pre_exp_diagnostics(cmdopts: types.Cmdopts, logger: logging.Logger) -> None:
    """
    Arguments:

        cmdopts: Dictionary of parsed command line options.

        logger: The logger to log to.

    """


def arena_dims_from_criteria(criteria: bc.BatchCriteria) -> tp.List[utils.ArenaExtent]:
    """
    Arguments:

       criteria: The batch criteria built from cmdline specification.
    """


def expsetup_from_def(exp_def: definition.BaseExpDef) -> types.SimpleDict:
    """
    Given an experiment definition, compute the experiment setup information.
    Should contain keys:

        - ``duration`` - Duration in seconds.

        - ``n_ticks_per_sec`` - Ticks per second for controllers/sim.

    """
