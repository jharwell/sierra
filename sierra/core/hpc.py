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
Classes for the various HPC plugins that can be used with SIERRA for running
experiments.
"""

# Core packages
import os
import typing as tp
import subprocess
import shutil
import re

# 3rd party packages
from singleton_decorator import singleton
import packaging.version

# Project packages
import sierra.core.plugin_manager as pm
import sierra.core.config


################################################################################
# Dispatchers
################################################################################


class ARGoSCmdGenerator():
    """
    Dispatcher to generate the ARGoS cmd to run for a simulation, given its input file.
    """

    def __call__(self, cmdopts: tp.Dict[str, tp.Any], input_fpath: str) -> str:
        hpc = pm.SIERRAPluginManager().get_plugin(cmdopts['hpc_env'])
        return hpc.argos_cmd_generate(input_fpath)  # type: ignore


class GNUParallelCmdGenerator():
    """
    Dispatcher to generate the GNU Parallel cmd SIERRA will use to run experiments in the specified
    HPC environment.

    Passes the following dictionary to the configured HPC plugin:
    - jobroot_path - The root directory for the batch experiment.
    - exec_resume - Is this a resume of a previously run experiment?
    - n_jobs - How many parallel jobs are allowed per node?
    - joblog_path - The logfile for GNU parallel output.
    - cmdfile_path - The file containing the ARGoS cmds to run.

    """

    def __call__(self, hpc_env: str, parallel_opts: tp.Dict[str, tp.Any]) -> str:
        hpc = pm.SIERRAPluginManager().get_plugin(hpc_env)
        return hpc.gnu_parallel_cmd_generate(parallel_opts)  # type: ignore


class XvfbCmdGenerator():
    """
    Dispatcher to generate the Xvfb wrapper cmd prepended to the generated ARGoS cmd for headless
    rendering.
    """

    def __call__(self, cmdopts: tp.Dict[str, tp.Any]) -> str:
        hpc = pm.SIERRAPluginManager().get_plugin(cmdopts['hpc_env'])
        return hpc.xvfb_cmd_generate(cmdopts)  # type: ignore


class EnvConfigurer():
    """
    Dispatcher for configuring the HPC environment via the specified plugin.
    """

    def __call__(self, hpc_env: str, args):
        args.__dict__['hpc_env'] = hpc_env
        hpc = pm.SIERRAPluginManager().get_plugin(hpc_env)
        hpc.env_configure(args)
        return args


class EnvChecker():
    """
    Verify the configured HPC environment before running any experiments during stage 2.
    """

    def __init__(self, hpc_env: str):
        self.hpc_env = hpc_env

    def __call__(self) -> None:
        # Check we can find ARGoS
        if self.hpc_env in ['hpc.local', 'hpc.adhoc']:
            argos3 = 'argos3'
        elif self.hpc_env in ['hpc.pbs', 'hpc.slurm']:
            arch = os.environ.get('SIERRA_ARCH')
            argos3 = 'argos3-{0}'.format(arch)
        else:
            assert False, "FATAL: Bad HPC env {0}".format(self.hpc_env)

        if shutil.which(argos3):
            result = subprocess.run(' '.join([argos3, '-v']),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    shell=True)
        else:
            assert False, "FATAL: Cannot find {0}".format(argos3)

        # Check ARGoS version
        res = re.search(r'beta[0-9]+', result.stdout.decode('utf-8'))
        assert res is not None, "FATAL: ARGOS_VERSION not in -v output"

        version = packaging.version.parse(res.group(0))
        min_version = packaging.version.parse(sierra.core.config.kARGoS['min_version'])

        assert version >= min_version,\
            "FATAL: ARGoS version {0} < min required {1}".format(version, min_version)

        # Check ARGoS plugin path is defined
        assert os.environ.get("ARGOS_PLUGIN_PATH") is not None, \
            "FATAL: You must have ARGOS_PLUGIN_PATH defined"


__api__ = [
    'EnvConfigurer',
    'EnvChecker',
    'XvfbCmdGenerator',
    'GNUParallelCmdGenerator',
    'ARGoSCmdGenerator'


]
