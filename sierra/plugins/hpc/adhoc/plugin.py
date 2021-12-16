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
HPC plugin for running SIERRA with an ad-hoc set of allocated compute nodes
(e.g., whatever computers you happen to have laying around in the lab).

"""

# Core packages
import os
import logging  # type: tp.Any
import typing as tp
import argparse

# 3rd party packages
import implements

# Project packages
from sierra.core import types, config
from sierra.core import plugin_manager as pm
from sierra.core.experiment import bindings


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    """
    Configure SIERRA for ad-hoc HPC by reading environment variables and
    modifying the parsed cmdline arguments. Uses the following environment
    variables:

    - ``SIERRA_NODEFILE``

    """

    def __init__(self, exec_env: str) -> None:
        pass

    def __call__(self, args: argparse.Namespace) -> None:
        if args.nodefile is None:
            assert 'SIERRA_NODEFILE' in os.environ,\
                "Non-Adhoc environment detected: 'SIERRA_NODEFILE' not found"
            args.nodefile = os.environ['SIERRA_NODEFILE']

        assert os.path.exists(args.nodefile), \
            f"SIERRA_NODEFILE '{args.nodefile}' does not exist"

        assert not args.platform_vc,\
            "Platform visual capture not supported on Adhoc"


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """
    Given a dictionary containing job information, generate the cmd to correctly
    invoke GNU Parallel in the ad-hoc HPC environment.
    """

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.ExpExecOpts) -> tp.List[types.ShellCmdSpec]:
        jobid = os.getpid()

        # Even if we are passed --nodelist, we still make our own copy of it, so
        # that the user can safely modify it (if they want to) after running
        # stage 1.
        nodelist = os.path.join(exec_opts['jobroot_path'],
                                "{0}-nodelist.txt".format(jobid))

        resume = ''
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts['exec_resume']:
            resume = '--resume-failed'

        # Make sure there are no duplicate nodes
        cmd1 = f'sort -u {0} > {1}'.format(exec_opts["nodelist"], nodelist)

        # GNU parallel cmd
        cmd2 = 'parallel {2} ' \
            '--jobs {1} ' \
            '--ungroup '\
            '--results {4} ' \
            '--joblog {3} ' \
            '--sshloginfile {0} ' \
            '--workdir {4} < "{5}"'

        cmd2 = cmd2.format(nodelist,
                           exec_opts['n_jobs'],
                           resume,
                           exec_opts['joblog_path'],
                           exec_opts['jobroot_path'],
                           exec_opts['cmdfile_path'])

        return [{'cmd': cmd1, 'shell': True, 'check': True},
                {'cmd': cmd2, 'shell': True, 'check': True}]


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
