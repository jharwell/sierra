import argparse

from sierra.core.experiment import bindings
from sierra.core import types


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator:
    """
    A class that conforms to
    :class:`sierra.core.experiment.bindings.IExpRunShellCmdsGenerator`.

    """


@implements.implements(bindings.IRunShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """
    A class that conforms to
    :class:`sierra.core.experiment.bindings.IExpShellCmdsGenerator`.

    """


def exec_env_check(cmdopts: types.Cmdopts):
    """
    Check the software environment for this plugin at the start of stage 2.
    """


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Additional configuration and/or validation of the passed cmdline
    arguments pertaining to this execution environment. Validation should be
    performed with assert(), and the parsed argument object should be
    returned with any modifications/additions.
    """
