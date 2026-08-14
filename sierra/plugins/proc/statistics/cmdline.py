#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
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
        "--center",
        choices=["mean", "median"],
        help="""
             Specify the measure of central tendency: mean or median.
             """
        + cmdline.stage_usage_doc([3, 4, 5]),
        default="mean",
    )
    cmdline.multistage.add_argument(
        "--spread",
        choices=["none", "conf95", "bw", "iqr"],
        help=""" Specify what kinds of measures of statistical spread, if any,
             should be calculated on the distribution of experimental data:

               - ``none`` - Do not generate any additional distribution stats.

               - For ``--center=mean``:

                 - ``conf95`` - Calculate standard deviation of experimental
                   distribution and show 95%% confidence interval on relevant
                   graphs w.r.t. the calculated mean.

                 - ``bw`` - Calculate statistics necessary to show box and
                   whisker plots around each mean point in supported
                   graphs.

                - For ``--center=median``:

                  - ``iqr`` - Calculate interquartile range (IQR) of experimental
                   distribution and show distribution on relevant
                   graphs w.r.t. the calculated median.

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
    return {"center": args.center, "spread": args.spread}


def sphinx_cmdline_multistage():
    return build([], [3, 4, 5]).parser
