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
"""
HPC plugin for running SIERRA locally (not necessarily HPC, but it fits well
enough under that semantic umbrella).

"""

# Core packages
import typing as tp
import argparse

# 3rd party packages
import implements

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    """
    Configure SIERRA for local HPC.
    """

    def __init__(self, exec_env: str) -> None:
        pass

    def __call__(self, args: argparse.Namespace) -> None:
        pass


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.ExpExecOpts) -> tp.List[types.ShellCmdSpec]:
        resume = ''

        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts['exec_resume']:
            resume = '--resume-failed'

        cmd = 'parallel ' \
            '--eta '\
            '--ungroup '\
            '--jobs {2} ' \
            '--results {0} '\
            '--joblog {3} '\
            '--no-notice < "{4}"'

        cmd = cmd.format(exec_opts['jobroot_path'],
                         resume,
                         exec_opts['n_jobs'],
                         exec_opts['joblog_path'],
                         exec_opts['cmdfile_path'])

        return [{'cmd': cmd, 'check': True, 'shell': True}]


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 n_robots: int,
                 exp_num: int) -> None:
        pass

    def pre_run_cmds(self,
                     input_fpath: str,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_run_cmds(self,
                      input_fpath: str,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_run_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []


class ExpRunConfigurer():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        pass

    def __call__(self, run_output_dir: str) -> None:
        pass


class ExecEnvChecker():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        pass

    def __call__(self) -> None:
        pass


__api__ = [
    'ParsedCmdlineConfigurer',
    'ExpRunShellCmdsGenerator',
    'ExpShellCmdsGenerator',
    'ExpRunConfigurer',
    'ExecEnvChecker'
]
