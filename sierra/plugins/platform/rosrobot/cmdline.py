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
Command line parsing and validation for the :term:`ROS+robot` platform.
"""

# Core packages
import typing as tp
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, config, ros
import sierra.core.cmdline as cmd


class PlatformCmdline(cmd.BaseCmdline):
    """
    Defines :term:`ROS` extensions to the core command line arguments defined
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
        pass

    @staticmethod
    def cmdopts_update(cli_args, cmdopts: types.Cmdopts) -> None:
        """
        Updates the core cmdopts dictionary with (key,value) pairs from the
        ROS+robot-specific cmdline options.

        """
        ros.cmdline.ROSCmdline.cmdopts_update(cli_args, cmdopts)
        updates = {
            # Multistage
            'exec_jobs_per_node': 1,  # (1 job/robot)

            # stage 2
            'exec_resume': False  # For now...
        }

        cmdopts.update(updates)


class CmdlineValidator(cmd.CoreCmdlineValidator):
    pass


def sphinx_cmdline_stage1():
    parent = ros.cmdline.ROSCmdline([1]).parser
    return PlatformCmdline([parent], [1]).parser


def sphinx_cmdline_stage2():
    parent = ros.cmdline.ROSCmdline([2]).parser
    return PlatformCmdline([parent], [2]).parser
