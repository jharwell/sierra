#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import typing as tp
import argparse
import psutil

# 3rd party packages

# Project packages
import sierra.core.cmdline as cmd
from sierra.core import types


class ProcCmdline(cmd.BaseCmdline):
    """Defines common cmdline arguments for ``--proc`` plugins."""

    def __init__(self, stages: tp.List[int]) -> None:
        self.parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
        self.scaffold_cli()
        self.init_cli(stages)

    def scaffold_cli(self) -> None:
        self.stage3 = self.parser.add_argument_group(
            "Stage1: General options for processing experiment results"
        )

    def init_cli(self, stages: tp.List[int]) -> None:
        if 3 in stages:
            self.init_stage3()

    def init_stage3(self) -> None:
        # Experiment options

        self.stage3.add_argument(
            "--processing-parallelism",
            type=int,
            help="""
                 The level of parallelism to use in results processing/graph
                 generation producer-consumer queue.  This value is used to
                 allocate consumers and produces in a 3:1 ratio.  If you are
                 doing a LOT of processing, you may want to oversubscribe your
                 machine by passing a higher than default value to overcome
                 slowdown with high disk I/O.
                 """
            + self.stage_usage_doc([3, 4]),
            default=psutil.cpu_count(),
        )


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    """Update cmdopts with ROS-specific cmdline options."""
    return {
        # stage 3
        "processing_parallelism": args.processing_parallelism,
    }


def cmdline_parser(
    parents: tp.List[argparse.ArgumentParser],
) -> tp.Optional[argparse.ArgumentParser]:
    """
    Get a cmdline parser supporting ``--proc`` plugins.
    """
    return ProcCmdline(parents=parents, stages=[-1, 1, 2, 3, 4, 5]).parser


__all__ = ["cmdline_parser", "to_cmdopts", "ProcCmdline"]
