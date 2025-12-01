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
    Get a cmdline supporting the ``proc.statistics`` plugin.
    """
    cmdline = PluginCmdline(parents, stages)
    cmdline.multistage.add_argument(
        "--dist-stats",
        choices=["none", "all", "conf95", "bw"],
        help="""
             Specify what kinds of statistics, if any, should be calculated on
             the distribution of experimental data during stage 3 for inclusion
             on graphs during stage 4:

                 - ``none`` - Only calculate and show raw mean on graphs.

                 - ``conf95`` - Calculate standard deviation of experimental
                   distribution and show 95%% confidence interval on relevant
                   graphs.

                 - ``bw`` - Calculate statistics necessary to show box and
                   whisker plots around each point in the graph (Summary Line
                   graphs only).

                 - ``all`` - Generate all possible statistics, and plot all
                   possible statistics on graphs.
             """
        + cmdline.graphs_applicable_doc(
            [
                ":py:func:`Summary Line <sierra.core.graphs.summary_line.generate>`",
                ":py:func:`Stacked Line <sierra.core.graphs.stacked_line.generate>`",
            ]
        )
        + cmdline.stage_usage_doc([3, 4, 5]),
        default="none",
    )

    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return {"dist_stats": args.dist_stats}


def sphinx_cmdline_multistage():
    return build([], [3, 4, 5]).parser
