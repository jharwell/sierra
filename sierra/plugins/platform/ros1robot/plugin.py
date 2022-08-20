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
import subprocess
import pwd
import pathlib

# 3rd party packages
import implements
import yaml

# Project packages
from sierra.plugins.platform.ros1robot import cmdline
from sierra.core import platform, config, ros1, types, utils
from sierra.core.experiment import bindings, definition, xml
import sierra.core.variables.batch_criteria as bc


class CmdlineParserGenerator():
    def __call__(self) -> argparse.ArgumentParser:
        parent1 = ros1.cmdline.ROSCmdline([-1, 1, 2, 3, 4, 5]).parser
        return cmdline.PlatformCmdline(parents=[parent1],
                                       stages=[-1, 1, 2, 3, 4, 5]).parser


@implements.implements(bindings.IParsedCmdlineConfigurer)
class ParsedCmdlineConfigurer():
    def __init__(self, exec_env: str) -> None:
        self.exec_env = exec_env
        self.logger = logging.getLogger('platform.ros1robot')

    def __call__(self, args: argparse.Namespace) -> None:
        if args.nodefile is None:
            assert 'SIERRA_NODEFILE' in os.environ,\
                ("Non-ros1robot environment detected: --nodefile not "
                 "passed and 'SIERRA_NODEFILE' not found")
            args.nodefile = os.environ['SIERRA_NODEFILE']

        assert utils.path_exists(args.nodefile), \
            f"SIERRA_NODEFILE '{args.nodefile}' does not exist"
        self.logger.info("Using '%s' as robot hostnames file", args.nodefile)

        assert not args.platform_vc,\
            "Platform visual capture not supported on ros1robot"


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.BatchCriteria,
                 n_robots: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.n_robots = n_robots
        self.exp_num = exp_num
        self.criteria = criteria
        self.logger = logging.getLogger('platform.ros1robot')

    def pre_run_cmds(self,
                     host: str,
                     input_fpath: pathlib.Path,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:

        master_ip = platform.get_local_ip()
        port = config.kROS['port_base'] + self.exp_num
        master_uri = f'http://{master_ip}:{port}'

        ros_master = types.ShellCmdSpec(cmd=f'export ROS_MASTER_URI={master_uri};',
                                        shell=True,
                                        env=True,
                                        wait=True)

        if host == 'master':
            if self.cmdopts['no_master_node']:
                return []
            else:
                return [ros_master]

        main_path = os.path.join(self.cmdopts['project_config_root'],
                                 config.kYAML.main)

        main_config = yaml.load(utils.utf8open(main_path), yaml.FullLoader)

        self.logger.debug("Generating pre-exec cmds for run%s slaves: %d robots",
                          run_num,
                          self.n_robots)

        script_yaml = main_config['ros']['robots'][self.cmdopts['robot']]
        script_file = script_yaml.get('setup_script', "$HOME/.bashrc")

        ros_setup = types.ShellCmdSpec(cmd=f'. {script_file};',
                                       shell=True,
                                       wait=True,
                                       env=True)

        return [ros_setup, ros_master]

    def exec_run_cmds(self,
                      host: str,
                      input_fpath: pathlib.Path,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        if host == 'master':
            return self._exec_run_cmds_master(host, input_fpath, run_num)
        else:
            return self._exec_run_cmds_slave(host, input_fpath, run_num)

    def _exec_run_cmds_master(self,
                              host: str,
                              input_fpath: pathlib.Path,
                              run_num: int) -> tp.List[types.ShellCmdSpec]:

        if self.cmdopts['no_master_node']:
            return []

        self.logger.debug("Generating exec cmds for run%s master",
                          run_num)

        # ROS master node
        exp_dirname = self.criteria.gen_exp_names(self.cmdopts)[self.exp_num]
        exp_template_path = utils.exp_template_path(self.cmdopts,
                                                    self.criteria.batch_input_root,
                                                    exp_dirname)
        cmd = '{0} --wait {1}_run{2}_master{3};'

        cmd = cmd.format(config.kROS['launch_cmd'],
                         str(exp_template_path),
                         run_num,
                         config.kROS['launch_file_ext'])

        # --wait tells roslaunch to wait for the configured master to come up
        # before launch the "master" code.
        #
        # 2022/02/28: -p (apparently) tells roslaunch not to CONNECT to a master
        # at the specified ort, but to LAUNCH a new master at the specified
        # port. This is not really documented well.

        master_node = types.ShellCmdSpec(cmd=cmd, shell=True, wait=True)

        return [master_node]

    def _exec_run_cmds_slave(self,
                             host: str,
                             input_fpath: pathlib.Path,
                             run_num: int) -> tp.List[types.ShellCmdSpec]:

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

        ret = []  # type: tp.List[types.ShellCmdSpec]
        for i in range(0, self.n_robots):
            # --wait tells roslaunch to wait for the configured master to
            # come up before launch the robot code.
            cmd = '{0} --wait {1}_robot{2}{3} '
            cmd = cmd.format(config.kROS['launch_cmd'],
                             input_fpath,
                             i,
                             config.kROS['launch_file_ext'])
            ret.extend([types.ShellCmdSpec(cmd=cmd, shell=True, wait=True)])
        return ret

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        if host == 'master':
            return []
        else:
            return [
                types.ShellCmdSpec(
                    # Can't use killall, because that returns non-zero if things
                    # are cleaned up nicely.
                    cmd='if pgrep roslaunch; then pkill roslaunch; fi;',
                    shell=True,
                    wait=True
                )
            ]


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num
        self.logger = logging.getLogger('platform.ros1robot')

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        local_ip = platform.get_local_ip()
        port = config.kROS['port_base'] + self.exp_num
        master_uri = f'http://{local_ip}:{port}'

        self.logger.info("Using ROS_MASTER_URI=%s", master_uri)

        return[
            types.ShellCmdSpec(
                # roscore will run on the SIERRA host machine.
                cmd=f'export ROS_MASTER_URI={master_uri}',
                shell=True,
                env=True,
                wait=True),
            types.ShellCmdSpec(
                # Each exppperiment gets their own roscore. Because each roscore
                # has a  different port, this prevents any robots from
                # pre-emptively starting the next experiment before the rest of
                # the robots have finished the current one.
                cmd=f'roscore -p {port} & ',
                shell=True,
                wait=False)
        ]

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        # Cleanup roscore processes on the SIERRA host machine which are still
        # active because they don't know how to clean up after themselves.
        return [types.ShellCmdSpec(cmd='killall rosmaster;',
                                   shell=True,
                                   wait=True),
                types.ShellCmdSpec(cmd='killall roscore;',
                                   shell=True,
                                   wait=True),
                types.ShellCmdSpec(cmd='killall rosout;',
                                   shell=True,
                                   wait=True)]


@implements.implements(bindings.IExpConfigurer)
class ExpConfigurer():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        self.logger = logging.getLogger('platform.ros1robot')

    def cmdfile_paradigm(self) -> str:
        return 'per-run'

    def for_exp_run(self,
                    exp_input_root: pathlib.Path,
                    run_output_root: pathlib.Path) -> None:
        pass

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        if self.cmdopts['skip_sync']:
            self.logger.info("Skipping syncing experiment inputs -> robots")
            return
        else:
            self.logger.info("Syncing experiment inputs  -> robots")

        checker = platform.ExecEnvChecker(self.cmdopts)
        nodes = checker.parse_nodefile(self.cmdopts['nodefile'])

        # Use parallel ssh, rsync to push each experiment to all robots in
        # parallel--takes O(M*N) operation and makes it O(N) more or less.
        pssh_base = 'parallel-ssh'
        prsync_base = 'parallel-rsync'

        for node in nodes:
            remote_login = node.login
            remote_port = node.port
            remote_hostname = node.hostname
            current_username = pwd.getpwuid(os.getuid())[0]

            if not self.cmdopts['skip_online_check']:
                checker.check_connectivity(remote_login,
                                           remote_hostname,
                                           remote_port,
                                           self.cmdopts['robot'])

            pssh_base += f' -H {remote_login}@{remote_hostname}:{remote_port}'
            prsync_base += f' -H {remote_login}@{remote_hostname}:{remote_port}'

        # In case the user is different on the remote machine than this one,
        # and the location of the generated experiment is under /home.
        robot_input_root = str(exp_input_root).replace(current_username,
                                                       remote_login)

        mkdir_cmd = (f"{pssh_base} "
                     f"-O StrictHostKeyChecking=no "
                     f"mkdir -p {robot_input_root}")

        rsync_cmd = (f"{prsync_base} "
                     f"-avz "
                     f"-O StrictHostKeyChecking=no "
                     f"{exp_input_root}/ "
                     f"{robot_input_root}/")
        try:
            self.logger.trace("Running mkdir: %s", mkdir_cmd)  # type: ignore
            res = subprocess.run(mkdir_cmd,
                                 shell=True,
                                 check=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            self.logger.trace("Running rsync: %s", rsync_cmd)  # type: ignore
            res = subprocess.run(rsync_cmd,
                                 shell=True,
                                 check=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            self.logger.fatal("Unable to sync %s with %s: stdout=%s,stderr=%s",
                              exp_input_root,
                              robot_input_root,
                              res.stdout.decode('utf-8'),
                              res.stderr.decode('utf-8'))
            raise


@ implements.implements(bindings.IExecEnvChecker)
class ExecEnvChecker():
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        pass

    def __call__(self) -> None:
        keys = ['ROS_DISTRO', 'ROS_VERSION']

        for k in keys:
            assert k in os.environ, \
                "Non-ROS1+robot environment detected: '{0}' not found".format(
                    k)

        # Check ROS distro
        assert os.environ['ROS_DISTRO'] in ['kinetic', 'noetic'],\
            "SIERRA only supports ROS1 kinetic,noetic"

        # Check ROS version
        assert os.environ['ROS_VERSION'] == "1",\
            "Wrong ROS version: This plugin is for ROS1"


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
    s = "batch_exp_root='%s',runs/exp=%s"
    logger.info(s,
                cmdopts['batch_root'],
                cmdopts['n_runs'])
