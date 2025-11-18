#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.plugins import PluginCmdline


def build(
    parents: list[argparse.ArgumentParser], stages: list[int]
) -> PluginCmdline:
    """
    Get a cmdline parser supporting the ``proc.compress`` processing plugin.
    """
    cmdline = PluginCmdline(parents, stages)
    cmdline.stage3.add_argument(
        "--compress-remove-after",
        action="store_true",
        help="""
                 If the ``proc.compress`` plugin is run, remove the uncompressed
                 :term:`Raw Output Data` files after compression.  This can save
                 TONS of disk space.  No data is lost because everything output
                 by each :term:`Experimental Run` is in the compressed archive.
                 """
        + cmdline.stage_usage_doc([3]),
        default=False,
    )
    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return {
        "compress_remove_after": args.compress_remove_after,
    }


def sphinx_cmdline_stage3():
    return build([], [3]).parser
