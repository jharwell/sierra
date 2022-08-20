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
"""Common cmdline classes :term:`Platforms <Platform>` using :term:`ROS1`.

"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, config
import sierra.core.cmdline as cmd


class ROSCmdline(cmd.BaseCmdline):
    """Defines :term:`ROS1` common command line arguments.

    """

    def __init__(self,
                 stages: tp.List[int]) -> None:
        self.parser = argparse.ArgumentParser(add_help=False,
                                              allow_abbrev=False)
        self.scaffold_cli()
        self.init_cli(stages)

    def scaffold_cli(self) -> None:
        self.multistage = self.parser.add_argument_group('Multi-stage options',
                                                         'Options which are used in multiple pipeline stages')
        self.stage1_exp = self.parser.add_argument_group(
            'Stage1: Experiment generation')

    def init_cli(self, stages: tp.List[int]) -> None:
        if -1 in stages:
            self.init_multistage()

        if 1 in stages:
            self.init_stage1()

    def init_multistage(self) -> None:
        self.multistage.add_argument("--no-master-node",
                                     help="""

                                     Do not generate commands for/start a ROS1
                                     master node on the SIERRA host
                                     machine (which is the ROS1 master).

                                     This is useful when:

                                     - Using the :term:`ROS1+Robot` platform and
                                       each robot outputs their own metrics to a
                                       shared filesystem.

                                     - The SIERRA host machine does not have ROS1
                                       installed, and you are doing
                                       testing/bringup of robots.

                                     """ + self.stage_usage_doc([1, 2]),
                                     action='store_true')

    def init_stage1(self) -> None:
        # Experiment options

        self.stage1_exp.add_argument("--exp-setup",
                                     help="""

                                     Defines experiment run length, ticks per
                                     second for the experiment, # of datapoints
                                     to capture/capture interval for each
                                     simulation. See :ref:`ln-sierra-vars-expsetup` for
                                     a full description.

                            """ + self.stage_usage_doc([1]),
                                     default="exp_setup.T{0}.K{1}.N{2}".format(
                                         config.kROS['n_secs_per_run'],
                                         config.kROS['n_ticks_per_sec'],
                                         config.kExperimentalRunData['n_datapoints_1D']))

        self.stage1_exp.add_argument("--robot",
                                     help="""

                                     The key name of the robot model, which must
                                     be present in the appropriate section of
                                     ``{0}`` for the :term:`Project`. See
                                     :ref:`ln-sierra-tutorials-project-main-config`
                                     for details.

                            """.format(config.kYAML.main) + self.stage_usage_doc([1]))

    @staticmethod
    def cmdopts_update(cli_args, cmdopts: types.Cmdopts) -> None:
        """Update cmdopts with ROS-specific cmdline options.
        """
        updates = {
            # multistagev
            'no_master_node': cli_args.no_master_node,

            # stage 1
            'robot': cli_args.robot,
            'exp_setup': cli_args.exp_setup,

        }

        cmdopts.update(updates)


class ROSCmdlineValidator():
    """
    Perform checks on parsed ROS cmdline arguments.
    """

    def __call__(self, args: argparse.Namespace) -> None:
        assert args.robot is not None,\
            "You must specify the --robot to use"


__api__ = [
    'ROSCmdline',
    'ROSCmdlineValidator'
]
