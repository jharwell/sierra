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
import logging  # type: tp.Any
import typing as tp
import os
import subprocess
import pwd

# 3rd party packages
import implements
import yaml

# Project packages
from sierra.plugins.platform.rosrobot import cmdline
from sierra.core import xml, platform, config, ros, types, utils
from sierra.core.experiment import bindings
import sierra.core.variables.batch_criteria as bc


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
                 criteria: bc.IConcreteBatchCriteria,
                 n_robots: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.n_robots = n_robots
        self.exp_num = exp_num
        self.logger = logging.getLogger('platform.rosrobot')

    def pre_run_cmds(self,
                     host: str,
                     input_fpath: str,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:

        master_ip = platform.get_local_ip()
        port = config.kROS['port_base'] + self.exp_num
        master_uri = f'http://{master_ip}:{port}'

        ros_master = {
            'cmd': f'export ROS_MASTER_URI={master_uri};',
            'shell': True,
            'check': True,
            'wait': True,
        }

        if host == 'master':
            return [ros_master]

        main_path = os.path.join(self.cmdopts['project_config_root'],
                                 config.kYAML['main'])

        main_config = yaml.load(open(main_path), yaml.FullLoader)

        self.logger.debug("Generating pre-exec cmds for run%s slaves: %d robots",
                          run_num,
                          self.n_robots)

        script = main_config['ros']['robots'][self.cmdopts['robot']].get(
            'setup_script',
            "$HOME/.bashrc")

        ros_setup = {
            'cmd': f'. {script};',
            'shell': True,
            'check': True,
            'wait': True
        }

        return [ros_setup, ros_master]

    def exec_run_cmds(self,
                      host: str,
                      input_fpath: str,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        if host == 'master':
            return []

        self.logger.debug("Generating exec cmds for run%s slaves: %d robots",
                          run_num,
                          self.n_robots)

        nodes = platform.ExecEnvChecker.parse_nodefile(self.cmdopts['nodefile'])

        if len(nodes) < self.n_robots:
            self.logger.critical(("Need %d hosts to correctly generate launch "
                                  "cmds for run%s with %d robots; %d available"),
                                 self.n_robots,
                                 run_num,
                                 self.n_robots,
                                 len(nodes))

        ret = []
        for i in range(0, self.n_robots):
            ret.extend([

                # --wait tells roslaunch to wait for the configured master to
                # come up before launch the robot code.
                {
                    'cmd': '{0} --wait {1}_robot{2}{3};'.format(config.kROS['launch_cmd'],
                                                                input_fpath,
                                                                i,
                                                                config.kROS['launch_file_ext']),
                    'shell': True,
                    'check': True,
                    'wait': True
                }
            ])
        return ret

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        if host == 'master':
            return []
        else:
            return [
                {
                    'cmd': 'killall roslaunch;',
                    'check': False,
                    'shell': True,
                    'wait': True
                }
            ]


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num
        self.logger = logging.getLogger('platform.rosrobot')

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        local_ip = platform.get_local_ip()
        port = config.kROS['port_base'] + self.exp_num
        self.logger.info("Using ROS_MASTER_URI=%s:%s", local_ip, port)

        return[
            {
                # roscore will run on the SIERRA host machine.
                'cmd': f'export ROS_MASTER_URI={local_ip}:{port};',
                'shell': True,
                'check': True,
                'wait': True
            },
            {
                # Each experiment gets their own roscore. Because each roscore has a
                # different port, this prevents any robots from pre-emptively
                # starting the next experiment before the rest of the robots have
                # finished the current one.
                'cmd': f'roscore -p {port} & ',
                'shell': True,
                'check': False,
                'wait': False
            }
        ]

    def exec_exp_cmds(self, exec_opts: types.ExpExecOpts) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        # Cleanup roscore processes on the SIERRA host machine which are still
        # active because they don't know how to clean up after themselves.
        return [{
                'cmd': 'killall rosmaster;',
                'check': False,
                'shell': True,
                'wait': True
                },
                {
                'cmd': 'killall roscore;',
                'check': False,
                    'shell': True,
                    'wait': True
                },
                {
                'cmd': 'killall rosout;',
                'check': False,
                    'shell': True,
                    'wait': True
                }]


@implements.implements(bindings.IExpConfigurer)
class ExpConfigurer():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        self.logger = logging.getLogger('platform.rosrobot')

    def cmdfile_paradigm(self) -> str:
        return 'per-run'

    def for_exp_run(self, exp_input_root: str, run_output_root: str) -> None:
        pass

    def for_exp(self, exp_input_root: str) -> None:
        self.logger.info("Syncing experiment input files to robots")

        checker = platform.ExecEnvChecker(self.cmdopts)
        nodes = checker.parse_nodefile(self.cmdopts['nodefile'])

        for hostname in nodes:
            remote_login = nodes[hostname]['login']
            current_username = pwd.getpwuid(os.getuid())[0]
            checker.check_connectivity(nodes[hostname]['login'],
                                       hostname,
                                       self.cmdopts['robot'])

            # In case the user is different on the remote machine than this one,
            # and the location of the generated experiment is under /home.
            robot_input_root = exp_input_root.replace(current_username,
                                                      remote_login)

            mkdir_cmd = f"ssh {remote_login}@{hostname} mkdir -p {robot_input_root}"
            rsync_cmd = (f"rsync -avz -e ssh {exp_input_root}/ "
                         f"{remote_login}@{hostname}:{robot_input_root}/")
            self.logger.trace("Running rsync: %s", rsync_cmd)
            try:
                self.logger.trace("Running mkdir: %s", mkdir_cmd)
                subprocess.run(mkdir_cmd,
                               shell=True,
                               check=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
                self.logger.trace("Running rsync: %s", rsync_cmd)
                subprocess.run(rsync_cmd,
                               shell=True,
                               check=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                self.logger.fatal("Unable to sync %s with %s via ssh",
                                  exp_input_root,
                                  robot_input_root)
                raise


@implements.implements(bindings.IExecEnvChecker)
class ExecEnvChecker():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        pass

    def __call__(self) -> None:
        keys = ['ROS_DISTRO', 'ROS_VERSION']

        for k in keys:
            assert k in os.environ, \
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
