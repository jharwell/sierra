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
Provides platform-specific callbacks for the :term:`ROS+Gazebo` platform.
"""
# Core packages
import argparse
import logging
import multiprocessing
import os
import re
import typing as tp

# 3rd party packages
import packaging.version
import implements

# Project packages
from sierra.plugins.platform.rosgazebo import cmdline
from sierra.core import hpc, xml, platform, config, ros, types
from sierra.core.experiment import bindings


class CmdlineParserGenerator():
    def __call__(self) -> argparse.ArgumentParser:
        parent1 = hpc.cmdline.HPCCmdline([-1, 1, 2, 3, 4, 5]).parser
        parent2 = ros.cmdline.ROSCmdline([-1, 1, 2, 3, 4, 5]).parser
        return cmdline.PlatformCmdline(parents=[parent1, parent2],
                                       stages=[-1, 1, 2, 3, 4, 5]).parser


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    def __init__(self, exec_env: str) -> None:
        self.exec_env = exec_env
        self.logger = logging.getLogger('rosgazebo.plugin')

    def __call__(self, args: argparse.Namespace) -> None:
        if self.exec_env == 'hpc.local':
            self._hpc_local(args)
        elif self.exec_env == 'hpc.adhoc':
            self._hpc_adhoc(args)
        elif self.exec_env == 'hpc.slurm':
            self._hpc_slurm(args)
        elif self.exec_env == 'hpc.pbs':
            self._hpc_pbs(args)
        else:
            assert False,\
                f"'{self.exec_env}' unsupported on Ros+Gazebo"

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
        with open(args.nodefile, 'r') as f:
            lines = f.readlines()
            n_nodes = len(lines)

            ppn = 0
            for line in lines:
                ppn = min(ppn, int(line.split('/')[0]))

        if args.exec_jobs_per_node is None:
            args.exec_jobs_per_node = int(float(args.n_runs) / n_nodes)

        self.logger.debug("Allocated %s physics threads/run, %s parallel runs/node",
                          args.physics_n_threads,
                          args.exec_jobs_per_node)

    def _hpc_local(self, args: argparse.Namespace) -> None:
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


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 n_robots: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.gazebo_port = -1
        self.roscore_port = -1

        assert self.cmdopts['exec_env'] in ['hpc.local'],\
            "Unsupported exec environment '{0}'".format(
                self.cmdopts['exec_env'])

    def pre_run_cmds(self,
                     input_fpath: str,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        # First, the cmd to start roscore. We need to be on a unique port so
        # that multiple ROS instances corresponding to multiple Gazebo
        # instances with the same topic names are considered distinct/not
        # accessible between instances of Gazebo.
        self.roscore_port = platform.get_free_port()

        # Second, the command to start Gazebo via roslaunch. We need to be on a
        # unique port so that multiple Gazebo instances can be run in
        # parallel. Note the -p argument to start a NEW roscore instance on the
        # current machine with the selected port.
        self.gazebo_port = platform.get_free_port()

        # 2021/12/13: You can't use HTTPS for some reason or gazebo won't
        # start...
        export_ros = f'export ROS_MASTER_URI=http://localhost:{self.roscore_port};'
        export_gazebo = f'export GAZEBO_MASTER_URI=http://localhost:{self.gazebo_port};'

        return [{'cmd': export_ros, 'shell': True, 'check': True},
                {'cmd': export_gazebo, 'shell': True, 'check': True}]

    def exec_run_cmds(self,
                      input_fpath: str,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        # --wait tells roslaunch to wait for the configured master to come up
        # before launch the robot code.
        roslaunch = '{0} --wait -p {1} {2}{3}'.format(config.kROS['launch_cmd'],
                                                      self.roscore_port,
                                                      input_fpath,
                                                      config.kROS['launch_file_ext'])

        return [{'cmd': roslaunch, 'shell': True, 'check': True}]

    def post_run_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.ExpExecOpts) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        # Cleanup roscore and gazebo processes which are still active because
        # they don't know how to clean up after themselves.
        return [{
                'cmd': 'killall gzserver',
                'check': False,
                'shell': True
                },
                {
                'cmd': 'killall rosmaster',
                'check': False,
                'shell': True
                },
                {
                'cmd': 'killall roscore',
                'check': False,
                'shell': True
                },
                {
                'cmd': 'killall rosout',
                'check': False,
                'shell': True
                }]


class ExpRunConfigurer():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

    def __call__(self, run_output_dir: str) -> None:
        pass


class ExecEnvChecker(platform.ExecEnvChecker):
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        super().__init__(cmdopts)

    def __call__(self) -> None:
        keys = ['ROS_DISTRO', 'GAZEBO_MASTER_URI', 'ROS_VERSION']

        for k in keys:
            assert k in os.environ,\
                "Non-ROS+Gazebo environment detected: '{0}' not found".format(
                    k)

        # Check ROS distro
        assert os.environ['ROS_DISTRO'] in ['melodic', 'noetic'],\
            "SIERRA only supports ROS melodic and noetic"

        # Check ROS version
        assert os.environ['ROS_VERSION'] == "1",\
            "SIERRA only supports ROS 1"

        # Check we can find Gazebo
        version = self.check_for_simulator(config.kGazebo['launch_cmd'])

        # Check Gazebo version
        res = re.search(r'[0-9]+.[0-9]+.[0-9]+', version.stdout.decode('utf-8'))
        assert res is not None, "Gazebo version not in -v output"

        version = packaging.version.parse(res.group(0))
        min_version = packaging.version.parse(config.kGazebo['min_version'])

        assert version >= min_version,\
            "Gazebo version {0} < min required {1}".format(version,
                                                           min_version)


def population_size_from_pickle(adds_def: tp.Union[xml.XMLAttrChangeSet,
                                                   xml.XMLTagAddList],
                                main_config: types.YAMLDict,
                                cmdopts: types.Cmdopts) -> int:
    return ros.callbacks.population_size_from_pickle(adds_def,
                                                     main_config,
                                                     cmdopts)


def population_size_from_def(exp_def: tp.Union[xml.XMLAttrChangeSet,
                                               xml.XMLTagAddList],
                             main_config: types.YAMLDict,
                             cmdopts: types.Cmdopts) -> int:
    return ros.callbacks.population_size_from_def(exp_def,
                                                  main_config,
                                                  cmdopts)


def robot_prefix_extract(main_config: types.YAMLDict,
                         cmdopts: types.Cmdopts) -> str:
    return ros.callbacks.robot_prefix_extract(main_config, cmdopts)


def pre_exp_diagnostics(cmdopts: types.Cmdopts,
                        logger: logging.Logger) -> None:
    s = "batch_exp_root='%s',runs/exp=%s,threads/job=%s,n_jobs=%s"
    logger.info(s,
                cmdopts['batch_root'],
                cmdopts['n_runs'],
                cmdopts['physics_n_threads'],
                cmdopts['exec_jobs_per_node'])
