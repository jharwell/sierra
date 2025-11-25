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


def build(parents: list[argparse.ArgumentParser], stages: list[int]) -> PluginCmdline:
    """
    Get a cmdline parser supporting the ``proc.imagize`` processing plugin.
    """
    cmdline = PluginCmdline(parents, stages)
    cmdline.stage3.add_argument(
        "--imagize-no-stats",
        action="store_true",
        help="""
             If the ``proc.imagize`` plugin is run, don't run statistics
             generation/assume it has already been run.  This can save TONS of
             time for:

                 - Large imagizing workloads

                 - Workloads where the memory limitations of the SIERRA host
                   machine are such that you need to specify different levels of
                   ``--processing-parallelism`` for statistics
                   calculations/imagizing to avoid filling up memory.

                 - Workloads where you don't want stats/stats don't make sense.
             """
        + cmdline.stage_usage_doc([3]),
        default=False,
    )
    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return {
        "imagize_no_stats": args.imagize_no_stats,
    }


def sphinx_cmdline_stage3():
    return build([], [3]).parser
