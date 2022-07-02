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
"""
Robot plugin for running SIERRA with a set of Turtlebot3 robots.

"""

# Core packages
import os
import logging
import typing as tp
import argparse
import shutil

# 3rd party packages
import implements

# Project packages
from sierra.core import types, platform, utils
from sierra.core.experiment import bindings
import sierra.core.variables.batch_criteria as bc


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    """Configure SIERRA for the turtlebot3 execution environment.

    Uses the following environment variables (if they are not defined SIERRA
    will throw an error):

    - ``SIERRA_NODEFILE``

    """

    def __init__(self, exec_env: str) -> None:
        self.logger = logging.getLogger("robots.turtlebot3")

    def __call__(self, args: argparse.Namespace) -> None:
        if args.nodefile is None:
            assert 'SIERRA_NODEFILE' in os.environ,\
                ("Non-robots.turtlebot3 environment detected: --nodefile not "
                 "passed and 'SIERRA_NODEFILE' not found")
            args.nodefile = os.environ['SIERRA_NODEFILE']

        assert utils.path_exists(args.nodefile), \
            f"SIERRA_NODEFILE '{args.nodefile}' does not exist"
        self.logger.info("Using '%s' as robot hostnames file", args.nodefile)

        assert not args.platform_vc,\
            "Platform visual capture not supported on robots.turtlebot3"


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """Generate the cmds to invoke GNU Parallel to launch ROS on the turtlebots.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.SimpleDict) -> tp.List[types.ShellCmdSpec]:
        jobid = os.getpid()

        # Even if we are passed --nodelist, we still make our own copy of it, so
        # that the user can safely modify it (if they want to) after running
        # stage 1.
        nodelist = os.path.join(exec_opts['exp_input_root'],
                                "{0}-nodelist.txt".format(jobid))

        resume = ''
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts['exec_resume']:
            resume = '--resume-failed'

        # Make sure there are no duplicate nodes
        unique_nodes = {
            'cmd': 'sort -u {0} > {1}'.format(exec_opts["nodefile"], nodelist),
            'shell': True,
            'wait': True
        }

        # Make sure GNU parallel uses the right shell, because it seems to
        # defaults to /bin/sh since all cmds are run in a python shell which
        # does not have $SHELL set.
        use_bash = {
            'cmd': 'export PARALLEL_SHELL={0}'.format(shutil.which('bash')),
            'shell': True,
            'env': True,
            'wait': True
        }

        ret = [use_bash, unique_nodes]

        # 1 GNU parallel command to launch each experimental run, because each
        # run might use all available nodes/robots.
        for i in range(self.cmdopts['n_runs']):

            # GNU parallel cmd for robots (slaves)
            robots = 'parallel {2} ' \
                '--jobs {1} ' \
                '--results {4} ' \
                '--joblog {3} ' \
                '--sshloginfile {0} ' \
                '--workdir {4} < "{5}"'

            robots_ipath = exec_opts['cmdfile_stem_path'] + \
                f"_run{i}_slave" + exec_opts['cmdfile_ext']
            robots = robots.format(nodelist,
                                   exec_opts['n_jobs'],
                                   resume,
                                   os.path.join(exec_opts['scratch_dir'],
                                                f"parallel-slaves-run{i}.log"),
                                   exec_opts['scratch_dir'],
                                   robots_ipath)

            # If no master is spawned, then we need to wait for this GNU
            # parallel cmd. If the master is spawned, then we wait for THAT
            # command; waiting for both results in the master never starting
            # because that cmd is never run.
            ret.append({
                'cmd': robots,
                'shell': True,
                'wait': self.cmdopts['no_master_node']
            })

            if not self.cmdopts['no_master_node']:
                ros_master = 'parallel {3} ' \
                    '--results {1} ' \
                    '--joblog {0} ' \
                    '--workdir {1} < "{2}"'

                ros_master_ipath = exec_opts['cmdfile_stem_path'] + \
                    f"_run{i}_master" + exec_opts['cmdfile_ext']
                ros_master = ros_master.format(os.path.join(exec_opts['scratch_dir'],
                                                            f"parallel-master-run{i}.log"),
                                               exec_opts['scratch_dir'],
                                               ros_master_ipath,
                                               resume)

                ret.append(
                    {
                        'cmd': ros_master,
                        'shell': True,
                        'wait': not self.cmdopts['no_master_node']
                    })

            ret.append(
                {
                    'cmd': ('echo  "{0} seconds until launching next run!"; '
                            'sleep {0}s ;'.format(self.cmdopts['exec_inter_run_pause'])),
                    'shell': True,
                    'wait': True
                }
            )
        return ret


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.IConcreteBatchCriteria,
                 n_robots: int,
                 exp_num: int) -> None:
        self.criteria = criteria
        self.cmdopts = cmdopts
        self.exp_num = exp_num

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


class ExecEnvChecker(platform.ExecEnvChecker):
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        super().__init__(cmdopts)
        self.cmdopts = cmdopts
        self.logger = logging.getLogger('robots.turtlebot3')

    def __call__(self) -> None:
        nodes = self.parse_nodefile(self.cmdopts['nodefile'])
        for node in nodes:
            if int(node['n_cores']) != 1:
                self.logger.warning(("Nodefile %s, host %s has multiple "
                                     "cores; turtlebots are single core"),
                                    self.cmdopts['nodefile'],
                                    node['hostname'])
            if not self.cmdopts['skip_online_check']:
                self.check_connectivity(node['login'],
                                        node['hostname'],
                                        node['port'],
                                        'turtlebot3')


__api__ = [
    'ParsedCmdlineConfigurer',
    'ExpRunShellCmdsGenerator',
    'ExpShellCmdsGenerator',
    'ExecEnvChecker'
]
