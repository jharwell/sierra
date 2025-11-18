# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
Command line definitions for the :term:`ARGoS` :term:`Engine`.
"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, config
from sierra.plugins import PluginCmdline


class EngineCmdline(PluginCmdline):
    """Defines :term:`ARGoS` cmdline."""

    def __init__(
        self,
        parents: list[argparse.ArgumentParser],
        stages: list[int],
    ) -> None:
        super().__init__(parents, stages)

    def init_stage1(self) -> None:
        # Experiment options

        self.stage1.add_argument(
            "--exp-setup",
            help="""
                 Defines experiment run length, :term:`Ticks <Tick>` per second
                 for the experiment (<experiment> tag).  See
                 :ref:`usage/vars/expsetup` for a full description.
                 """
            + self.stage_usage_doc([1]),
            default="exp_setup.T{}.K{}".format(
                config.ARGOS["n_secs_per_run"],
                config.ARGOS["n_ticks_per_sec"],
            ),
        )

        # Physics engines options

        self.stage1.add_argument(
            "--physics-engine-type2D",
            choices=["dynamics2d"],
            help="""

                                         The type of 2D physics engine to use
                                         for managing spatial extents within the
                                         arena, choosing one of the types that
                                         ARGoS supports. The precise 2D areas
                                         (if any) within the arena which will be
                                         controlled by 2D physics engines is
                                         defined on a per ``--project`` basis.

                             """
            + self.stage_usage_doc([1]),
            default="dynamics2d",
        )

        self.stage1.add_argument(
            "--physics-engine-type3D",
            choices=["dynamics3d"],
            help="""

                                         The type of 3D physics engine to use
                                         for managing 3D volumetric extents
                                         within the arena, choosing one of the
                                         types that ARGoS supports. The precise
                                         3D volumes (if any) within the arena
                                         which will be controlled by 3D physics
                                         engines is defined on a per
                                         ``--project`` basis.

                                         """
            + self.stage_usage_doc([1]),
            default="dynamics3d",
        )

        self.stage1.add_argument(
            "--physics-n-engines",
            choices=[1, 2, 4, 6, 8, 12, 16, 24],
            type=int,
            help="""

                                         # of physics engines to use during
                                         simulation (yay ARGoS!). If N > 1, the
                                         engines will be tiled in a uniform grid
                                         within the arena (X and Y spacing may
                                         not be the same depending on dimensions
                                         and how many engines are chosen,
                                         however), extending upward in Z to the
                                         height specified by ``--scenario``
                                         (i.e., forming a set of "silos" rather
                                         that equal volumetric extents).

                                         If 2D and 3D physics engines are mixed,
                                         then half of the specified # of engines
                                         will be allocated among all arena
                                         extents cumulatively managed by each
                                         type of engine. For example, if 4
                                         engines are used, with 1/3 of the arena
                                         managed by 2D engines and 2/3 by 3D,
                                         then 2 2D engines will manage 1/3 of
                                         the arena, and 2 3D engines will manage
                                         the other 2/3 of the arena.

                                         If ``--execenv`` is something other
                                         than ``hpc.local`` then the # physics
                                         engines will be computed from the HPC
                                         environment, and the cmdline value (if
                                         any) will be ignored.

                                         .. IMPORTANT:: When using multiple
                                            physics engines, always make sure
                                            that ``# engines / arena dimension``
                                            (X **AND** Y dimensions) is always a
                                            rational number. That is,

                                            - 24 engines in a ``12x12`` arena
                                              will be fine, because
                                              ``12/24=0.5``, which can be
                                              represented reasonably well in
                                              floating point.

                                            - 24 engines in a ``16x16`` arena
                                              will not be fine, because
                                              ``16/24=0.666667``, which will
                                              very likely result in rounding
                                              errors and ARGoS being unable to
                                              initialize the space because it
                                              can't place arena walls.

                                            This is enforced by SIERRA.

                             """
            + self.stage_usage_doc([1]),
        )
        self.stage1.add_argument(
            "--physics-iter-per-tick",
            type=int,
            help="""

                                         The # of iterations all physics engines
                                         should perform per :term:`Tick` each
                                         time the controller loops are run (the
                                         # of ticks per second for controller
                                         control loops is set via
                                         ``--exp-setup``).

                             """
            + self.stage_usage_doc([1]),
            default=config.ARGOS["physics_iter_per_tick"],
        )

        self.stage1.add_argument(
            "--physics-spatial-hash2D",
            help="""

                                         Specify that each 2D physics engine
                                         should use a spatial hash (only applies
                                         to ``dynamics2d`` engine type).

                                         """,
            action="store_true",
        )

        # Rendering options
        self.stage1.add_argument(
            "--camera-config",
            choices=["overhead", "sw", "sw+interp"],
            help="""

                                           Select the camera configuration for
                                           simulation. Ignored unless
                                           ``--engine-vc`` is passed. Valid
                                           values are:

                                           - ``overhead`` - Use a single
                                             overhead camera at the center of
                                             the aren looking straight down at
                                             an appropriate height to see the
                                             whole arena.

                                           - ``sw`` - Use the ARGoS camera
                                             configuration (12 cameras), cycling
                                             through them periodically
                                             throughout simulation without
                                             interpolation.

                                           - ``sw+interp`` - Same as ``sw``, but
                                             with interpolation between cameras.

                                           """
            + self.stage_usage_doc([1]),
            default="overhead",
        )

        self.stage1.add_argument(
            "--with-robot-rab",
            help="""

                                        If passed, do not remove the Range and
                                        Bearing (RAB) sensor, actuator, and
                                        medium XML definitions from
                                        ``--expdef-template`` before
                                        generating experimental
                                        inputs. Otherwise, the following XML
                                        tags are removed if they exist:

                                        - ``.//media/range_and_bearing``
                                        - ``.//actuators/range_and_bearing``
                                        - ``.//sensors/range_and_bearing``

                                        """
            + self.stage_usage_doc([1]),
            action="store_true",
            default=False,
        )

        self.stage1.add_argument(
            "--with-robot-leds",
            help="""

                                        If passed, do not remove the robot LED
                                        actuator XML definitions from the
                                        ``--expdef-template`` before
                                        generating experimental
                                        inputs. Otherwise, the following XML
                                        tags are removed if they exist:

                                        - ``.//actuators/leds``
                                        - ``.//medium/leds``
                                        - ``.//sensors/colored_blob_omnidirectional_camera``

                                        """
            + self.stage_usage_doc([1]),
            action="store_true",
            default=False,
        )

        self.stage1.add_argument(
            "--with-robot-battery",
            help="""

                                        If passed, do not remove the robot
                                        battery sensor XML definitions from
                                        ``--expdef-template`` before
                                        generating experimental
                                        inputs. Otherwise, the following XML
                                        tags are removed if they exist:

                                        - ``.//entity/*/battery``
                                        - ``.//sensors/battery``

                                        """
            + self.stage_usage_doc([1]),
            action="store_true",
            default=False,
        )

        self.stage1.add_argument(
            "--n-agents",
            help="""
                                             The # agents (robots) that should
                                             be used in the simulation.  Can be
                                             used to override batch criteria, or
                                             to supplement experiments that do
                                             not set it so that manual
                                             modification of input file is
                                             unneccesary.
                                             """
            + self.stage_usage_doc([1]),
            type=int,
            default=None,
        )


def build(parents: list[argparse.ArgumentParser], stages: list[int]) -> PluginCmdline:
    """
    Get a cmdline parser supporting the :term:`ARGoS` engine.
    """
    return EngineCmdline(parents=parents, stages=stages)


def to_cmdopts(args: argparse.Namespace) -> types.Cmdopts:
    """Update cmdopts with ARGoS-specific cmdline options."""
    return {
        # Stage 1
        "n_agents": args.n_agents,
        "exp_setup": args.exp_setup,
        "physics_n_engines": args.physics_n_engines,
        "physics_n_threads": args.physics_n_engines,  # alias
        "physics_engine_type2D": args.physics_engine_type2D,
        "physics_engine_type3D": args.physics_engine_type3D,
        "physics_iter_per_tick": args.physics_iter_per_tick,
        "physics_spatial_hash2D": args.physics_spatial_hash2D,
        "with_robot_rab": args.with_robot_rab,
        "with_robot_leds": args.with_robot_leds,
        "with_robot_battery": args.with_robot_battery,
        "camera_config": args.camera_config,
    }


def sphinx_cmdline_stage1():
    return EngineCmdline([], [1]).parser


def sphinx_cmdline_stage2():
    return EngineCmdline([], [2]).parser
