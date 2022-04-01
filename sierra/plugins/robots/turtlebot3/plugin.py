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
import logging  # type: tp.Any
import typing as tp
import argparse
import subprocess

# 3rd party packages
import implements

# Project packages
from sierra.core import types, config, platform, utils
from sierra.core import plugin_manager as pm
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

        assert os.path.exists(args.nodefile), \
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

    def exec_exp_cmds(self, exec_opts: types.ExpExecOpts) -> tp.List[types.ShellCmdSpec]:
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
            'check': True,
            'wait': True
        }

        ret = [unique_nodes]

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
                                                "parallel.log"),
                                   exec_opts['scratch_dir'],
                                   robots_ipath)

            ros_master = 'parallel ' \
                '--results {1} ' \
                '--joblog {0} ' \
                '--workdir {1} < "{2}"'

            ros_master_ipath = exec_opts['cmdfile_stem_path'] + \
                f"_run{i}_master" + exec_opts['cmdfile_ext']
            ros_master = ros_master.format(os.path.join(exec_opts['scratch_dir'],
                                                        "parallel.log"),
                                           exec_opts['scratch_dir'],
                                           ros_master_ipath)

            ret.append(
                {
                    'cmd': robots,
                    'shell': True,
                    'check': True,
                    'wait': False
                })
            ret.append(
                {
                    'cmd': ros_master,
                    'shell': True,
                    'check': True,
                    'wait': True
                })
            ret.append(
                {
                    'cmd': ('echo  "{0} seconds until launching next run!"; '
                            'sleep {0}s ;'.format(self.cmdopts['exec_inter_run_pause'])),
                    'check': False,
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
        if host == 'slave':
            return []

        # ROS master node
        exp_dirname = self.criteria.gen_exp_dirnames(self.cmdopts)[self.exp_num]
        batch_template_path = utils.batch_template_path(self.cmdopts,
                                                        self.criteria.batch_input_root,
                                                        exp_dirname)

        master_node = {
            # --wait tells roslaunch to wait for the configured master to
            # come up before launch the "master" code.
            #
            # 2022/02/28: -p (apparently) tells roslaunch to to CONNECT to a
            # master at the specified ort, but to LAUNCH a new master at the
            # specified port. This is not really documented well.
            'cmd': '{0} --wait {1}_run{2}_master{3};'.format(config.kROS['launch_cmd'],
                                                             batch_template_path,
                                                             run_num,
                                                             config.kROS['launch_file_ext']),
            'shell': True,
            'check': True,
            'wait': True
        }

        return [master_node]

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        return []


class ExecEnvChecker(platform.ExecEnvChecker):
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        self.logger = logging.getLogger('robots.turtlebot3')

    def __call__(self) -> None:
        nodes = self.parse_nodefile(self.cmdopts['nodefile'])
        for hostname in nodes:
            if int(nodes[hostname]['n_cores']) != 1:
                self.logger.warning(("Nodefile %s, host %s has multiple "
                                     "cores; turtlebots are single core"),
                                    self.cmdopts['nodefile'],
                                    hostname)

            self.check_connectivity(nodes[hostname]['login'],
                                    hostname,
                                    'turtlebot3')


__api__ = [
    'ParsedCmdlineConfigurer',
    'ExpRunShellCmdsGenerator',
    'ExpShellCmdsGenerator',
    'ExecEnvChecker'
]
