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

# Core packages
import argparse
import logging
import typing as tp
import os

# 3rd party packages
import implements
import packaging.version

# Project packages
from sierra.plugins.platform.rosrobot import cmdline
from sierra.core import xml, platform, config, ros, types
from sierra.core.experiment import bindings

kROSCORE_PORT_START = 11235
"""
Port number to start allocating roscore processes at.
"""


class CmdlineParserGenerator():
    def __call__(self) -> argparse.ArgumentParser:
        parent1 = ros.cmdline.ROSCmdline([-1, 1, 2, 3, 4, 5]).parser
        return cmdline.PlatformCmdline(parents=[parent1],
                                       stages=[-1, 1, 2, 3, 4, 5]).parser


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    def __init__(self, exec_env: str) -> None:
        self.exec_env = exec_env
        self.logger = logging.getLogger('platform.rosrobot')

    def __call__(self, args: argparse.Namespace) -> None:
        pass


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 n_robots: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.n_robots = n_robots
        self.exp_num = exp_num
        self.logger = logging.getLogger('platform.rosrobot')

    def pre_run_cmds(self,
                     input_fpath: str,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_run_cmds(self,
                      input_fpath: str,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        local_ip = platform.get_local_ip()
        self.logger.debug("Using ROS_IP=%s", local_ip)

        # First, the cmd to start roscore, on THIS (the host) machine. We don't
        # really need to be on a unique port so that multiple ROS instances can
        # be running.
        roscore_port = (kROSCORE_PORT_START + self.exp_num)

        ret = []

        for _ in range(0, self.n_robots):
            ret.extend([
                {
                    # ROS core runs on SIERRA host machine; all robot nodes are
                    # slaves. We need to set ROS_IP in the case the host machine
                    # has multiple IP addresses.
                    'cmd': f'export ROS_IP={local_ip};',
                    'shell': True,
                    'check': True
                },

                # --wait tells roslaunch to wait for the configured master to
                # come up before launch the robot code.
                {
                    'cmd': '{0} --wait -p {1} {2}{3};\n'.format(config.kROS['launch_cmd'],
                                                                roscore_port,
                                                                input_fpath,
                                                                config.kROS['launch_file_ext']),
                    'shell': True,
                    'check': True
                }
            ])
        return ret

    def post_run_cmds(self) -> tp.List[types.ShellCmdSpec]:
        prompt = ("Once the robots and environment are "
                  "reset/setup for the next run, press any key to continue... ")
        return [
            {
                'cmd': f"read -p {prompt} c",
                'shell': True,
                'check': False
            }
        ]


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        local_ip = platform.get_local_ip()
        port = kROSCORE_PORT_START + self.exp_num
        return[{
            # roscore will run on the SIERRA host machine.
            'cmd': f'export ROS_MASTER_URI={local_ip}:{port};',
            'shell': True,
            'check': True
        },
            {
            # Each experiment gets their own roscore. Because each roscore has a
            # different port, this prevents any robots from pre-emptively
            # starting the next experiment before the rest of the robots have
            # finished the current one.
            'cmd': 'roscore -p {roscore_port} &',
            'shell': True,
            'check': True
        },
        ]

        return []

    def exec_exp_cmds(self, exec_opts: types.ExpExecOpts) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        # Cleanup roscore processes on the SIERRA host machine which are still
        # active because they don't know how to clean up after themselves.
        return [{
                'cmd': 'killall rosmaster;',
                'check': False,
                'shell': True
                },
                {
                'cmd': 'killall roscore;',
                'check': False,
                'shell': True
                },
                {
                'cmd': 'killall rosout;',
                'check': False,
                'shell': True
                }]


@implements.implements(bindings.IExpRunConfigurer)
class ExpRunConfigurer():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

    def __call__(self, run_output_dir: str) -> None:
        pass


@implements.implements(bindings.IExecEnvChecker)
class ExecEnvChecker():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        pass

    def __call__(self) -> None:
        keys = ['ROS_DISTRO', 'ROS_VERSION']

        for k in keys:
            assert k in os.environ,\
                "Non-ROS+robot environment detected: '{0}' not found".format(
                    k)

        # Check ROS distro
        assert os.environ['ROS_DISTRO'] in ['melodic', 'noetic'],\
            "SIERRA only supports ROS melodic and noetic"

        # Check ROS version
        assert os.environ['ROS_VERSION'] == "1",\
            "SIERRA only supports ROS 1"


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
    s = "batch_exp_root='%s',runs/exp=%s"
    logger.info(s,
                cmdopts['batch_root'],
                cmdopts['n_runs'])
