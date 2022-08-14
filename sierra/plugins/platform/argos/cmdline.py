# Copyright 2021 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#
"""
Command line parsing and validation for the :term:`ARGoS`.
"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, config, hpc
import sierra.core.cmdline as cmd


class PlatformCmdline(cmd.BaseCmdline):
    """Defines :term:`ARGoS` extensions to :class:`~sierra.core.cmdline.CoreCmdline`.

    """

    def __init__(self,
                 parents: tp.Optional[tp.List[argparse.ArgumentParser]],
                 stages: tp.List[int]) -> None:

        if parents is not None:
            self.parser = argparse.ArgumentParser(add_help=False,
                                                  parents=parents,
                                                  allow_abbrev=False)
        else:
            self.parser = argparse.ArgumentParser(add_help=False,
                                                  allow_abbrev=False)

        self.scaffold_cli()
        self.init_cli(stages)

    def scaffold_cli(self) -> None:
        self.stage1_exp = self.parser.add_argument_group(
            'Stage1: Experiment generation')
        self.stage1_physics = self.parser.add_argument_group(
            'Stage1: Configuring ARGoS physics engines')
        self.stage1_rendering = self.parser.add_argument_group(
            'Stage1: Rendering (see also stage4 rendering options)')
        self.stage1_robots = self.parser.add_argument_group(
            'Stage1: Configuring robots')

    def init_cli(self, stages: tp.List[int]) -> None:
        if 1 in stages:
            self.init_stage1()

    def init_stage1(self) -> None:
        # Experiment options

        self.stage1_exp.add_argument("--exp-setup",
                                     help="""

                                     Defines experiment run length, :term:`Ticks
                                     <Tick>` per second for the experiment
                                     (<experiment> tag), # of datapoints to
                                     capture/capture interval for each
                                     simulation. See :ref:`ln-sierra-vars-expsetup` for
                                     a full description.

                                     """ + self.stage_usage_doc([1]),
                                     default="exp_setup.T{0}.K{1}.N{2}".format(
                                         config.kARGoS['n_secs_per_run'],
                                         config.kARGoS['n_ticks_per_sec'],
                                         config.kExperimentalRunData['n_datapoints_1D']))

        # Physics engines options

        self.stage1_physics.add_argument("--physics-engine-type2D",
                                         choices=['dynamics2d'],
                                         help="""

                                         The type of 2D physics engine to use
                                         for managing spatial extents within the
                                         arena, choosing one of the types that
                                         ARGoS supports. The precise 2D areas
                                         (if any) within the arena which will be
                                         controlled by 2D physics engines is
                                         defined on a per ``--project`` basis.

                             """ + self.stage_usage_doc([1]),
                                         default='dynamics2d')

        self.stage1_physics.add_argument("--physics-engine-type3D",
                                         choices=['dynamics3d'],
                                         help="""

                                         The type of 3D physics engine to use
                                         for managing 3D volumetric extents
                                         within the arena, choosing one of the
                                         types that ARGoS supports. The precise
                                         3D volumes (if any) within the arena
                                         which will be controlled by 3D physics
                                         engines is defined on a per
                                         ``--project`` basis.

                                         """ + self.stage_usage_doc([1]),
                                         default='dynamics3d')

        self.stage1_physics.add_argument("--physics-n-engines",
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

                                         If ``--exec-env`` is something other
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

                             """ + self.stage_usage_doc([1]))
        self.stage1_physics.add_argument("--physics-iter-per-tick",
                                         type=int,
                                         help="""

                                         The # of iterations all physics engines
                                         should perform per :term:`Tick` each
                                         time the controller loops are run (the
                                         # of ticks per second for controller
                                         control loops is set via
                                         ``--exp-setup``).

                             """ + self.stage_usage_doc([1]),
                                         default=config.kARGoS['physics_iter_per_tick'])

        self.stage1_physics.add_argument("--physics-spatial-hash2D",
                                         help="""

                                         Specify that each 2D physics engine
                                         should use a spatial hash (only applies
                                         to ``dynamics2d`` engine type).

                                         """,
                                         action='store_true')

        # Rendering options
        self.stage1_rendering.add_argument("--camera-config",
                                           choices=['overhead',
                                                    'sw',
                                                    'sw+interp'],
                                           help="""

                                           Select the camera configuration for
                                           simulation. Ignored unless
                                           ``--platform-vc`` is passed. Valid
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

                                           """ + self.stage_usage_doc([1]),
                                           default='overhead')

        self.stage1_robots.add_argument("--with-robot-rab",
                                        help="""

                                        If passed, do not remove the Range and
                                        Bearing (RAB) sensor, actuator, and
                                        medium XML definitions from
                                        ``--template-input-file`` before
                                        generating experimental
                                        inputs. Otherwise, the following XML
                                        tags are removed if they exist:

                                        - ``.//media/range_and_bearing``
                                        - ``.//actuators/range_and_bearing``
                                        - ``.//sensors/range_and_bearing``

                                        """ + self.stage_usage_doc([1]),
                                        action="store_true",
                                        default=False)

        self.stage1_robots.add_argument("--with-robot-leds",
                                        help="""

                                        If passed, do not remove the robot LED
                                        actuator XML definitions from the
                                        ``--template-input-file`` before
                                        generating experimental
                                        inputs. Otherwise, the following XML
                                        tags are removed if they exist:

                                        - ``.//actuators/leds``
                                        - ``.//medium/leds``
                                        - ``.//sensors/colored_blob_omnidirectional_camera``

                                        """ + self.stage_usage_doc([1]),
                                        action="store_true",
                                        default=False)

        self.stage1_robots.add_argument("--with-robot-battery",
                                        help="""

                                        If passed, do not remove the robot
                                        battery sensor XML definitions from
                                        ``--template-input-file`` before
                                        generating experimental
                                        inputs. Otherwise, the following XML
                                        tags are removed if they exist:

                                        - ``.//entity/*/battery``
                                        - ``.//sensors/battery``

                                        """ + self.stage_usage_doc([1]),
                                        action="store_true",
                                        default=False)

        self.stage1_robots.add_argument("--n-robots",
                                        help="""

                                        The # robots that should be used in the
                                        simulation. Can be used to override
                                        batch criteria, or to supplement
                                        experiments that do not set it so that
                                        manual modification of input file is
                                        unneccesary.

                                        """ + self.stage_usage_doc([1]),
                                        type=int,
                                        default=None)

    @staticmethod
    def cmdopts_update(cli_args, cmdopts: types.Cmdopts) -> None:
        """Update cmdopts with ARGoS-specific cmdline options.

        """
        hpc.cmdline.HPCCmdline.cmdopts_update(cli_args, cmdopts)

        updates = {
            # Stage 1
            'n_robots': cli_args.n_robots,

            'exp_setup': cli_args.exp_setup,

            'physics_n_engines': cli_args.physics_n_engines,
            'physics_n_threads': cli_args.physics_n_engines,  # alias
            "physics_engine_type2D": cli_args.physics_engine_type2D,
            "physics_engine_type3D": cli_args.physics_engine_type3D,
            "physics_iter_per_tick": cli_args.physics_iter_per_tick,
            "physics_spatial_hash2D": cli_args.physics_spatial_hash2D,

            "with_robot_rab": cli_args.with_robot_rab,
            "with_robot_leds": cli_args.with_robot_leds,
            "with_robot_battery": cli_args.with_robot_battery,

            'camera_config': cli_args.camera_config,

        }

        cmdopts.update(updates)


class CmdlineValidator(cmd.CoreCmdlineValidator):
    pass


def sphinx_cmdline_stage1():
    return PlatformCmdline(None, [1]).parser


def sphinx_cmdline_stage2():
    parent = hpc.cmdline.HPCCmdline([2]).parser
    return PlatformCmdline([parent], [2]).parser
