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
from sierra.core import types, utils
from sierra.plugins import PluginCmdline


def build(
    parents: list[argparse.ArgumentParser], stages: list[int]
) -> PluginCmdline:
    """
    Get a cmdline parser supporting the ``compare.graphs`` comparison plugin.
    """
    cmdline = PluginCmdline(parents, stages)
    cmdline.stage5.add_argument(
        "--things",
        help="""
             Comma separated list of things to compare within ``--sierra-root``.

             The first things in this list will be used as the thing of primary
             interest if ``--comparison-type`` is passed.
             """
        + cmdline.stage_usage_doc([5]),
    )

    cmdline.stage5.add_argument(
        "--things-legend",
        help="""
             Comma separated list of names to use on the legend for the
             generated comparison graphs, specified in the same order as the
             ``--things``.
             """
        + cmdline.stage_usage_doc(
            [5], "If omitted: the raw names of the compared things will be used."
        ),
    )

    cmdline.stage5.add_argument(
        "--across",
        choices=["controllers", "scenarios", "criterias"],
        help="""
             Perform a comparison *across* ``--things`` (controllers,
             scenarios, batch criteria), as configured.
             """
        + cmdline.stage_usage_doc([5]),
        default="intercc",
    )

    cmdline.stage5.add_argument(
        "--comparison-type",
        choices=["LNraw"],
        help=r"""
             Specify how controller comparisons should be performed.

             If the batch criteria is univariate, the options are:

                 - ``LNraw`` - Output raw 1D performance measures using a single
                   {0} for each measure, with all ``--things`` shown on the same
                   graph.

             If the batch criteria is bivariate, the options are:

                 - ``LNraw`` - Output raw performance measures as a set of {0},
                   where each line graph is constructed from the i-th row/column
                   for the 2D dataframe for the performance results for all
                   ``--things``.

             .. NOTE:: SIERRA cannot currently plot statistics on the linegraphs
                       built from slices of the 2D CSVs/heatmaps generated
                       during stage4, because statistics generation is limited
                       to stage3.  This limitation may be removed in a future
                       release.

             For all comparison types, ``--legend`` is used if passed for
             legend.
             """.format(
            utils.sphinx_ref(
                ":py:func:`Summary Line <sierra.core.graphs.summary_line.generate>`"
            )
        )
        + cmdline.stage_usage_doc([5]),
    )

    cmdline.stage5.add_argument(
        "--bc-cardinality",
        help="""
             Specify the cardinality of the batch criteria used.  It is not
             trivial to deduce this correctly for all ``--across`` /
             ``--comparison-type`` combinations, so for now the solution is to
             require that this be passed.
             """
        + cmdline.stage_usage_doc([5]),
        type=int,
    )

    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return {
        "things": args.things,
        "things_legend": args.things_legend,
        "across": args.across,
        "comparison_type": args.comparison_type,
        "bc_cardinality": args.bc_cardinality,
    }


def sphinx_cmdline_stage5():
    return build([], [5]).parser
