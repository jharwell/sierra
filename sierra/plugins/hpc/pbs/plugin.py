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
HPC plugin for running SIERRA on HPC clusters using the TORQUE-PBS scheduler.
"""

# Core packages
import os
import typing as tp
import argparse
import shutil

# 3rd party packages
import implements

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings
import sierra.core.variables.batch_criteria as bc


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    """Configure SIERRA for PBS HPC.

    Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

    - ``PBS_NUM_PPN``
    - ``PBS_NODEFILE``
    - ``PBS_JOBID``
    - ``SIERRA_ARCH``
    - ``PARALLEL``

    """

    def __init__(self, exec_env: str) -> None:
        pass

    def __call__(self, args: argparse.Namespace) -> None:
        keys = ['PBS_NUM_PPN', 'PBS_NODEFILE',
                'PBS_JOBID', 'SIERRA_ARCH', 'PARALLEL']

        for k in keys:
            assert k in os.environ,\
                f"Non-PBS environment detected: '{k}' not found"

        assert args.exec_jobs_per_node is not None, \
            "--exec-jobs-per-node is required (can't be computed from PBS)"

        assert not args.platform_vc,\
            "Platform visual capture not supported on PBS"


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """Generate the cmd to invoke GNU Parallel on PBS HPC.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.SimpleDict) -> tp.List[types.ShellCmdSpec]:
        resume = ''
        jobid = os.environ['PBS_JOBID']
        nodelist = os.path.join(exec_opts['exp_input_root'],
                                f"{jobid}-nodelist.txt")

        resume = ''
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts['exec_resume']:
            resume = '--resume-failed'

        unique_nodes = {
            'cmd': f'sort -u $PBS_NODEFILE > {nodelist}',
            'shell': True,
            'wait': True
        }

        # Make sure GNU parallel uses the right shell, because it seems to
        # defaults to /bin/sh since all cmds are run in a python shell which
        # does not have $SHELL set.
        use_bash = {
            'cmd': 'export PARALLEL_SHELL={0}'.format(shutil.which('bash')),
            'shell': True,
            'wait': True,
            'env': True,
        }
        ret = [unique_nodes, use_bash]

        parallel = 'parallel {2} ' \
            '--jobs {1} '\
            '--results {4} '\
            '--joblog {3} '\
            '--sshloginfile {0} '\
            '--workdir {4} < "{5}"'

        parallel = parallel.format(nodelist,
                                   exec_opts['n_jobs'],
                                   resume,
                                   os.path.join(exec_opts['scratch_dir'],
                                                "parallel.log"),
                                   exec_opts['scratch_dir'],
                                   exec_opts['cmdfile_stem_path'] +
                                   exec_opts['cmdfile_ext'])

        ret.append({
            'cmd': parallel,
            'shell': True,
            'wait': True
        })

        return ret


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    """
    Stub implementation.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.IConcreteBatchCriteria,
                 n_robots: int,
                 exp_num: int) -> None:
        pass

    def pre_run_cmds(self,
                     host: str,
                     input_fpath: str,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_run_cmds(self,
                      host: str,
                      input_fpath: str,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        return []


class ExecEnvChecker():
    """
    Stub implementation.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        pass

    def __call__(self) -> None:
        pass


__api__ = [
    'ParsedCmdlineConfigurer',
    'ExpRunShellCmdsGenerator',
    'ExpShellCmdsGenerator',
    'ExecEnvChecker'
]
