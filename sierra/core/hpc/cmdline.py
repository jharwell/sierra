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
"""Common cmdline classes for the various HPC plugins.

"""

# Core packages
import argparse
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types, cmdline


class HPCCmdline(cmdline.BaseCmdline):
    def __init__(self, stages: tp.List[int]) -> None:
        self.parser = argparse.ArgumentParser(add_help=False,
                                              allow_abbrev=False)

        self.scaffold_cli()
        self.init_cli(stages)

    def scaffold_cli(self) -> None:
        desc = ("For platforms which are simulators (and can "
                "therefore be run in HPC environments).")
        self.hpc = self.parser.add_argument_group('HPC options', desc)

    def init_cli(self, stages: tp.List[int]) -> None:
        if 2 in stages:
            self.init_stage2()

    def init_stage2(self) -> None:
        """Add HPC cmdline options.

        Options may be interpreted differently between :term:`Platforms
        <Platform>`, or ignored, depending. These include:

        - ``--exec-jobs-per-node``

        - ``--exec-no-devnull``

        - ``--exec-resume``

        - ``--exec-strict``

        """
        self.hpc.add_argument("--exec-jobs-per-node",
                              help="""

                              Specify the maximum number of parallel jobs to run
                              per allocated node. By default this is computed
                              from the selected HPC environment for maximum
                              throughput given the desired ``--n-runs`` and CPUs
                              per allocated node. However, for some environments
                              being able to override the computed default can be
                              useful.

                              """ + self.stage_usage_doc([2]),
                              type=int,
                              default=None)

        self.hpc.add_argument("--exec-devnull",
                              help="""

                              Redirect ALL output from simulations to
                              /dev/null. Useful for platform where you can't
                              disable all INFO messages at compile time, and
                              don't want to have to grep through lots of
                              redundant stdout files to see if there were any
                              errors.

                              """ + self.stage_usage_doc([1, 2]),
                              action='store_true',
                              dest='exec_devnull',
                              default=True)

        self.hpc.add_argument("--exec-no-devnull",
                              help="""

                              Don't redirect ALL output from simulations to
                              /dev/null. Useful for platform where you can't
                              disable all INFO messages at compile time, and
                              don't want to have to grep through lots of
                              redundant stdout files to see if there were any
                              errors.

                              """ + self.stage_usage_doc([1, 2]),
                              action='store_false',
                              dest='exec_devnull')

        self.hpc.add_argument("--exec-resume",
                              help="""

                              Resume a batch experiment that was
                              killed/stopped/etc last time SIERRA was run.

                              """ + self.stage_usage_doc([2]),
                              action='store_true',
                              default=False)

        self.hpc.add_argument("--exec-strict",
                              help="""

                              If passed, then if any experimental commands fail
                              during stage 2 SIERRA will exit, rather than try
                              to keep going and execute the rest of the
                              experiments.

                              Useful for:

                              - "Correctness by construction" experiments, where
                                you know if SIERRA doesn't crash and it makes it
                                to the end of your batch experiment then none of
                                the individual experiments crashed.

                              - CI pipelines

                              """,
                              action='store_true')

    @staticmethod
    def cmdopts_update(cli_args: argparse.Namespace,
                       cmdopts: types.Cmdopts) -> None:
        """Update cmdopts dictionary with the HPC-specific cmdline options.

        """
        updates = {
            # Multistage
            'exec_devnull': cli_args.exec_devnull,
            'exec_jobs_per_node': cli_args.exec_jobs_per_node,
            'exec_resume': cli_args.exec_resume,
            'exec_strict': cli_args.exec_strict
        }
        cmdopts.update(updates)


__api__ = [
    'HPCCmdline',
]
