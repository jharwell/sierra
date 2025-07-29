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
from sierra.core import types, cmdline


class PrefectCmdline(cmdline.BaseCmdline):
    def __init__(self, stages: tp.List[int]) -> None:
        self.parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)

        self.scaffold_cli()
        self.init_cli(stages)

    def scaffold_cli(self) -> None:
        desc = (
            "For engines which are simulators (and can "
            "therefore be run in Prefect environments)."
        )
        self.prefect = self.parser.add_argument_group("Prefect options", desc)

    def init_cli(self, stages: tp.List[int]) -> None:
        if 2 in stages:
            self.init_stage2()

    def init_stage2(self) -> None:
        """Add Prefect cmdline options."""
        self.prefect.add_argument(
            "--docker-extra-mounts",
            nargs="+",
            help="""
                 Add extra mounts in the usual docker format, space separated.
                 """
            + self.stage_usage_doc([2]),
        )
        self.prefect.add_argument(
            "--docker-image",
            help="""
                 Path to the docker image to use.
                 """
            + self.stage_usage_doc([2]),
        )
        self.prefect.add_argument(
            "--docker-is-host-user",
            action="store_true",
            default=False,
            help="""
                 Direct prefect -> docker to run things as the host user within
                 docker containers.  Said user obviously has to exist in the
                 container for this to work.
                 """
            + self.stage_usage_doc([2]),
        )

        self.prefect.add_argument(
            "--work-pool",
            default="sierra-pool",
            help="""
                 Name of the prefect worker pool to use.
                 """
            + self.stage_usage_doc([2]),
        )
        self.prefect.add_argument(
            "--work-queue",
            default="sierra-queue",
            help="""
                 Name of the prefect work queue to use.
                 """
            + self.stage_usage_doc([2]),
        )


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    """Update cmdopts dictionary with the prefect-specific cmdline options."""
    return {
        # stage 2
        "docker_extra_mounts": args.docker_extra_mounts,
        "docker_image": args.docker_image,
        "docker_is_host_user": args.docker_is_host_user,
        "work_pool": args.work_pool,
        "work_queue": args.work_queue,
    }


__all__ = [
    "PrefectCmdline",
]
