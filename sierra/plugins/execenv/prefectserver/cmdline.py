# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Common cmdline classes for the various :term:`Prefect` plugins.
"""

# Core packages
import argparse
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.plugins.execenv import hpc


class PrefectCmdline(hpc.cmdline.HPCCmdline):
    """
    Define the common :term:`Prefect` cmdline.

    This class decorates the HPC cmdline with some additional options; it
    *mostly* makes sense to consider HPC as a more general form of execution
    environment and prefect a specialization of it. Mostly.
    """

    def __init__(
        self, parents: list[argparse.ArgumentParser], stages: list[int]
    ) -> None:
        super().__init__(parents, stages)

    def init_stage2(self) -> None:
        """Add Prefect cmdline options."""
        super().init_stage2()

        self.stage2.add_argument(
            "--work-pool",
            default="sierra-pool",
            help="""
                 Name of the prefect worker pool to use.
                 """
            + self.stage_usage_doc([2]),
        )
        self.stage2.add_argument(
            "--work-queue",
            default="sierra-queue",
            help="""
                 Name of the prefect work queue to use.
                 """
            + self.stage_usage_doc([2]),
        )


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    """Update cmdopts dictionary with the prefect-specific cmdline options."""
    opts = hpc.cmdline.to_cmdopts(args)
    updates = {
        "work_pool": args.work_pool,
        "work_queue": args.work_queue,
    }
    opts |= updates
    return opts


__all__ = ["to_cmdopts"]
