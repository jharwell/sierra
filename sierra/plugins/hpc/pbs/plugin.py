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
import logging  # type: tp.Any
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, config
from sierra.core import plugin_manager as pm


class CmdoptsConfigurer():
    """
    Configure SIERRA for a TORQUE HPC by reading environment variables and
    modifying the parsed cmdline arguments. Uses the following environment
    variables (if any of them are not defined an assertion will be triggered):

    - ``PBS_NUM_PPN``
    - ``PBS_NODEFILE``
    - ``PBS_JOBID``
    - ``SIERRA_ARCH``
    - ``PARALLEL``

    """

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.pbs')

    def __call__(self, args) -> None:

        keys = ['PBS_NUM_PPN', 'PBS_NODEFILE',
                'PBS_JOBID', 'SIERRA_ARCH', 'PARALLEL']

        for k in keys:
            assert k in os.environ,\
                "Non-PBS environment detected: '{0}' not found".format(k)

        assert args.exec_jobs_per_node is not None, \
            "--exec-jobs-per-node is required (can't be computed from PBS)"

        assert not args.platform_vc,\
            "Platform visual capture not supported on PBS"

        if self.platform == 'platform.argos':
            self.configure_argos(args)
        elif self.platform == 'platform.rosgazebo':
            self.configure_rosgazebo(args)
        else:
            assert False,\
                "hpc.pbs does not support platform '{0}'".format(self.platform)

    def configure_argos(self, args) -> None:
        # For HPC, we want to use the the maximum # of simultaneous jobs per
        # node such that there is no thread oversubscription. We also always
        # want to allocate each physics engine its own thread for maximum
        # performance, per the original ARGoS paper.
        #
        # However, PBS does not have an environment variable for # jobs/node, so
        # we have to rely on the user to set this appropriately.
        args.physics_n_engines = int(
            float(os.environ['PBS_NUM_PPN']) / args.exec_jobs_per_node)

        self.logger.debug("Allocated %s physics engines/run, %s parallel runs/node",
                          args.physics_n_engines,
                          args.exec_jobs_per_node)

    def configure_rosgazebo(self, args: argparse.Namespace) -> None:
        # For now, nothing to do. If more stuff with physics engine
        # configuration is implemented, this may change.
        self.logger.debug("Allocated %s physics threads/run, %s parallel runs/node",
                          args.physics_n_threads,
                          args.exec_jobs_per_node)


class LaunchCmdGenerator():
    def __init__(self, platform: str) -> None:
        self.platform = platform

    def __call__(self, input_fpath: str) -> str:
        module = pm.SIERRAPluginManager().get_plugin_module(self.platform)
        return module.launch_cmd_generate('hpc.pbs', input_fpath)


class GNUParallelCmdGenerator():
    """
    Given a dictionary containing job information, generate the cmd to correctly
    invoke GNU Parallel on a TORQUE managed cluster.

    """

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.pbs')

    def __call__(self, parallel_opts: tp.Dict[str, tp.Any]) -> str:
        resume = ''
        jobid = os.environ['PBS_JOBID']
        nodelist = os.path.join(parallel_opts['jobroot_path'],
                                "{0}-nodelist.txt".format(jobid))

        resume = ''
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if parallel_opts['exec_resume']:
            resume = '--resume-failed'

        cmd = 'sort -u $PBS_NODEFILE > {0} && ' \
            'parallel {2} ' \
            '--jobs {1} '\
            '--results {4} '\
            '--joblog {3} '\
            '--sshloginfile {0} '\
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
        self.logger = logging.getLogger('hpc.pbs')

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
