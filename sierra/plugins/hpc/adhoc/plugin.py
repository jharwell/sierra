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
"""HPC plugin for running experiments with an ad-hoc set of compute nodes.

E.g., whatever computers you happen to have laying around in the lab.

"""

# Core packages
import os
import typing as tp
import argparse
import shutil
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core import types, utils
from sierra.core.experiment import bindings


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    """Configure SIERRA for ad-hoc HPC.

    May use the following environment variables:

    - ``SIERRA_NODEFILE`` - If this is not defined ``--nodefile`` must be
      passed.

    """

    def __init__(self, exec_env: str) -> None:
        pass

    def __call__(self, args: argparse.Namespace) -> None:
        if args.nodefile is None:
            assert 'SIERRA_NODEFILE' in os.environ,\
                ("Non-hpc.adhoc environment detected: --nodefile not "
                 "passed and 'SIERRA_NODEFILE' not found")
            args.nodefile = os.environ['SIERRA_NODEFILE']

        assert utils.path_exists(args.nodefile), \
            f"SIERRA_NODEFILE '{args.nodefile}' does not exist"

        assert not args.platform_vc,\
            "Platform visual capture not supported on Adhoc"


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """Generate the cmd to invoke GNU Parallel in the ad-hoc HPC environment.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> tp.List[types.ShellCmdSpec]:
        jobid = os.getpid()

        # Even if we are passed --nodelist, we still make our own copy of it, so
        # that the user can safely modify it (if they want to) after running
        # stage 1.
        nodelist = pathlib.Path(exec_opts['exp_input_root'],
                                f"{jobid}-nodelist.txt")

        resume = ''
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts['exec_resume']:
            resume = '--resume-failed'

        # Make sure there are no duplicate nodes
        unique_nodes = types.ShellCmdSpec(
            cmd='sort -u {0} > {1}'.format(exec_opts["nodefile"], nodelist),
            shell=True,
            wait=True)
        # Make sure GNU parallel uses the right shell, because it seems to
        # defaults to /bin/sh since all cmds are run in a python shell which
        # does not have $SHELL set.
        use_bash = types.ShellCmdSpec(
            cmd='export PARALLEL_SHELL={0}'.format(shutil.which('bash')),
            shell=True,
            wait=True,
            env=True)

        # GNU parallel cmd
        parallel = 'parallel {2} ' \
            '--jobs {1} ' \
            '--results {4} ' \
            '--joblog {3} ' \
            '--sshloginfile {0} ' \
            '--workdir {4} < "{5}"'

        log = pathlib.Path(exec_opts['scratch_dir'], "parallel.log")
        parallel = parallel.format(nodelist,
                                   exec_opts['n_jobs'],
                                   resume,
                                   log,
                                   exec_opts['scratch_dir'],
                                   exec_opts['cmdfile_stem_path'] + exec_opts['cmdfile_ext'])

        parallel_spec = types.ShellCmdSpec(cmd=parallel,
                                           shell=True,
                                           wait=True)

        return [unique_nodes, use_bash, parallel_spec]


__api__ = [
    'ParsedCmdlineConfigurer',
    'ExpShellCmdsGenerator',
]
