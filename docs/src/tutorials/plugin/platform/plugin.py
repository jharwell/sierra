import typing as tp
import argparse

import implements

from sierra.core.experiment import bindings, definition
from sierra.core.variables import batch_criteria as bc
from sierra.core import hpc, platform

from platform.matrix import cmdline as cmd


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """A class that conforms to
    :class:`~sierra.core.experiment.bindings.IExpShellCmdsGenerator`.
    """


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    """A class that conforms to
    :class:`~sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`.
    """


@implements.implements(bindings.IExpConfigurer)
class ExpConfigurer():
    """A class that conforms to
    :class:`~sierra.core.experiment.bindings.IExpConfigurer`.
    """


def cmdline_parser() -> argparse.Parser:
    """
    Get a cmdline parser supporting the platform. The returned parser
    should extend :class:`~sierra.core.cmdline.BaseCmdline`.

    This example extends :class:`~sierra.core.cmdline.BaseCmdline` with:

    - :class:`~sierra.core.hpc.cmdline.HPCCmdline` (HPC common)
    - :class:`~cmd.PlatformCmdline` (platform specifics)

    assuming this platform can run on HPC environments.
    """
    # Initialize all stages and return the initialized
    # parser to SIERRA for use.
    parser = hpc.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
    return cmd.PlatformCmdline(parents=[parser],
                               stages=[-1, 1, 2, 3, 4, 5]).parser


def cmdline_postparse_configure(argparse.Namespace) -> argparse.Namespace:
    """
    Additional configuration and/or validation of the passed cmdline
    arguments pertaining to this platform. Validation should be performed
    with assert(), and the parsed argument object should be returned with any
    modifications/additions.
    """


def exec_env_check(cmdopts: types.Cmdopts):
    """
    Check the software environment (envvars, PATH, etc.) for this platform
    plugin prior to running anything in stage 2.
    """


def population_size_from_pickle(exp_def: tp.Union[xml.AttrChangeSet,
                                                  xml.ElementAddList]) -> int:
    """
    Given an experiment definition, main configuration, and cmdopts,
             get the # agents in the experiment.Size can be obtained from added tags or changed attributes; platform
    specific.

    Arguments:

        exp_def: *Part* of the pickled experiment definition object.

  """


def population_size_from_def(exp_def: definition.XMLExpDef) -> int:
    """
    Arguments:

        exp_def: The *entire* experiment definition object.

    """


def agent_prefix_extract(main_config: types.YAMLDict,
                         cmdopts: types.Cmdopts) -> str:
    """
    Arguments:

        main_config: Parsed dictionary of main YAML configuration.

        cmdopts: Dictionary of parsed command line options.
    """


def pre_exp_diagnostics(cmdopts: types.Cmdopts,
                        logger: logging.Logger) -> None:
    """
    Arguments:

        cmdopts: Dictionary of parsed command line options.

        logger: The logger to log to.

  """


def arena_dims_from_criteria(criteria: bc.BatchCriteria) -> tp.List[utils.ArenaExtent]:
    """
    Arguments:

       criteria: The batch criteria built from cmdline specification
    """
