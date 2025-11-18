# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
Command line parsing and validation for the :term:`ROS1+Gazebo` engine.
"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core import config
from sierra.core import ros1
from sierra.plugins import PluginCmdline


class EngineCmdline(ros1.cmdline.ROSCmdline):
    """Defines :term:`ROS1+Gazebo` extensions to :class:`~sierra.core.cmdline.CoreCmdline`."""

    def __init__(
        self,
        parents: list[argparse.ArgumentParser],
        stages: list[int],
    ) -> None:
        super().__init__(parents, stages)

    def init_stage1(self) -> None:
        super().init_stage1()
        # Experiment options
        positions_omitted_doc = (
            "If omitted: effective arena dimensions must "
            "be given as part of ``--scenario``."
        )

        self.stage1.add_argument(
            "--robot-positions",
            help="""
                 A list of space-separated "X,Y,Z" tuples (no quotes) passed on
                 the command line as valid starting positions for the robots
                 within the world.
                 """
            + self.stage_usage_doc([1], positions_omitted_doc),
            nargs="+",
            default=[],
        )

        # Physics engines options
        self.stage1.add_argument(
            "--physics-engine-type",
            choices=["ode", "bullet", "dart", "simbody"],
            help="""
                 The type of 3D physics engine to use for managing spatial
                 extents within the arena, choosing one of the types that
                 :term:`Gazebo` supports.  A single engine instance is used to
                 manage all physics in the arena.
                 """
            + self.stage_usage_doc([1]),
            default="ode",
        )

        self.stage1.add_argument(
            "--physics-iter-per-tick",
            type=int,
            help="""
                 The # of iterations all physics engines should perform per tick
                 each time the controller loops are run (the # of ticks per
                 second for controller control loops is set via
                 ``--exp-setup``).
                 """
            + self.stage_usage_doc([1]),
            default=config.GAZEBO["physics_iter_per_tick"],
        )

        self.stage1.add_argument(
            "--physics-n-threads",
            type=int,
            help="""
                 Gazebo can group non-interacting entities into computational
                 "islands" and do the physics updates for those islands in
                 parallel each timestep (islands) are recomputed after each
                 timestep).  Gazebo can also parallelize the computation of
                 velocity/position updates with the computation of resolving
                 collisions (i.e., the timestep impulse results in one entity
                 "inside" another).  You can assign multiple threads to a pool
                 for cumulative use for these two parallelization methods
                 (threads will be allocated evenly between them).  The point at
                 which adding more threads will start to DECREASE performance
                 depends on the complexity of your world, the number and type of
                 robots in it, etc., so don't just set this parameter to the #
                 of cores for your machine as a default.

                 From the Gazebo Parallel Physics Report, setting the pool size
                 to the # robots/# joint trees in your simulation usually gives
                 good results, as long as you have more cores available than you
                 allocate to this pool (Gazebo has other threads too).

                 This only applies if ``--physics-engine-type``\\=ode.

                 A value of 0=no threads.
                 """
            + self.stage_usage_doc([1]),
            default=0,
        )

        self.stage1.add_argument(
            "--physics-ec-threadpool",
            type=int,
            help="""
                 Gazebo can parallelize the computation of velocity/position
                 updates with the computation of resolving collisions (i.e., the
                 timestep impulse results in one entity "inside" another).  You
                 can assign multiple threads to a pool for cumulative use for
                 this purpose.  The point at which adding more threads will
                 start to DECREASE performance depends on the complexity of your
                 world, the number and type of robots in it, etc., so don't just
                 set this parameter to the # of cores for your machine as a
                 default.

                 From the Gazebo Parallel Physics Report, setting the pool size
                 to the # robots/#joint trees in your simulation usually gives
                 good results, as long as you have more cores than than you
                 allocate to physics (Gazebo has other threads too).

                 This only applies if ``--physics-engine-type``\\=ode.

                 A value of 0=no threads.
                 """
            + self.stage_usage_doc([1]),
            default=0,
        )


def build(parents: list[argparse.ArgumentParser], stages: list[int]) -> PluginCmdline:
    """
    Get a cmdline parser supporting the :term:`ROS1+Gazebo` engine.

    Contains:

        - :class:`~sierra.core.ros1.cmdline.ROSCmdline` (ROS1 common)

        - :class:`~sierra.plugins.engine.ros1gazebo.cmdline.EngineCmdline`
          (ROS1+Gazebo)
    """
    return EngineCmdline(parents=parents, stages=stages)


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    """Update cmdopts with ROS1+Gazebo-specific cmdline options."""
    opts = ros1.cmdline.to_cmdopts(args)

    for_self = {
        # stage 1
        "robot_positions": args.robot_positions,
        "physics_n_engines": 1,  # Always 1 for gazebo...
        "physics_n_threads": args.physics_n_threads,
        "physics_engine_type": args.physics_engine_type,
        "physics_iter_per_tick": args.physics_iter_per_tick,
    }

    opts |= for_self
    return opts


def sphinx_cmdline_stage1():
    return EngineCmdline([], [1]).parser


__all__ = ["EngineCmdline"]
