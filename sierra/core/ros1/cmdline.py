# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""Common cmdline classes :term:`Engines <Engine>` using :term:`ROS1`."""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, config
from sierra.plugins import PluginCmdline


class ROSCmdline(PluginCmdline):
    """Defines :term:`ROS1` common command line arguments."""

    def __init__(
        self,
        parents: tp.List[argparse.ArgumentParser],
        stages: tp.List[int],
    ) -> None:
        super().__init__(parents, stages)

    def init_multistage(self) -> None:
        self.multistage.add_argument(
            "--no-master-node",
            help="""

                                     Do not generate commands for/start a ROS1
                                     master node on the SIERRA host
                                     machine (which is the ROS1 master).

                                     This is useful when:

                                     - Using the :term:`ROS1+Robot` engine and
                                       each robot outputs their own metrics to a
                                       shared filesystem.

                                     - The SIERRA host machine does not have ROS1
                                       installed, and you are doing
                                       testing/bringup of robots.

                                     """
            + self.stage_usage_doc([1, 2]),
            action="store_true",
        )

    def init_stage1(self) -> None:
        # Experiment options

        self.stage1.add_argument(
            "--exp-setup",
            help="""
                 Defines experiment run length, ticks per second for the
                 experiment, # of datapoints to capture/capture interval for
                 each simulation.  See :ref:`usage/vars/expsetup` for a full
                 description.
                 """
            + self.stage_usage_doc([1]),
            default="exp_setup.T{0}.K{1}.N{2}".format(
                config.kROS["n_secs_per_run"],
                config.kROS["n_ticks_per_sec"],
                config.kExperimentalRunData["n_datapoints_1D"],
            ),
        )

        self.stage1.add_argument(
            "--robot",
            required=True,
            help="""
                 The key name of the robot model, which must be present in the
                 appropriate section of ``{0}`` for the :term:`Project`.  See
                 :ref:`tutorials/project/main-config` for details.
                 """.format(
                config.kYAML.main
            )
            + self.stage_usage_doc([1]),
        )


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    """Update cmdopts with ROS-specific cmdline options."""
    return {
        # multistage
        "no_master_node": args.no_master_node,
        # stage 1
        "robot": args.robot,
        "exp_setup": args.exp_setup,
    }


__all__ = [
    "ROSCmdline",
]
