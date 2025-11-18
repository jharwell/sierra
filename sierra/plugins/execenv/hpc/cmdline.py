# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Common cmdline classes for the various HPC plugins.
"""

# Core packages
import argparse
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.plugins import PluginCmdline


class HPCCmdline(PluginCmdline):
    def __init__(
        self, parents: list[argparse.ArgumentParser], stages: list[int]
    ) -> None:
        super().__init__(parents, stages)

    def init_stage2(self) -> None:
        """Add HPC cmdline options.

        Options may be interpreted differently between :term:`Engines
        <Engine>`, or ignored, depending. These include:

        - ``--exec-jobs-per-node``

        - ``--exec-no-devnull``

        - ``--exec-resume``

        - ``--exec-strict``

        """
        self.stage2.add_argument(
            "--exec-jobs-per-node",
            help="""

                              Specify the maximum number of parallel jobs to run
                              per allocated node. By default this is computed
                              from the selected HPC environment for maximum
                              throughput given the desired ``--n-runs`` and CPUs
                              per allocated node. However, for some environments
                              being able to override the computed default can be
                              useful.

                              """
            + self.stage_usage_doc([2]),
            type=int,
            default=None,
        )

        self.stage2.add_argument(
            "--exec-devnull",
            help="""

                              Redirect ALL output from simulations to
                              /dev/null. Useful for engine where you can't
                              disable all INFO messages at compile time, and
                              don't want to have to grep through lots of
                              redundant stdout files to see if there were any
                              errors.

                              """
            + self.stage_usage_doc([1, 2]),
            action="store_true",
            dest="exec_devnull",
            default=True,
        )

        self.stage2.add_argument(
            "--exec-no-devnull",
            help="""

                              Don't redirect ALL output from simulations to
                              /dev/null. Useful for engines where you can't
                              disable all INFO messages at compile time, and
                              don't want to have to grep through lots of
                              redundant stdout files to see if there were any
                              errors.

                              """
            + self.stage_usage_doc([1, 2]),
            action="store_false",
            dest="exec_devnull",
        )

        self.stage2.add_argument(
            "--exec-resume",
            help="""
                 Resume a batch experiment that was killed/stopped/etc last time
                 SIERRA was run.
                 """
            + self.stage_usage_doc([2]),
            action="store_true",
            default=False,
        )

        self.stage2.add_argument(
            "--exec-strict",
            help="""
                 If passed, then if any experimental commands fail during stage
                 2 SIERRA will exit, rather than try to keep going and execute
                 the rest of the experiments.

                 Useful for:

                     - "Correctness by construction" experiments, where you know
                       if SIERRA doesn't crash and it makes it to the end of
                       your batch experiment then none of the individual
                       experiments crashed.

                     - CI pipelines.
                 """,
            action="store_true",
        )


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    """Update cmdopts dictionary with the HPC-specific cmdline options."""
    return {
        # Multistage
        "exec_devnull": args.exec_devnull,
        "exec_jobs_per_node": args.exec_jobs_per_node,
        "exec_resume": args.exec_resume,
        "exec_strict": args.exec_strict,
    }


__all__ = [
    "HPCCmdline",
]
