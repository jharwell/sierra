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
from sierra.plugins.execenv import prefectserver
from sierra.core import types
from sierra.plugins import PluginCmdline


def build(
    parents: list[argparse.ArgumentParser], stages: list[int]
) -> PluginCmdline:
    """
    Get a cmdline for the ``prefectserver.dockerremote`` execution environment.
    """
    cmdline = prefectserver.cmdline.PrefectCmdline(parents, stages)

    cmdline.stage2.add_argument(
        "--docker-extra-mounts",
        nargs="+",
        help="""
             Add extra mounts in the usual docker format, space separated.
             """
        + cmdline.stage_usage_doc([2]),
    )
    cmdline.stage2.add_argument(
        "--docker-image",
        help="""
             Path to the docker image to use.
             """
        + cmdline.stage_usage_doc([2]),
    )
    cmdline.stage2.add_argument(
        "--docker-is-host-user",
        action="store_true",
        default=False,
        help="""
             Direct prefect -> docker to run things as the host user within
             docker containers.  Said user obviously has to exist in the
             container for this to work.
             """
        + cmdline.stage_usage_doc([2]),
    )
    return cmdline


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    opts = prefectserver.cmdline.to_cmdopts(args)
    updates = {
        # stage 2
        "docker_extra_mounts": args.docker_extra_mounts,
        "docker_image": args.docker_image,
        "docker_is_host_user": args.docker_is_host_user,
    }
    opts |= updates

    return opts
