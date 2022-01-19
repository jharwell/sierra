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
"""Common cmdline parsing and validation for :term:`Platforms <Platform>` using
:term:`ROS`.

"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, config
import sierra.core.cmdline as cmd


class ROSCmdline(cmd.BaseCmdline):
    """Defines :term:`ROS` comon command line arguments.

    """

    def __init__(self,
                 stages: tp.List[int]) -> None:
        self.parser = argparse.ArgumentParser(prog='sierra-cli',
                                              add_help=False,
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
                                simulation. See :ref:`ln-vars-ts` for a full
                                description.

                                 """ + self.stage_usage_doc([1]),
                                default="time_setup.T{0}.K{1}.N{2}".format(
                                    config.kROS['n_secs_per_run'],
                                    config.kROS['n_ticks_per_sec'],
                                    config.kExperimentalRunData['n_datapoints_1D']))

        experiment.add_argument("--robot",

                                help="""

                                The key name of the robot model, which must be
                                present in the appropriate section of
                                ``main.yaml`` for the :term:`Project`. See
                                :ref:`ln-tutorials-main-config` for details.

                                """ + self.stage_usage_doc([1]))

    @staticmethod
    def cmdopts_update(cli_args, cmdopts: types.Cmdopts) -> None:
        """
        Updates the core cmdopts dictionary with (key,value) pairs from the
        ROS-specific cmdline options.

        """
        updates = {
            # stage 1
            'robot': cli_args.robot,
            'time_setup': cli_args.time_setup,
        }

        cmdopts.update(updates)


class ROSCmdlineValidator():
    def __call__(self, args: argparse.Namespace) -> None:
        assert args.robot is not None,\
            "You must specify the --robot to use"
