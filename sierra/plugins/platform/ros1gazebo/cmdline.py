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
Command line parsing and validation for the :term:`ROS1+Gazebo` platform.
"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core import config
import sierra.core.cmdline as corecmd
from sierra.core import hpc, ros1


class PlatformCmdline(corecmd.BaseCmdline):
    """Defines :term:`ROS1+Gazebo` extensions to :class:`~sierra.core.cmdline.CoreCmdline`.

    """

    def __init__(self,
                 parents: tp.Optional[tp.List[argparse.ArgumentParser]],
                 stages: tp.List[int]) -> None:

        if parents is not None:
            self.parser = argparse.ArgumentParser(parents=parents,
                                                  add_help=False,
                                                  allow_abbrev=False)
        else:
            self.parser = argparse.ArgumentParser(add_help=False,
                                                  allow_abbrev=False)

        self.scaffold_cli()
        self.init_cli(stages)

    def scaffold_cli(self) -> None:
        self.stage1_exp = self.parser.add_argument_group('Stage1: Experiment setup')
        self.stage1_physics = self.parser.add_argument_group(
            'Stage1: Configuring Gazebo physics engines')

    def init_cli(self, stages: tp.List[int]) -> None:
        if 1 in stages:
            self.init_stage1()

    def init_stage1(self) -> None:
        # Experiment options
        positions_omitted_doc = ("If omitted: effective arena dimensions must "
                                 "be given as part of ``--scenario``.")

        self.stage1_exp.add_argument("--robot-positions",

                                     help="""

                                     A list of space-separated "X,Y,Z" tuples
                                     (no quotes) passed on the command line as
                                     valid starting positions for the robots
                                     within the world.

                                     """ + self.stage_usage_doc([1],
                                                                positions_omitted_doc),
                                     nargs='+',
                                     default=[])

        # Physics engines options
        self.stage1_physics.add_argument("--physics-engine-type",
                                         choices=['ode', 'bullet',
                                                  'dart', 'simbody'],
                                         help="""

                                         The type of 3D physics engine to use
                                         for managing spatial extents within the
                                         arena, choosing one of the types that
                                         :term:`Gazebo` supports. A single
                                         engine instance is used to manage all
                                         physics in the arena.

                                         """ + self.stage_usage_doc([1]),
                                         default='ode')

        self.stage1_physics.add_argument("--physics-iter-per-tick",
                                         type=int,
                                         help="""

                                         The # of iterations all physics engines
                                         should perform per tick each time the
                                         controller loops are run (the # of
                                         ticks per second for controller control
                                         loops is set via ``--exp-setup``).

                             """ + self.stage_usage_doc([1]),
                                         default=config.kGazebo['physics_iter_per_tick'])

        self.stage1_physics.add_argument("--physics-n-threads",
                                         type=int,
                                         help="""

                                         Gazebo can group non-interacting
                                         entities into computational "islands"
                                         and do the physics updates for those
                                         islands in parallel each timestep
                                         (islands) are recomputed after each
                                         timestep). Gazebo can also parallelize
                                         the computation of velocity/position
                                         updates with the computation of
                                         resolving collisions (i.e., the
                                         timestep impulse results in one entity
                                         "inside" another). You can assign
                                         multiple threads to a pool for
                                         cumulative use for these two
                                         parallelization methods (threads will
                                         be allocated evenly between them). The
                                         point at which adding more threads will
                                         start to DECREASE performance depends
                                         on the complexity of your world, the
                                         number and type of robots in it, etc.,
                                         so don't just set this parameter to the
                                         # of cores for your machine as a
                                         default.

                                         From the Gazebo Parallel Physics
                                         Report, setting the pool size to the #
                                         robots/# joint trees in your simulation
                                         usually gives good results, as long as
                                         you have more cores available than you
                                         allocate to this pool (Gazebo has other
                                         threads too).

                                         This only applies if
                                         ``--physics-engine-type``\\=ode.

                                         A value of 0=no threads.

                                         """ + self.stage_usage_doc([1]),
                                         default=0)

        self.stage1_physics.add_argument("--physics-ec-threadpool",
                                         type=int,
                                         help="""

                                         Gazebo can parallelize the computation
                                         of velocity/position updates with the
                                         computation of resolving collisions
                                         (i.e., the timestep impulse results in
                                         one entity "inside" another). You can
                                         assign multiple threads to a pool for
                                         cumulative use for this purpose. The
                                         point at which adding more threads will
                                         start to DECREASE performance depends
                                         on the complexity of your world, the
                                         number and type of robots in it, etc.,
                                         so don't just set this parameter to the
                                         # of cores for your machine as a
                                         default.

                                         From the Gazebo Parallel Physics
                                         Report, setting the pool size to the #
                                         robots/#joint trees in your simulation
                                         usually gives good results, as long as
                                         you have more cores than than you
                                         allocate to physics (Gazebo has other
                                         threads too).

                                         This only applies if ``--physics-engine-type``\\=ode.

                                         A value of 0=no threads.

                                         """ + self.stage_usage_doc([1]),
                                         default=0)

    @staticmethod
    def cmdopts_update(cli_args: argparse.Namespace,
                       cmdopts: types.Cmdopts) -> None:
        """Update cmdopts with ROS1+Gazebo-specific cmdline options.

        """
        hpc.cmdline.HPCCmdline.cmdopts_update(cli_args, cmdopts)
        ros1.cmdline.ROSCmdline.cmdopts_update(cli_args, cmdopts)

        updates = {
            # stage 1
            'robot_positions': cli_args.robot_positions,

            'physics_n_engines': 1,  # Always 1 for gazebo...
            'physics_n_threads': cli_args.physics_n_threads,
            'physics_engine_type': cli_args.physics_engine_type,
            'physics_iter_per_tick': cli_args.physics_iter_per_tick,
        }

        cmdopts.update(updates)


class CmdlineValidator(corecmd.CoreCmdlineValidator):
    """
    Stub implementation.
    """


def sphinx_cmdline_stage1():
    parent1 = hpc.cmdline.HPCCmdline([1]).parser
    parent2 = ros1.cmdline.ROSCmdline([1]).parser
    return PlatformCmdline([parent1, parent2], [1]).parser


def sphinx_cmdline_stage2():
    parent1 = hpc.cmdline.HPCCmdline([2]).parser
    parent2 = ros1.cmdline.ROSCmdline([2]).parser
    return PlatformCmdline([parent1, parent2], [2]).parser
