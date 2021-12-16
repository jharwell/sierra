# Copyright 2020 John Harwell, All rights reserved.
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
"""Common cmdline parsing and validation classes for the various HPC plugins
that can be used with SIERRA for running experiments.

"""

# Core packages
import argparse
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types, cmdline


class HPCCmdline(cmdline.BaseCmdline):
    def __init__(self, stages: tp.List[int]) -> None:
        self.parser = argparse.ArgumentParser(prog='sierra-cli',
                                              add_help=False,
                                              allow_abbrev=False)

        self.init_cli(stages)

    def init_cli(self, stages: tp.List[int]) -> None:
        if 2 in stages:
            self.init_stage2()

    def init_stage2(self) -> None:
        desc = ("For platforms which are simulators (and can"
                "therefore be run in HPC environments).")
        hpc = self.parser.add_argument_group('HPC options', desc)

        hpc.add_argument("--exec-jobs-per-node",
                         help="""

                         Specify the maximum number of parallel jobs to run per
                         allocated node. By default this is computed from the
                         selected HPC environment for maximum throughput given
                         the desired ``--n-runs`` and CPUs per allocated
                         node. However, for some environments being able to
                         override the computed default can be useful.

                         """ + self.stage_usage_doc([2]),
                         type=int,
                         default=None)

        hpc.add_argument("--exec-no-devnull",
                         help="""

                         Don't redirect ALL output from simulations to
                         /dev/null. Useful for platform where you can't disable
                         all INFO messages at compile time, and don't want to
                         have to grep through lots of redundant stdout files to
                         see if there were any errors.

                         """ + self.stage_usage_doc([1, 2]),
                         action='store_true',
                         default=False)

        hpc.add_argument("--exec-resume",
                         help="""

                         Resume a batch experiment that was killed/stopped/etc
                         last time SIERRA was run. This maps directly to GNU
                         parallel's ``--resume-failed`` option.

                         """ + self.stage_usage_doc([2]),
                         action='store_true',
                         default=False)

    @staticmethod
    def cmdopts_update(cli_args: argparse.Namespace,
                       cmdopts: types.Cmdopts) -> None:
        """
        Updates the core cmdopts dictionary with (key,value) pairs from the
        HPC-specific cmdline options.

        """
        updates = {
            # Multistage
            'exec_no_devnull': cli_args.exec_no_devnull,
            'exec_jobs_per_node': cli_args.exec_jobs_per_node,
            'exec_resume': cli_args.exec_resume
        }
        cmdopts.update(updates)


__api__ = [
    'HPCCmdline',
]
