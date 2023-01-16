# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""HPC plugin for running SIERRA locally.

Not necessarily HPC, but it fits well enough under that semantic umbrella.

"""

# Core packages
import typing as tp
import shutil
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """
    Generate the command to invoke GNU parallel for local HPC.
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
        resume = ''

        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts['exec_resume']:
            resume = '--resume-failed'

        # Make sure GNU parallel uses the right shell, because it seems to
        # defaults to /bin/sh since all cmds are run in a python shell which
        # does not have $SHELL set.
        shell = shutil.which('bash')
        use_bash = types.ShellCmdSpec(cmd=f'export PARALLEL_SHELL={shell}',
                                      shell=True,
                                      wait=True,
                                      env=True)

        parallel = 'parallel {1} ' \
            '--jobs {2} ' \
            '--results {0} '\
            '--joblog {3} '\
            '--no-notice < "{4}"'

        log = pathlib.Path(exec_opts['scratch_dir'], "parallel.log")
        parallel = parallel.format(exec_opts['scratch_dir'],
                                   resume,
                                   exec_opts['n_jobs'],
                                   log,
                                   exec_opts['cmdfile_stem_path'] +
                                   exec_opts['cmdfile_ext'])

        parallel_spec = types.ShellCmdSpec(cmd=parallel,
                                           shell=True,
                                           wait=True)

        return [use_bash, parallel_spec]


__api__ = [
    'ExpShellCmdsGenerator'
]
