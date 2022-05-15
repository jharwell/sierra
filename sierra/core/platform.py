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
import argparse
import socket
import logging
import pwd
import re

# 3rd party packages
import implements
import netifaces

# Project packages
import sierra.core.plugin_manager as pm
from sierra.core import config, types, utils
from sierra.core.experiment import bindings
import sierra.core.variables.batch_criteria as bc


class CmdlineParserGenerator():
    """
    Dispatcher to generate additional cmdline arguments which are dependent on
    the selected ``--platform``.
    """

    def __init__(self, platform: str) -> None:
        module = pm.pipeline.get_plugin_module(platform)
        self.platform = module.CmdlineParserGenerator()

    def __call__(self) -> argparse.ArgumentParser:
        return self.platform()


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    """
    Trampoline class for dispatching cmd generation to platforms and/or
    execution environments.

    Called during stage 1 to add shell commands which should be run immediately
    before and after the shell command to actually execute a single
    :term:`Experimental Run` to the commands file to be fed to whatever the
    tool a given execution environment environment uses to run cmds (e.g., GNU
    parallel).
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.IConcreteBatchCriteria,
                 n_robots: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.criteria = criteria
        module = pm.pipeline.get_plugin_module(
            self.cmdopts['platform'])
        self.platform = module.ExpRunShellCmdsGenerator(self.cmdopts,
                                                        self.criteria,
                                                        n_robots,
                                                        exp_num)
        module = pm.pipeline.get_plugin_module(
            self.cmdopts['exec_env'])
        self.env = module.ExpRunShellCmdsGenerator(self.cmdopts,
                                                   self.criteria,
                                                   n_robots,
                                                   exp_num)

    def pre_run_cmds(self,
                     host: str,
                     input_fpath: str,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        cmds = self.platform.pre_run_cmds(host, input_fpath, run_num)
        cmds.extend(self.env.pre_run_cmds(host, input_fpath, run_num))
        return cmds

    def exec_run_cmds(self,
                      host: str,
                      input_fpath: str,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        cmds = self.platform.exec_run_cmds(host, input_fpath, run_num)
        cmds.extend(self.env.exec_run_cmds(host, input_fpath, run_num))
        return cmds

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        cmds = self.platform.post_run_cmds(host)
        cmds.extend(self.env.post_run_cmds(host))
        return cmds


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """Trampoline class for dispatching shell cmd generation to platforms and/or
    execute environments.

    Called during stage 2 to run shell commands immediately before running a
    given :term:`Experiment`, to run shell commands to actually run the
    experiment, and to run shell commands immediately after the experiment
    finishes.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        module = pm.pipeline.get_plugin_module(
            self.cmdopts['platform'])
        self.platform = module.ExpShellCmdsGenerator(self.cmdopts,
                                                     exp_num)
        module = pm.pipeline.get_plugin_module(
            self.cmdopts['exec_env'])
        self.env = module.ExpShellCmdsGenerator(self.cmdopts,
                                                exp_num)

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        cmds = self.platform.pre_exp_cmds()
        cmds.extend(self.env.pre_exp_cmds())
        return cmds

    def exec_exp_cmds(self, exec_opts: types.ExpExecOpts) -> tp.List[types.ShellCmdSpec]:
        cmds = self.platform.exec_exp_cmds(exec_opts)
        cmds.extend(self.env.exec_exp_cmds(exec_opts))
        return cmds

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        cmds = self.platform.post_exp_cmds()
        cmds.extend(self.env.post_exp_cmds())
        return cmds


