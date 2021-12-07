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
HPC plugin for running SIERRA on HPC clusters using the SLURM scheduler.
"""

# Core packages
import os
import re
import typing as tp
import logging  # type: tp.Any

# 3rd party packages

# Project packages
from sierra.core import types, config
from sierra.core import plugin_manager as pm


class CmdoptsConfigurer():
    """
    Configure SIERRA for SLURM HPC by reading environment variables and
    modifying the parsed cmdline arguments. Uses the following environment
    variables (if any of them are not defined an assertion will be triggered):

    - ``SLURM_CPUS_PER_TASK``
    - ``SLURM_TASKS_PER_NODE``
    - ``SLURM_JOB_NODELIST``
    - ``SLURM_JOB_ID``
    - ``SLURM_ARCH``
    - ``PARALLEL``

    """

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.slurm')

    def __call__(self, args) -> None:
        keys = ['SLURM_CPUS_PER_TASK',
                'SLURM_TASKS_PER_NODE',
                'SLURM_JOB_NODELIST',
                'SLURM_JOB_ID',
                'SIERRA_ARCH',
                'PARALLEL']

        for k in keys:
            assert k in os.environ,\
                "Non-SLURM environment detected: '{0}' not found".format(k)

        assert not args.platform_vc,\
            "Platform visual capture not supported on SLURM"

        # SLURM_TASKS_PER_NODE can be set to things like '1(x32),3', indicating
        # that not all nodes will run the same # of tasks. SIERRA expects all
        # nodes to have the same # tasks allocated to each (i.e., a homogeneous
        # allocation), so we check for this.
        assert "," not in os.environ['SLURM_TASKS_PER_NODE'], \
            "SLURM_TASKS_PER_NODE not homogeneous"

        if self.platform == 'platform.argos':
            self.configure_argos(args)
        elif self.platform == 'platform.rosgazebo':
            self.configure_rosgazebo(args)
        else:
            assert False,\
                "hpc.slurm does not support platform '{0}'".format(
                    self.platform)

    def configure_argos(self, args) -> None:
        # For HPC, we want to use the the maximum # of simultaneous jobs per
        # node such that there is no thread oversubscription. We also always
        # want to allocate each physics engine its own thread for maximum
        # performance, per the original ARGoS paper.
        #
        # We rely on the user to request their job intelligently so that
        # SLURM_TASKS_PER_NODE is appropriate.
        if args.exec_jobs_per_node is None:
            res = re.search(r"^[^\(]+", os.environ['SLURM_TASKS_PER_NODE'])
            assert res is not None, \
                "Unexpected format in SLURM_TASKS_PER_NODE: '{0}'".format(
                    os.environ['SLURM_TASKS_PER_NODE'])
            args.exec_jobs_per_node = int(res.group(0))

        self.logger.debug("Allocated %s physics engines/run, %s parallel runs/node",
                          args.physics_n_engines,
                          args.exec_jobs_per_node)

    def configure_rosgazebo(self, args) -> None:
        # We rely on the user to request their job intelligently so that
        # SLURM_TASKS_PER_NODE is appropriate.
        if args.exec_jobs_per_node is None:
            res = re.search(r"^[^\(]+", os.environ['SLURM_TASKS_PER_NODE'])
            assert res is not None, \
                "Unexpected format in SLURM_TASKS_PER_NODE: '{0}'".format(
                    os.environ['SLURM_TASKS_PER_NODE'])
            args.exec_jobs_per_node = int(res.group(0))

        self.logger.debug("Allocated %s physics threads/run, %s parallel runs/node",
                          args.physics_n_threads,
                          args.exec_jobs_per_node)


class LaunchCmdGenerator():
    def __init__(self, platform: str) -> None:
        self.logger = logging.getLogger('hpc.slurm')

    def __call__(self, input_fpath: str) -> str:
        module = pm.SIERRAPluginManager().get_plugin_module(self.platform)
        return module.launch_cmd_generate('hpc.slurm', input_fpath)


class GNUParallelCmdGenerator():
    """
    Given a dictionary containing job information, generate the cmd to correctly
    invoke GNU Parallel in a SLURM HPC environment.
    """

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.slurm')

    def __call__(self, parallel_opts: tp.Dict[str, tp.Any]) -> str:
        jobid = os.environ['SLURM_JOB_ID']
        nodelist = os.path.join(parallel_opts['jobroot_path'],
                                "{0}-nodelist.txt".format(jobid))

        resume = ''
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if parallel_opts['exec_resume']:
            resume = '--resume-failed'

        # Move ALL ROS/gazebo output to the stdout/stderr files for parallel,
        # because you can't tell those programs not to print stuff/log
        # everything that's not an error to a file, and GNU parallel
        # echoes the stdout/stderr after commads finish in general.
        suppress = ''
        if self.platform == 'platform.rosgazebo':
            suppress = '--ungroup'

        cmd = 'scontrol show hostnames $SLURM_JOB_NODELIST > {0} && ' \
            'parallel {2} '\
            '--jobs {1} '\
            '{5} '\
            '--results {4} ' \
            '--joblog {3} '\
            '--sshloginfile {0}' \
            '--workdir {4} < "{5}"'
        return cmd.format(nodelist,
                          parallel_opts['n_jobs'],
                          resume,
                          parallel_opts['joblog_path'],
                          parallel_opts['jobroot_path'],
                          parallel_opts['cmdfile_path'],
                          suppress)


class LaunchWithVCCmdGenerator():
    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.slurm')

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
