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
Command line parsing and validation for the :term:`ROS1+robot` platform.
"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, ros1, config
import sierra.core.cmdline as cmd


class PlatformCmdline(cmd.BaseCmdline):
    """Defines :term:`ROS1` extensions to :class:`~sierra.core.cmdline.CoreCmdline`.

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
        self.multistage = self.parser.add_argument_group('Multi-stage options',
                                                         'Options which are used in multiple pipeline stages')
        self.stage1 = self.parser.add_argument_group('Stage1: Experiment generation')
        self.stage2 = self.parser.add_argument_group('Stage2: Experiment execution'
                                                     'For running real robot experiments')

    def init_cli(self, stages: tp.List[int]) -> None:
        if -1 in stages:
            self.init_multistage()

        if 1 in stages:
            self.init_stage1()

        if 2 in stages:
            self.init_stage2()

    def init_multistage(self) -> None:
        self.multistage.add_argument("--skip-online-check",
                                     help="""

                                     If passed, then the usual 'is this robot
                                     online' checks will be skipped.

                                     """ + self.stage_usage_doc([1, 2]),
                                     action='store_true')

        self.multistage.add_argument("--online-check-method",
                                     choices=['ping+ssh', 'nc+ssh'],
                                     help="""

                                     How SIERRA should check if a given robot is
                                     online. Valid values:

                                     - ``ping+ssh`` - First, verify that you can
                                       ping each the hostname/IP associated with
                                       each robot. Second, verify that
                                       passwordless ssh to the hostname/IP
                                       works. This is the most common option.

                                     - ``nc+ssh`` - First, verify that an ssh
                                       connection exists from the SIERRA host
                                       machine to the robot on the specified
                                       port using netcat. Second, verify that
                                       passwordless ssh to the robot on the
                                       specified port works. This is useful when
                                       connecting to the robots through a
                                       reverse SSH tunnel, which can be
                                       necessary if the robots don't have a
                                       fixed IP address and cannot be addressed
                                       by FQDN (looking at you eduroam...).

                                     """,
                                     default='ping+ssh')

    def init_stage1(self) -> None:
        self.stage1.add_argument("--skip-sync",
                                 help="""

                                 If passed, then the generated experiment will not
                                 be synced to robots. This is useful when:

                                 - You are developing your :term:`Project` and
                                   just want to check locally if the experiment
                                   is being generated properly.

                                 - You have a lot of robots and/or the network
                                   connection from the SIERRA host machine to
                                   the robots is slow, and copying the
                                   experiment multiple times as you tweak
                                   parameters takes a long time.

                                 """ + self.stage_usage_doc([1]),
                                 action='store_true')

    def init_stage2(self) -> None:
        self.stage2.add_argument("--exec-inter-run-pause",
                                 metavar="SECONDS",
                                 help="""

                                 How long to pause between :term:`Experimental
                                 Runs <Experimental Run>`, giving you time to
                                 reset the environment, move robots, etc.

                                 """ + self.stage_usage_doc([2]),
                                 type=int,
                                 default=config.kROS['inter_run_pause'])

        self.stage2.add_argument("--exec-resume",
                                 help="""

                                 Resume a batch experiment that was
                                 killed/stopped/etc last time SIERRA was
                                 run.

                                 """ + self.stage_usage_doc([2]),
                                 action='store_true',
                                 default=False)

    @staticmethod
    def cmdopts_update(cli_args, cmdopts: types.Cmdopts) -> None:
        """Update cmdopts with ROS1+robot-specific cmdline options.

        """
        ros1.cmdline.ROSCmdline.cmdopts_update(cli_args, cmdopts)
        updates = {
            # Multistage
            'exec_jobs_per_node': 1,  # (1 job/robot)
            'skip_online_check': cli_args.skip_online_check,
            'online_check_method': cli_args.online_check_method,

            # stage 1
            'skip_sync': cli_args.skip_sync,

            # stage 2
            'exec_resume': cli_args.exec_resume,
            'exec_inter_run_pause': cli_args.exec_inter_run_pause
        }

        cmdopts.update(updates)


class CmdlineValidator(ros1.cmdline.ROSCmdlineValidator):
    """
    Stub implementation.
    """


def sphinx_cmdline_stage1():
    parent = ros1.cmdline.ROSCmdline([1]).parser
    return PlatformCmdline([parent], [1]).parser


def sphinx_cmdline_stage2():
    parent = ros1.cmdline.ROSCmdline([2]).parser
    return PlatformCmdline([parent], [2]).parser
