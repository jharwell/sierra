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
Classes for the generating the commands to run :term:`experiments <Batch
Experiment>` on multiple :term:`platforms <Platform>` using multiple execution
methods.
"""

# Core packages
import os
import typing as tp
import subprocess
import shutil
import re
import argparse
import logging  # type: tp.Any
import socket

# 3rd party packages
import packaging.version

# Project packages
import sierra.core.plugin_manager as pm
from sierra.core import config
from sierra.core import types
from sierra.core import utils

################################################################################
# Dispatchers
################################################################################


class CmdlineParserGenerator():
    """
    Dispatcher to generate additional cmdline arguments which are dependent on
    the selected ``--platform``.
    """

    def __call__(self, platform: str) -> argparse.ArgumentParser:
        module = pm.SIERRAPluginManager().get_plugin_module(platform)
        return module.cmdline_parser_generate()  # type: ignore


class LaunchCmdGenerator():
    """
    Dispatcher to generate the cmd to launch execution of controller code on a
    real robot (for real robot platforms) or to launch execution of a simulation
    (for simulator platforms).

    Arguments:
        cmdopts: Dictionary of parsed cmdline options.
        input_fpath: Path to the input file for the simulation/robot.
    """

    def __call__(self,
                 platform: str,
                 exec_env: str,
                 input_fpath: str) -> str:
        env = pm.SIERRAPluginManager().get_plugin_module(exec_env)
        return env.LaunchCmdGenerator(platform)(input_fpath)  # type: ignore


class GNUParallelCmdGenerator():
    """
    Dispatcher to generate the GNU Parallel cmd SIERRA will use to run
    experiments in the specified execution environment for the specified
    platform.

    Passes the following dictionary to the configured execution environment
    plugin (not all plugins may need all arguments):

    - ``jobroot_path`` - The root directory for the batch experiment.

    - ``exec_resume`` - Is this a resume of a previously run experiment?

    - ``n_jobs`` - How many parallel jobs are allowed per node?

    - ``joblog_path`` - The logfile for GNU parallel output.

    - ``cmdfile_path`` - The file containing the launch cmds to run (one per
                         line)

    """

    def __call__(self,
                 platform: str,
                 exec_env: str,
                 parallel_opts: tp.Dict[str, tp.Any]) -> str:
        env = pm.SIERRAPluginManager().get_plugin_module(exec_env)
        cmd = env.GNUParallelCmdGenerator(platform)(parallel_opts)
        return cmd  # type: ignore


class LaunchWithVCCmdGenerator():
    """
    Dispatcher to modify the non-rendering launch cmd for the specified platform
    to enable capturing of simulation frames/videos via headless rendering.

    """

    def __call__(self, cmdopts: types.Cmdopts, launch_cmd: str) -> str:
        env = pm.SIERRAPluginManager().get_plugin_module(cmdopts['exec_env'])
        generator = env.LaunchWithVCCmdGenerator(cmdopts['platform'])
        cmd = generator(cmdopts, launch_cmd)
        return cmd   # type: ignore


class CmdoptsConfigurer():
    """
    Dispatcher for configuring the main cmdopts dictionary for the selected
    platform and execution environment.
    """

    def __call__(self,
                 platform: str,
                 exec_env: str,
                 args: argparse.Namespace) -> argparse.Namespace:
        # Configure cmdopts for selected platform
        args.__dict__['platform'] = platform

        # Configure cmdopts for selected execution enivornment
        args.__dict__['exec_env'] = exec_env
        env = pm.SIERRAPluginManager().get_plugin_module(exec_env)  # type: ignore
        env.CmdoptsConfigurer(platform)(args)
        return args


class ExpRunVCConfigurer():
    """
    Perform platform-specific configuration for a given experimental run to
    enable/setup visual capture for that run.
    """

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: types.Cmdopts,
                 run_output_dir: str) -> None:
        if self.platform == 'platform.argos':
            self.configure_argos(run_output_dir)
        else:
            assert False,\
                "Platform '{0}' does not support visual capture".format(
                    self.platform)

    def configure_argos(self, run_output_dir: str) -> None:
        frames_fpath = os.path.join(run_output_dir,
                                    config.kARGoS['frames_leaf'])
        assert shutil.which('Xvfb') is not None, "Xvfb not found"
        utils.dir_create_checked(frames_fpath, exist_ok=True)


class PostExpVCCleanup():
    """
    Perform platform-specific cleanup after a given experiment if visual capture
    was enabled.
    """

    def __init__(self, platform: str) -> None:
        self.platform = platform
        self.logger = logging.getLogger(__name__)

    def __call__(self) -> None:
        if self.platform == 'platform.argos':
            self.cleanup_argos()
        else:
            assert False,\
                "Platform '{0}' does not support visual capture".format(
                    self.platform)

    def cleanup_argos(self) -> None:
        self.logger.trace("Cleaning up orphan Xvfb processes")
        # Cleanup Xvfb processes which were started in the background. If SIERRA
        # was run with --exec-resume, then there may be no Xvfb processes to
        # kill, so we can't (in general) check the return code.
        subprocess.run(['killall', 'Xvfb'], check=False)


class ExecEnvChecker():
    """
    Verify the configured ``--exec-env` for the configured ``--platform`` before
    running any experiments during stage 2. This is needed in addition to the
    checks performed during stage 1, because stage 2 can be run on its own
    without running stage 1 first on the same SIERRA invocation.

    """

    def __init__(self, platform: str, exec_env: str):
        self.platform = platform
        self.exec_env = exec_env

    def __call__(self) -> None:
        if self.platform == 'platform.argos':
            self.check_argos()
        elif self.platform == 'platform.rosgazebo':
            self.check_rosgazebo()
        else:
            assert False,\
                "HPC environments not supported for platform '{0}'".format(
                    self.platform)

    def check_rosgazebo(self) -> None:
        keys = ['ROS_DISTRO', 'GAZEBO_MASTER_URI']

        for k in keys:
            assert k in os.environ,\
                "Non-ROS/non-Gazebo environment detected: '{0}' not found".format(
                    k)

        # Check ROS distro
        assert os.environ['ROS_DISTRO'] in ['melodic', 'noetic'],\
            "SIERRA only supports ROS melodic and noetic"

        # Check we can find Gazebo
        version = self._check_for_simulator(config.kGazebo['launch_cmd'])

        # Check Gazebo version
        res = re.search(r'[0-9]+.[0-9]+.[0-9]+', version.stdout.decode('utf-8'))
        assert res is not None, "Gazebo version not in -v output"

        version = packaging.version.parse(res.group(0))
        min_version = packaging.version.parse(config.kGazebo['min_version'])

        assert version >= min_version,\
            "Gazebo version {0} < min required {1}".format(version,
                                                           min_version)

    def check_argos(self) -> None:
        keys = ['ARGOS_PLUGIN_PATH']

        for k in keys:
            assert k in os.environ,\
                "Non-ARGoS environment detected: '{0}' not found".format(k)

        # Check we can find ARGoS
        version = self._check_for_simulator(config.kARGoS['launch_cmd'])

        # Check ARGoS version
        res = re.search(r'beta[0-9]+', version.stdout.decode('utf-8'))
        assert res is not None, "ARGOS_VERSION not in -v output"

        version = packaging.version.parse(res.group(0))
        min_version = packaging.version.parse(config.kARGoS['min_version'])

        assert version >= min_version,\
            "ARGoS version {0} < min required {1}".format(version,
                                                          min_version)

    def _check_for_simulator(self, name: str):
        if self.exec_env in ['hpc.local', 'hpc.adhoc']:
            shellname: str = name
        elif self.exec_env in ['hpc.pbs', 'hpc.slurm']:
            arch = os.environ.get('SIERRA_ARCH')
            shellname: str = '{0}-{1}'.format(name, arch)
        else:
            assert False,\
                "Bad HPC env {0} for platform {1}".format(self.exec_env,
                                                          self.platform)

        if shutil.which(shellname):
            version_info = subprocess.run(' '.join([shellname, '-v']),
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          shell=True)
            return version_info
        else:
            assert False,\
                "Bad HPC env '{0}' for platform '{1}': cannot find '{2}'".format(self.exec_env,
                                                                                 self.platform,
                                                                                 name)
            return None


def get_free_port(self) -> int:
    """
    Determines a free port using sockets. From
    https://stackoverflow.com/questions/44875422/how-to-pick-a-free-port-for-a-subprocess

    Because of TCP TIME_WAIT, close()d ports are still unusable for a few
    minutes, which will leave plenty of time for SIERRA to assign all unique
    ports to processes during stage 2.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))  # bind to port 0 -> OS allocates free port
    port = s.getsockname()[1]
    s.close()
    return port


__api__ = [
    'CmdlineParserGenerator'
    'CmdoptsConfigurer',
    'LaunchWithVCCmdGenerator',
    'GNUParallelCmdGenerator',
    'LaunchCmdGenerator',
    'HPCEnvChecker',
]
