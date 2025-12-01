#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import argparse

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.plugins import PluginCmdline


def build(parents: list[argparse.ArgumentParser], stages: list[int]) -> PluginCmdline:
    """
    Get a cmdline supporting the ``proc.pseudostats`` plugin.
    """
    cmdline = PluginCmdline(parents, stages)
    cmdline.multistage.add_argument(
        "--dataop",
        choices=["copy", "move"],
        help="""
             Specify what kinds of data operation should be performed.

                 - ``copy`` - Data files are copied from each run output
                   directory to <batchroot>/statistics.

                 - ``move`` - Data files are moved from each run output
                   directory to <batchroot>/statistics.

             Unless your code generates TONS of outputs, prefer ``copy`` to
             ``move`` to preserve stage 3idempotency.
             """
        + cmdline.stage_usage_doc([3]),
        default="copy",
    )

    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return {"dataop": args.dataop}


def sphinx_cmdline_multistage():
    return build([], [3]).parser
