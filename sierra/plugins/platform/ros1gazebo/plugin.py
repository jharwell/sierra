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
Provides platform-specific callbacks for the :term:`ROS1+Gazebo` platform.
"""
# Core packages
import argparse
import logging
import os
import re
import typing as tp
import sys
import pathlib
import psutil

# 3rd party packages
import packaging.version
import implements

# Project packages
from sierra.plugins.platform.ros1gazebo import cmdline
from sierra.core import hpc, platform, config, ros1, types
from sierra.core.experiment import bindings, definition, xml
import sierra.core.variables.batch_criteria as bc


class CmdlineParserGenerator():
    def __call__(self) -> argparse.ArgumentParser:
        parent1 = hpc.cmdline.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
        parent2 = ros1.cmdline.ROSCmdline([-1, 1, 2, 3, 4, 5]).parser
        return cmdline.PlatformCmdline(parents=[parent1, parent2],
                                       stages=[-1, 1, 2, 3, 4, 5]).parser


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    def __init__(self, exec_env: str) -> None:
        self.exec_env = exec_env
        self.logger = logging.getLogger('ros1gazebo.plugin')

    def __call__(self, args: argparse.Namespace) -> None:
        # No configuration needed for stages 3-5
        if not any(stage in args.pipeline for stage in [1, 2]):
            return

        if self.exec_env == 'hpc.local':
            self._hpc_local(args)
        elif self.exec_env == 'hpc.adhoc':
            self._hpc_adhoc(args)
        elif self.exec_env == 'hpc.slurm':
            self._hpc_slurm(args)
        elif self.exec_env == 'hpc.pbs':
            self._hpc_pbs(args)
        else:
            raise RuntimeError(f"'{self.exec_env}' unsupported on ROS1+Gazebo")

    def _hpc_pbs(self, args: argparse.Namespace) -> None:
        # For now, nothing to do. If more stuff with physics engine
        # configuration is implemented, this may change.
        self.logger.debug("Allocated %s physics threads/run, %s parallel runs/node",
                          args.physics_n_threads,
                          args.exec_jobs_per_node)

    def _hpc_slurm(self, args: argparse.Namespace) -> None:
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

    def _hpc_adhoc(self, args: argparse.Namespace) -> None:
        nodes = platform.ExecEnvChecker.parse_nodefile(args.nodefile)
        ppn = sys.maxsize
        for node in nodes:
            ppn = min(ppn, node.n_cores)

        if args.exec_jobs_per_node is None:
            args.exec_jobs_per_node = int(float(args.n_runs) / len(nodes))

        self.logger.debug("Allocated %s physics threads/run, %s parallel runs/node",
                          args.physics_n_threads,
                          args.exec_jobs_per_node)

    def _hpc_local(self, args: argparse.Namespace) -> None:
        # For now. If more physics engine configuration is added, this will
        # change.
        ppn_per_run_req = 1

        if args.exec_jobs_per_node is None:
            parallel_jobs = int(psutil.cpu_count() / float(ppn_per_run_req))

        if parallel_jobs == 0:
            self.logger.warning(("Local machine has %s logical cores, but "
                                 "%s threads/run requested; "
                                 "allocating anyway"),
                                psutil.cpu_count(),
                                ppn_per_run_req)
            parallel_jobs = 1

        # Make sure we don't oversubscribe cores--each simulation needs at
        # least 1 core.
        args.exec_jobs_per_node = min(args.n_runs, parallel_jobs)

        self.logger.debug("Allocated %s physics threads/run, %s parallel runs/node",
                          args.physics_n_threads,
                          args.exec_jobs_per_node)


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.BatchCriteria,
                 n_robots: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.gazebo_port = -1
        self.roscore_port = -1

    def pre_run_cmds(self,
                     host: str,
                     input_fpath: pathlib.Path,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        if host == 'master':
            return []

        # First, the cmd to start roscore. We need to be on a unique port so
        # that multiple ROS instances corresponding to multiple Gazebo
        # instances with the same topic names are considered distinct/not
        # accessible between instances of Gazebo.
        self.roscore_port = config.kROS['port_base'] + run_num * 2

        # roscore will run on each slave node used during stage 2, so we have to
        # use 'localhost' for binding.
        roscore_uri = types.ShellCmdSpec(
            cmd=f'export ROS_MASTER_URI=http://localhost:{self.roscore_port};',
            shell=True,
            wait=True,
            env=True)

        # Each experiment gets their own roscore. Because each roscore has a
        # different port, this prevents any robots from pre-emptively starting
        # the next experiment before the rest of the robots have finished the
        # current one.
        roscore_process = types.ShellCmdSpec(
            cmd=f'roscore -p {self.roscore_port} & ',
            shell=True,
            wait=False)

        # Second, the command to give Gazebo a unique port on the host during
        # stage 2. We need to be on a unique port so that multiple Gazebo
        # instances can be run in parallel.
        self.gazebo_port = config.kROS['port_base'] + run_num * 2 + 1

        # 2021/12/13: You can't use HTTPS for some reason or gazebo won't
        # start...
        gazebo_uri = types.ShellCmdSpec(
            cmd=f'export GAZEBO_MASTER_URI=http://localhost:{self.gazebo_port};',
            shell=True,
            env=True,
            wait=True
        )

        return [roscore_uri, roscore_process, gazebo_uri]

    def exec_run_cmds(self,
                      host: str,
                      input_fpath: pathlib.Path,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        if host == 'master':
            return []

        # For ROS+gazebo, we have two files per experimental run:
        #
        # - One for the stuff that is run on the ROS master (can be
        #   nothing/empty file).
        #
        # - One for the stuff that describes what to run on each robot/how many
        #   robots to spawn.
        #
        # We COULD do it all in a single file, but in order to share base code
        # with the ROS+robot platform, we need to do it this way.
        #
        # 2022/02/28: I don't use the -u argument here to set ROS_MASTER_URI,
        # because ROS works well enough when only running on the localhost, in
        # terms of respecting whatever the envvar is set to.
        master = str(input_fpath) + "_master" + config.kROS['launch_file_ext']
        robots = str(input_fpath) + "_robots" + config.kROS['launch_file_ext']

        cmd = '{0} --wait {1} {2} '.format(config.kROS['launch_cmd'],
                                           master,
                                           robots)

        # ROS/Gazebo don't provide options to not print stuff, so we have to use
        # the nuclear option.
        if self.cmdopts['exec_devnull']:
            cmd += '2>&1 > /dev/null'

        cmd += ';'

        return [types.ShellCmdSpec(cmd=cmd, shell=True, wait=True)]

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        return []


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self,
                      exec_opts: types.StrDict) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        # Cleanup roscore and gazebo processes which are still active because
        # they don't know how to clean up after themselves.
        #
        # This is OK to do even when we have multiple Gazebo+ROS instances on
        # the same machine, because we only run these commands after an
        # experiment finishes, so there isn't anything currently running we
        # might accidentally kill.
        #
        # Can't use killall, because that returns non-zero if things
        # are cleaned up nicely.
        return [types.ShellCmdSpec(cmd='if pgrep gzserver; then pkill gzserver; fi;',
                                   shell=True,
                                   wait=True),
                types.ShellCmdSpec(cmd='if pgrep rosmaster; then pkill rosmaster; fi;',
                                   shell=True,
                                   wait=True),
                types.ShellCmdSpec(cmd='if pgrep roscore; then pkill roscore; fi;',
                                   shell=True,
                                   wait=True),
                types.ShellCmdSpec(cmd='if pgrep rosout; then pkill rosout; fi;',
                                   shell=True,
                                   wait=True)]


@implements.implements(bindings.IExpConfigurer)
class ExpConfigurer():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

    def for_exp_run(self,
                    exp_input_root: pathlib.Path,
                    run_output_root: pathlib.Path) -> None:
        pass

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        pass

    def cmdfile_paradigm(self) -> str:
        return 'per-exp'


@implements.implements(bindings.IExecEnvChecker)
class ExecEnvChecker(platform.ExecEnvChecker):
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        super().__init__(cmdopts)

    def __call__(self) -> None:
        keys = ['ROS_DISTRO', 'ROS_VERSION']

        for k in keys:
            assert k in os.environ,\
                f"Non-ROS+Gazebo environment detected: '{k}' not found"

        # Check ROS distro
        assert os.environ['ROS_DISTRO'] in ['kinetic', 'noetic'],\
            "SIERRA only supports ROS1 kinetic,noetic"

        # Check ROS version
        assert os.environ['ROS_VERSION'] == "1",\
            "Wrong ROS version: this plugin is for ROS1"

        # Check we can find Gazebo
        version = self.check_for_simulator(config.kGazebo['launch_cmd'])

        # Check Gazebo version
        res = re.search(r'[0-9]+.[0-9]+.[0-9]+', version.stdout.decode('utf-8'))
        assert res is not None, "Gazebo version not in -v output"

        version = packaging.version.parse(res.group(0))
        min_version = packaging.version.parse(config.kGazebo['min_version'])

        assert version >= min_version,\
            f"Gazebo version {version} < min required {min_version}"


def population_size_from_pickle(adds_def: tp.Union[xml.AttrChangeSet,
                                                   xml.TagAddList],
                                main_config: types.YAMLDict,
                                cmdopts: types.Cmdopts) -> int:
    return ros1.callbacks.population_size_from_pickle(adds_def,
                                                      main_config,
                                                      cmdopts)


def population_size_from_def(exp_def: definition.XMLExpDef,
                             main_config: types.YAMLDict,
                             cmdopts: types.Cmdopts) -> int:
    return ros1.callbacks.population_size_from_def(exp_def,
                                                   main_config,
                                                   cmdopts)


def robot_prefix_extract(main_config: types.YAMLDict,
                         cmdopts: types.Cmdopts) -> str:
    return ros1.callbacks.robot_prefix_extract(main_config, cmdopts)


def pre_exp_diagnostics(cmdopts: types.Cmdopts,
                        logger: logging.Logger) -> None:
    s = "batch_exp_root='%s',runs/exp=%s,threads/job=%s,n_jobs=%s"
    logger.info(s,
                cmdopts['batch_root'],
                cmdopts['n_runs'],
                cmdopts['physics_n_threads'],
                cmdopts['exec_jobs_per_node'])