class ParsedCmdlineConfigurer():
    """
    Dispatcher for configuring the main cmdopts dictionary for the selected
    platform and execution environment.

    Called before the pipeline starts to add new/modify existing cmdline
    arguments after initial parsing.
    """

    def __init__(self,
                 platform: str,
                 exec_env: str) -> None:
        self.platform = platform
        self.exec_env = exec_env
        self.logger = logging.getLogger(__name__)

        module = pm.pipeline.get_plugin_module(self.platform)
        self.platformg = module.ParsedCmdlineConfigurer(exec_env)

        module = pm.pipeline.get_plugin_module(self.exec_env)
        self.envg = module.ParsedCmdlineConfigurer(exec_env)

    def __call__(self, args: argparse.Namespace) -> argparse.Namespace:
        # Configure for selected execution enivornment first, to check for
        # low-level details.
        self.logger.debug("Configuring cmdline from --exec_env=%s",
                          self.exec_env)
        args.__dict__['exec_env'] = self.exec_env
        self.envg(args)

        # Configure for selected platform
        self.logger.debug("Configuring cmdline from --platform=%s",
                          self.platform)
        args.__dict__['platform'] = self.platform
        self.platformg(args)

        return args


class ExpConfigurer():
    """
    Perform platform-specific configuration for a given experimental run that
    you can do programmatically (i.e., without needing a shell). This usually is
    things like creating directories, etc.

    Called at the end of stage 1 during configuring a specific
    :term:`Experimental Run`.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        module = pm.pipeline.get_plugin_module(cmdopts['platform'])
        self.platform = module.ExpConfigurer(self.cmdopts)

    def for_exp_run(self, exp_input_root: str, run_output_dir: str) -> None:
        self.platform.for_exp_run(exp_input_root, run_output_dir)

    def for_exp(self, exp_input_root: str) -> None:
        self.platform.for_exp(exp_input_root)

    def cmdfile_paradigm(self) -> str:
        return self.platform.cmdfile_paradigm()


class ExecEnvChecker():
    """
    Verify the configured ``--exec-env` for the configured ``--platform`` before
    running any experiments during stage 2. This is needed in addition to the
    checks performed during stage 1, because stage 2 can be run on its own
    without running stage 1 first on the same SIERRA invocation.

    """

    @staticmethod
    def parse_nodefile(nodefile: str) -> tp.Set[tp.Dict]:
        ret = []

        with open(nodefile, 'r') as f:
            lines = f.readlines()

            for line in lines:
                comment_re = r"^#"
                if res := re.search(comment_re, line):
                    continue

                cores_re = r"^[0-9]+/"
                if res := re.search(cores_re, line):
                    cores, ssh = line.split('/')
                else:
                    cores = 1
                    ssh = line

                identifier_re = r"[a-zA-Z0-9_.]+"
                port_re = r"ssh -p\s*([0-9]+)"
                username_at_host_re = f"({identifier_re})+@({identifier_re})"
                port_and_username_at_host_re = port_re + r"\*s" + username_at_host_re
                port_and_hostname_re = port_re + rf"\s+({identifier_re})"

                if res := re.search(port_and_username_at_host_re, ssh):
                    # They specified the port AND 'username@host'
                    port = int(res.group(1))
                    login = res.group(2)
                    hostname = res.group(3)
                elif res := re.search(port_and_hostname_re, ssh):
                    # They only specified the port and hostname
                    port = int(res.group(1))
                    hostname = res.group(2)
                    login = pwd.getpwuid(os.getuid())[0]
                elif res := re.search(username_at_host_re, ssh):
                    # They only specified 'username@host'
                    port = 22
                    login = res.group(1)
                    hostname = res.group(2)
                elif res := re.search(identifier_re, ssh):
                    # They only specified the hostname
                    port = 22
                    login = pwd.getpwuid(os.getuid())[0]
                    hostname = res.group(0)
                else:
                    raise ValueError(f"Bad ssh/hostname spec {ssh}")

                ret.append({
                    'hostname': hostname,
                    'n_cores': cores,
                    'login': login,
                    'port': port
                })
        return ret

    def __init__(self, cmdopts: types.Cmdopts):
        self.cmdopts = cmdopts
        self.exec_env = self.cmdopts['exec_env']
        self.platform = self.cmdopts['platform']
        self.logger = logging.getLogger(__name__)

    def __call__(self) -> None:
        module = pm.pipeline.get_plugin_module(
            self.cmdopts['platform'])
        module.ExecEnvChecker(self.cmdopts)()
        module = pm.pipeline.get_plugin_module(
            self.cmdopts['exec_env'])
        module.ExecEnvChecker(self.cmdopts)()

    def check_connectivity(self,
                           login: str,
                           hostname: str,
                           port: int,
                           host_type: str) -> bool:
        self.logger.info("Checking connectivity to %s", hostname)
        ssh_diag = f"{host_type},port={port} via {login}@{hostname}"
        nc_diag = f"{host_type},port={port} via {hostname}"

        if self.cmdopts['online_check_method'] == 'ping+ssh':
            try:
                self.logger.debug("Attempt to ping %s, type=%s",
                                  hostname,
                                  host_type)
                timeout = config.kPlatform['ping_timeout']
                subprocess.run(f"ping -c 3 -W {timeout} {hostname}",
                               shell=True,
                               check=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                self.logger.fatal("Unable to ping %s, type=%s",
                                  hostname,
                                  host_type)
                raise
            self.logger.debug("%s is alive, type=%s", hostname, host_type)
        elif self.cmdopts['online_check_method'] == 'nc+ssh':
            try:
                self.logger.debug("Check for ssh tunnel to %s", nc_diag)
                timeout = config.kPlatform['ping_timeout']
                subprocess.run(f"nc -z {hostname} {port}",
                               shell=True,
                               check=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            except subprocess.CalledProcessError:
                self.logger.fatal("No ssh tunnel to %s", nc_diag)
                raise
            self.logger.debug("ssh tunnel to %s alive", nc_diag)

        try:

            self.logger.debug("Verify ssh to %s", ssh_diag)
            subprocess.run((f"ssh -p{port} "
                            "-o PasswordAuthentication=no "
                            "-o StrictHostKeyChecking=no "
                            "-o BatchMode=yes "
                            f"{login}@{hostname} exit"),
                           shell=True,
                           check=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
        except subprocess.CalledProcessError:
            self.logger.fatal("Unable to connect to %s", ssh_diag)
            raise
        self.logger.info("%s@%s online", host_type, hostname)

    def check_for_simulator(self, name: str):
        if self.exec_env in ['hpc.local', 'hpc.adhoc']:
            shellname: str = name
        elif self.exec_env in ['hpc.pbs', 'hpc.slurm']:
            arch = os.environ.get('SIERRA_ARCH')
            shellname: str = '{0}-{1}'.format(name, arch)
        else:
            assert False, \
                "Bad --exec-env '{0}' for platform '{1}'".format(self.exec_env,
                                                                 self.platform)

        version_cmd = f'{shellname} -v'
        self.logger.debug("Check version for '%s' via '%s'",
                          shellname,
                          version_cmd)

        if shutil.which(shellname):
            res = subprocess.run(version_cmd,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 shell=True)
            return res
        else:
            assert False, \
                "Bad --exec-env '{0}' for platform '{1}': cannot find '{2}'".format(self.exec_env,
                                                                                    self.platform,
                                                                                    name)
            return None


def get_free_port() -> int:
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


def get_local_ip():
    """
    Get the local IP address of the SIERRA host machine.
    """
    active = []
    for iface in netifaces.interfaces():
        # Active=has a normal IP address (that's what AF_INET means)
        if socket.AF_INET in netifaces.ifaddresses(iface):
            active.append(iface)

    active = list(filter('lo'.__ne__, active))

    if len(active) > 1:
        logging.warning(("SIERRA host machine has > 1 non-loopback IP addresses"
                         "/network interfaces--SIERRA may select the wrong "
                         "one: %s"), active)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


__api__ = [
    'CmdlineParserGenerator',
    'ParsedCmdlineConfigurer',
    'ExpRunLaunchCmdGenerator',
    'ExpCmdsGenerator',
    'HPCEnvChecker',
]
