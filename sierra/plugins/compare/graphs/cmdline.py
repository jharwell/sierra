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
from sierra.core import types, utils
from sierra.plugins import PluginCmdline


def build(parents: list[argparse.ArgumentParser], stages: list[int]) -> PluginCmdline:
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
        "--across",
        choices=["controllers", "scenarios", "criterias"],
        help="""
             Perform a comparison *across* ``--things`` (controllers,
             scenarios, batch criteria), as configured.
             """
        + cmdline.stage_usage_doc([5]),
        default="controllers",
    )

    cmdline.stage5.add_argument(
        "--bc-cardinality",
        help="""
             Specify the cardinality of the batch criteria used.  It is much
             easier to specify this here rather than try to deduce this *before*
             creating the batch criteria for each scenario/controller to compare
             for all ``--across`` combinations.
             """
        + cmdline.stage_usage_doc([5]),
        type=int,
    )

    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    return {
        "things": args.things,
        "across": args.across,
        "bc_cardinality": args.bc_cardinality,
    }


def sphinx_cmdline_stage5():
    return build([], [5]).parser
