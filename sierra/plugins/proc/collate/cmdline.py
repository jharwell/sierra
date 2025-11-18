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
    Get a cmdline parser supporting the ``proc.collate`` processing plugin.
    """
    cmdline = PluginCmdline(parents, stages)
    cmdline.multistage.add_argument(
        "--skip-collate",
        help="""
             Specify that no collation of data across experiments within a batch
             (stage 4) or across runs within an experiment (stage 3) should be
             performed.  Useful if collation takes a long time and multiple
             types of stage 4 outputs are desired.  Collation is generally
             idempotent unless you change the stage3 options (YMMV).
             """
        + cmdline.stage_usage_doc([3, 4]),
        action="store_true",
    )
    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return {
        "skip_collate": args.skip_collate,
    }


def sphinx_cmdline_multistage():
    return build([], [3, 4]).parser
