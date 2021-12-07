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
import multiprocessing
import random
import typing as tp
import logging  # type: tp.Any
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, config
from sierra.core import plugin_manager as pm


class CmdoptsConfigurer():
    """
    Configure SIERRA for local machine according to the # CPUs available on the
    local machine.

    """

    def __init__(self, platform: str) -> None:

        self.platform = platform
        self.logger = logging.getLogger('hpc.local')

    def __call__(self, args: argparse.Namespace) -> None:
        if self.platform == 'platform.argos':
            self.configure_argos(args)
        elif self.platform == 'platform.rosgazebo':
            self.configure_rosgazebo(args)
        else:
            assert False,\
                "hpc.local does not support platform '{0}'".format(
                    self.platform)

    def configure_argos(self, args: argparse.Namespace) -> None:
        if any([1, 2]) in args.pipeline:
            assert args.physics_n_engines is not None,\
                '--physics-n-engines is required for --exec-env=hpc.local when running stage{1,2}'

        ppn_per_run_req = args.physics_n_engines

        if args.exec_jobs_per_node is None:
            # Every physics engine gets at least 1 core
            parallel_jobs = int(multiprocessing.cpu_count() /
                                float(ppn_per_run_req))
            if parallel_jobs == 0:
                self.logger.warning(("Local machine has %s cores, but %s "
                                     "physics engines/run requested; "
                                     "allocating anyway"),
                                    multiprocessing.cpu_count(),
                                    ppn_per_run_req)
                parallel_jobs = 1

            # Make sure we don't oversubscribe cores--each simulation needs at
            # least 1 core.
            args.exec_jobs_per_node = min(args.n_runs, parallel_jobs)

        self.logger.debug("Allocated %s physics engines/run, %s parallel runs/node",
                          args.physics_n_engines,
                          args.exec_jobs_per_node)

    def configure_rosgazebo(self, args: argparse.Namespace) -> None:
        # For now. If more physics engine configuration is added, this will
        # change.
        ppn_per_run_req = 1

        if args.exec_jobs_per_node is None:
            parallel_jobs = int(multiprocessing.cpu_count() /
                                float(ppn_per_run_req))
            if parallel_jobs == 0:
                self.logger.warning(("Local machine has %s cores, but "
                                     "%s threads/run requested; "
                                     "allocating anyway"),
                                    multiprocessing.cpu_count(),
                                    ppn_per_run_req)
                parallel_jobs = 1

            # Make sure we don't oversubscribe cores--each simulation needs at
            # least 1 core.
            args.exec_jobs_per_node = min(args.n_runs, parallel_jobs)

        self.logger.debug("Allocated %s physics threads/run, %s parallel runs/node",
                          args.physics_n_threads,
                          args.exec_jobs_per_node)


class LaunchCmdGenerator():
    def __init__(self, platform: str) -> None:
        self.platform = platform

    def __call__(self, input_fpath: str) -> str:
        module = pm.SIERRAPluginManager().get_plugin_module(self.platform)
        return module.launch_cmd_generate('hpc.local', input_fpath)


class GNUParallelCmdGenerator():
    """
    Given a dictionary containing job information, generate the cmd to correctly
    invoke GNU Parallel in the local HPC environment.
    """

    def __init__(self, platform: str) -> None:
        self.logger = logging.getLogger('hpc.local')
        self.platform = platform

    def __call__(self, parallel_opts: tp.Dict[str, tp.Any]) -> str:
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

        cmd = 'cd {0} && ' \
            'parallel ' \
            '--eta '\
            '{5} '\
            '--jobs {2} ' \
            '--results {0} '\
            '--joblog {3} '\
            '--no-notice < "{4}"'

        cmd = cmd.format(parallel_opts['jobroot_path'],
                         resume,
                         parallel_opts['n_jobs'],
                         parallel_opts['joblog_path'],
                         parallel_opts['cmdfile_path'],
                         suppress)

        return cmd


class LaunchWithVCCmdGenerator():
    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger('hpc.local')

    def __call__(self,
                 cmdopts: types.Cmdopts,
                 launch_cmd: str) -> None:
        if self.platform == 'platform.argos':
            return self.vc_cmd_argos(cmdopts, launch_cmd)
        elif self.platform == 'platform.rosgazebo':
            return launch_cmd
        else:
            assert False,\
                "Visual capture for hpc.local not supported for platform '{0}'".format(
                    self.platform)

    def vc_cmd_argos(self, cmdopts: types.Cmdopts, launch_cmd: str):
        """
        Generate the command for running ARGoS under Xvfb for headless rendering
        (if configured).
        """

        # When running ARGoS under Xvfb in order to headlessly render frames, we
        # need to start a per-instance Xvfb server that we tell ARGoS to use via
        # the DISPLAY environment variable, which will then be killed when the
        # shell GNU parallel spawns to run each line in the commands file exits.
        cmd = ''
        if cmdopts['platform_vc']:
            display_port = random.randint(0, 1000000)
            cmd = "eval 'Xvfb :{0} -screen 0, 1600x1200x24 &' && "\
                "DISPLAY=:{0} {1}"
            cmd = cmd.format(display_port, launch_cmd)
        else:
            cmd = launch_cmd

        return cmd


__api__ = [
    'CmdoptsConfigurer',
    'LaunchWithVCCmdGenerator',
    'GNUParallelCmdGenerator',
    'LaunchCmdGenerator'
]
