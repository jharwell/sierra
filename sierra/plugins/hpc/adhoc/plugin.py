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

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core import config


class CmdoptsConfigurer():
    """
    Configure SIERRA for ad-hoc HPC by reading environment variables and
    modifying the parsed cmdline arguments. Uses the following environment
    variables (if any of them are not defined an assertion will be triggered):

    - ``SIERRA_ADHOC_NODEFILE``

    """

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.adhoc')

    def __call__(self, args) -> None:
        keys = ['SIERRA_ADHOC_NODEFILE']

        for k in keys:
            assert k in os.environ,\
                "Non-Adhoc environment detected: '{0}' not found".format(k)

        assert not args.platform_vc,\
            "Platform visual capture not supported on PBS"

        with open(os.environ['SIERRA_ADHOC_NODEFILE'], 'r') as f:
            lines = f.readlines()
            n_nodes = len(lines)

            ppn = 0
            for line in lines:
                ppn = min(ppn, int(line.split('/')[0]))

        if self.platform == 'platform.argos':
            self.configure_argos(ppn, n_nodes, args)
        else:
            assert False,\
                "hpc.adhoc does not support platform '{0}'".format(
                    self.platform)

    def configure_argos(self, ppn: int, n_nodes: int, args) -> None:
        # For HPC, we want to use the the maximum # of simultaneous jobs per
        # node such that there is no thread oversubscription. We also always
        # want to allocate each physics engine its own thread for maximum
        # performance, per the original ARGoS paper.
        if args.exec_sims_per_node is None:
            args.exec_sims_per_node = int(float(args.n_runs) / n_nodes)

        args.physics_n_engines = int(ppn / args.exec_sims_per_node)

        self.logger.debug("Allocated %s physics engines/run, %s parallel runs/node",
                          args.physics_n_engines,
                          args.exec_sims_per_node,)


class LaunchCmdGenerator():
    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.adhoc')

    def __call__(self, input_fpath: str) -> str:
        if self.platform == 'platform.argos':
            return self.launch_cmd_argos(input_fpath)
        else:
            assert False,\
                "hpc.adhoc does not support platform '{0}'".format(
                    self.platform)

    def launch_cmd_argos(self, input_fpath: str) -> str:
        """
        Generate the ARGoS cmd to run on a machine in the ad-hoc cluster,
        given the path to an input file.

        """
        cmd = '{0} -c "{0}" --log-file /dev/null --logerr-file /dev/null'
        return cmd.format(config.kARGoS['cmdname'], input_fpath)


class GNUParallelCmdGenerator():
    """
    Given a dictionary containing job information, generate the cmd to correctly
    invoke GNU Parallel in the ad-hoc HPC environment.
    """

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.adhoc')

    def __call__(self, parallel_opts: tp.Dict[str, tp.Any]) -> str:
        jobid = os.getpid()
        nodelist = os.path.join(parallel_opts['jobroot_path'],
                                "{0}-nodelist.txt".format(jobid))

        resume = ''
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if parallel_opts['exec_resume']:
            resume = '--resume-failed'

        cmd = 'sort -u $SIERRA_ADHOC_NODEFILE > {0} && ' \
            'parallel {2} ' \
            '--jobs {1} ' \
            '--results {4} ' \
            '--joblog {3} ' \
            '--sshloginfile {0} ' \
            '--workdir {4} < "{5}"'

        return cmd.format(nodelist,
                          parallel_opts['n_jobs'],
                          resume,
                          parallel_opts['joblog_path'],
                          parallel_opts['jobroot_path'],
                          parallel_opts['cmdfile_path'])


class LaunchWithVCCmdGenerator():
    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.adhoc')

    def __call__(self,
                 cmdopts: types.Cmdopts,
                 launch_cmd: str) -> str:
        return launch_cmd


__api__ = [
    'CmdoptsConfigurer',
    'LaunchWithVCCmdGenerator',
    'GNUParallelCmdGenerator',
    'LaunchCmdGenerator'
]
