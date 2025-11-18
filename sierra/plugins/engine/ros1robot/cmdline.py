# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
Command line parsing and validation for the :term:`ROS1+robot` engine.
"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, ros1, config
from sierra.plugins import PluginCmdline
from sierra.core.ros1 import cmdline


class EngineCmdline(cmdline.ROSCmdline):
    """Defines :term:`ROS1` extensions to :class:`~sierra.core.cmdline.CoreCmdline`."""

    def __init__(
        self,
        parents: tp.Optional[list[argparse.ArgumentParser]],
        stages: list[int],
    ) -> None:
        super().__init__(parents, stages)

    def init_multistage(self) -> None:
        super().init_multistage()
        self.multistage.add_argument(
            "--skip-online-check",
            help="""
                 If passed, then the usual 'is this robot online' checks will be
                 skipped.
                 """
            + self.stage_usage_doc([1, 2]),
            action="store_true",
        )

        self.multistage.add_argument(
            "--online-check-method",
            choices=["ping+ssh", "nc+ssh"],
            help="""
                 How SIERRA should check if a given robot is online.  Valid
                 values:

                     - ``ping+ssh`` - First, verify that you can ping each the
                       hostname/IP associated with each robot.  Second, verify
                       that passwordless ssh to the hostname/IP works.  This is
                       the most common option.

                     - ``nc+ssh`` - First, verify that an ssh connection exists
                       from the SIERRA host machine to the robot on the
                       specified port using netcat.  Second, verify that
                       passwordless ssh to the robot on the specified port
                       works.  This is useful when connecting to the robots
                       through a reverse SSH tunnel, which can be necessary if
                       the robots don't have a fixed IP address and cannot be
                       addressed by FQDN (looking at you eduroam...).
                 """,
            default="ping+ssh",
        )

    def init_stage1(self) -> None:
        super().init_stage1()
        self.stage1.add_argument(
            "--skip-sync",
            help="""
                 If passed, then the generated experiment will not be synced to
                 robots.  This is useful when:

                     - You are developing your :term:`Project` and just want to
                       check locally if the experiment is being generated
                       properly.

                     - You have a lot of robots and/or the network connection
                       from the SIERRA host machine to the robots is slow, and
                       copying the experiment multiple times as you tweak
                       parameters takes a long time.
                 """
            + self.stage_usage_doc([1]),
            action="store_true",
        )

    def init_stage2(self) -> None:
        super().init_stage2()

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
            "--exec-inter-run-pause",
            metavar="SECONDS",
            help="""
                 How long to pause between :term:`Experimental Runs
                 <Experimental Run>`, giving you time to reset the environment,
                 move robots, etc.
                 """
            + self.stage_usage_doc([2]),
            type=int,
            default=config.ROS["inter_run_pause"],
        )


def build(parents: list[argparse.ArgumentParser], stages: list[int]) -> PluginCmdline:
    """
    Get a cmdline parser supporting the :term:`ROS1+Robot` engine.

    Extends built-in cmdline parser with:

        - :class:`~sierra.core.ros1.cmdline.ROSCmdline` (ROS1 common)

        - :class:`~sierra.plugins.engine.ros1robot.cmdline.EngineCmdline`
          (ROS1+robot specifics)
    """
    return EngineCmdline(parents=parents, stages=stages)


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    """Update cmdopts with ROS1+robot-specific cmdline options."""
    opts = ros1.cmdline.to_cmdopts(args)
    self_updates = {
        # Multistage
        "exec_jobs_per_node": 1,  # (1 job/robot)
        "skip_online_check": args.skip_online_check,
        "online_check_method": args.online_check_method,
        # stage 1
        "skip_sync": args.skip_sync,
        # stage 2
        "exec_resume": args.exec_resume,
        "exec_inter_run_pause": args.exec_inter_run_pause,
    }

    opts |= self_updates
    return opts


def sphinx_cmdline_stage1():
    return EngineCmdline([], [1]).parser


def sphinx_cmdline_stage2():
    return EngineCmdline([], [2]).parser


__all__ = ["EngineCmdline"]
