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
from sierra.core import types
from sierra.core import config
import sierra.core.cmdline as cmd
import sierra.core.hpc as hpc


class PlatformCmdline(cmd.BaseCmdline):
    """
    Defines :term:`Gazebo` extensions to the core command line arguments defined
    in :class:`~sierra.core.cmdline.CoreCmdline`.
    """

    def __init__(self,
                 parents: tp.Optional[tp.List[argparse.ArgumentParser]],
                 stages: tp.List[int]) -> None:

        if parents is not None:
            self.parser = argparse.ArgumentParser(prog='sierra-cli',
                                                  parents=parents,
                                                  allow_abbrev=False)
        else:
            self.parser = argparse.ArgumentParser(prog='sierra-cli',
                                                  allow_abbrev=False)

        self.init_cli(stages)

    def init_cli(self, stages: tp.List[int]) -> None:
        if 1 in stages:
            self.init_stage1()

    def init_stage1(self) -> None:
        # Experiment options
        experiment = self.parser.add_argument_group('Stage1: Experiment setup')

        experiment.add_argument("--time-setup",
                                help="""

                                Defines experiment run length, ticks per second
                                for the experiment, # of datapoints to
                                capture/capture interval for each
                                simulation. See
                                :ref:`ln-platform-rosgazebo-vars-ts` for a full
                                description.

                                 """ + self.stage_usage_doc([1]),
                                default="time_setup.T{0}.K{1}.N{2}".format(
                                    config.kGazebo['n_secs_per_run'],
                                    config.kGazebo['n_ticks_per_sec'],
                                    config.kExperimentalRunData['n_datapoints_1D']))

        experiment.add_argument("--robot",

                                help="""

                                The key name of the robot model, which must be
                                present in the appropriate section of
                                ``main.yaml`` for the :term:`Project`. See
                                :ref:`ln-tutorials-main-config` for details.

                                """ + self.stage_usage_doc([1]))

        experiment.add_argument("--robot-positions",

                                help="""

                                A list of space-separated "X,Y,Z" tuples (no
                                quotes) passed on the command line as valid
                                starting positions for the robots within the
                                world.
                                """ + self.stage_usage_doc([1],
                                                           """If omitted:
                                                          effective arena
                                                          dimensions must be
                                                          given as part of the
                                                          ``--scenario``
                                                          parameter."""),
                                nargs='+',
                                default=[])

        # Physics engines options
        physics = self.parser.add_argument_group(
            'Stage1: Configuring Gazebo physics engines')

        physics.add_argument("--physics-engine-type",
                             choices=['ode', 'bullet', 'dart', 'simbody'],
                             help="""

                             The type of 3D physics engine to use for managing
                             spatial extents within the arena, choosing one of
                             the types that :term:`Gazebo` supports. A single
                             engine instance is used to manage all physics in
                             the arena.
                             """ + self.stage_usage_doc([1]),
                             default='ode')

        physics.add_argument("--physics-iter-per-tick",
                             type=int,
                             help="""

                             The # of iterations all physics engines should
                             perform per tick each time the controller loops are
                             run (the # of ticks per second for controller
                             control loops is set via ``--time-setup``).

                             """ + self.stage_usage_doc([1]),
                             default=config.kGazebo['physics_iter_per_tick'])

        physics.add_argument("--physics-n-threads",
                             type=int,
                             help="""

                             Gazebo can group non-interacting entities into
                             computational "islands" and do the physics updates
                             for those islands in parallel each timestep
                             (islands) are recomputed after each
                             timestep). Gazebo can also parallelize the
                             computation of velocity/position updates with the
                             computation of resolving collisions (i.e., the
                             timestep impulse results in one entity "inside"
                             another). You can assign multiple threads to a pool
                             for cumulative use for these two parallelization
                             methods (threads will be allocated evenly between
                             them). The point at which adding more threads will
                             start to DECREASE performance depends on the
                             complexity of your world, the number and type of
                             robots in it, etc., so don't just set this
                             parameter to the # of cores for your machine as a
                             default.

                             From the Gazebo Parallel Physics Report, setting
                             the pool size to the # robots/# joint trees in your
                             simulation usually gives good results, as long as
                             you have more cores available than you allocate to
                             this pool (Gazebo has other threads too).

                             This only applies if ``--physics-engine-type``=ode.

                             A value of 0=no threads.
                             """ + self.stage_usage_doc([1]),
                             default=0)

        physics.add_argument("--physics-ec-threadpool",
                             type=int,
                             help="""

                             Gazebo can parallelize the computation of
                             velocity/position updates with the computation of
                             resolving collisions (i.e., the timestep impulse
                             results in one entity "inside" another). You
                             can assign multiple threads to a pool for
                             cumulative use for this purpose. The point at which
                             adding more threads will start to DECREASE
                             performance depends on the complexity of your
                             world, the number and type of robots in it, etc.,
                             so don't just set this parameter to the # of cores
                             for your machine as a default.

                             From the Gazebo Parallel Physics Report, setting
                             the pool size to the # robots/#joint trees in your
                             simulation usually gives good results, as long as
                             you have more cores than than you allocate to
                             physics (Gazebo has other threads too).

                             This only applies if ``--physics-engine-type``=ode.

                             A value of 0=no threads.
                             """ + self.stage_usage_doc([1]),
                             default=0)

    @staticmethod
    def cmdopts_update(cli_args, cmdopts: types.Cmdopts) -> None:
        """
        Updates the core cmdopts dictionary with (key,value) pairs from the
        ROS/Gazebo-specific cmdline options.

        """
        updates = {
            # Multistage
            'exec_devnull': cli_args.exec_devnull,

            # stage 1
            'robot': cli_args.robot,
            'robot_positions': cli_args.robot_positions,

            'time_setup': cli_args.time_setup,

            'physics_n_engines': 1,  # Always 1 for gazebo...
            'physics_n_threads': cli_args.physics_n_threads,
            'physics_engine_type': cli_args.physics_engine_type,
            'physics_iter_per_tick': cli_args.physics_iter_per_tick,

        }

        cmdopts.update(updates)


class CmdlineValidator(cmd.CoreCmdlineValidator):
    pass


def sphinx_cmdline_stage1():
    return PlatformCmdline(None, [1]).parser


def sphinx_cmdline_stage2():
    parent = hpc.HPCCmdline([2]).parser
    return PlatformCmdline([parent], [2]).parser
