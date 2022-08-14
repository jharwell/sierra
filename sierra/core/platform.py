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
"""Terminal interface for pltaform plugins.

Classes for generating the commands to run :term:`experiments <Batch
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
import pathlib

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
    Dispatcher to generate additional platform-dependent cmdline arguments.
    """

    def __init__(self, platform: str) -> None:
        module = pm.pipeline.get_plugin_module(platform)
        self.platform = module.CmdlineParserGenerator()

    def __call__(self) -> argparse.ArgumentParser:
        return self.platform()


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    """Dispatcher for shell cmd generation for an :term:`Experimental Run`.

    Dispatches generation to the selected platform and execution environment.
    Called during stage 1 to add shell commands which should be run immediately
    before and after the shell command to actually execute a single
    :term:`Experimental Run` to the commands file to be fed to whatever the tool
    a given execution environment environment uses to run cmds (e.g., GNU
    parallel).

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.BatchCriteria,
                 n_robots: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.criteria = criteria
        module = pm.pipeline.get_plugin_module(self.cmdopts['platform'])

        if hasattr(module, 'ExpRunShellCmdsGenerator'):
            self.platform = module.ExpRunShellCmdsGenerator(self.cmdopts,
                                                            self.criteria,
                                                            n_robots,
                                                            exp_num)
        else:
            self.platform = None

        module = pm.pipeline.get_plugin_module(self.cmdopts['exec_env'])
        if hasattr(module, 'ExpRunShellCmdsGenerator'):
            self.env = module.ExpRunShellCmdsGenerator(self.cmdopts,
                                                       self.criteria,
                                                       n_robots,
                                                       exp_num)
        else:
            self.env = None

    def pre_run_cmds(self,
                     host: str,
                     input_fpath: pathlib.Path,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        cmds = []
        if self.platform:
            cmds.extend(self.platform.pre_run_cmds(host, input_fpath, run_num))

        if self.env:
            cmds.extend(self.env.pre_run_cmds(host, input_fpath, run_num))

        return cmds

    def exec_run_cmds(self,
                      host: str,
                      input_fpath: pathlib.Path,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.exec_run_cmds(host, input_fpath, run_num))

        if self.env:
            cmds.extend(self.env.exec_run_cmds(host, input_fpath, run_num))

        return cmds

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.post_run_cmds(host))

        if self.env:
            cmds.extend(self.env.post_run_cmds(host))

        return cmds


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """Dispatcher for shell cmd generation for an :term:`Experiment`.

    Dispatches generation to the selected platform and execution environment.
    Called during stage 2 to run shell commands immediately before running a
    given :term:`Experiment`, to run shell commands to actually run the
    experiment, and to run shell commands immediately after the experiment
    finishes.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

        module = pm.pipeline.get_plugin_module(self.cmdopts['platform'])
        if hasattr(module, 'ExpShellCmdsGenerator'):
            self.logger.debug(("Skipping generating experiment shell commands "
                               "for --platform=%s"),
                              self.cmdopts['platform'])

            self.platform = module.ExpShellCmdsGenerator(self.cmdopts,
                                                         exp_num)
        else:
            self.platform = None

        module = pm.pipeline.get_plugin_module(self.cmdopts['exec_env'])
        if hasattr(module, 'ExpShellCmdsGenerator'):
            self.logger.debug(("Skipping generating experiment shell commands "
                               "for --exec-env=%s"),
                              self.cmdopts['exec_env'])

            self.env = module.ExpShellCmdsGenerator(self.cmdopts,
                                                    exp_num)
        else:
            self.env = None

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.pre_exp_cmds())

        if self.env:
            cmds.extend(self.env.pre_exp_cmds())

        return cmds

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.exec_exp_cmds(exec_opts))

        if self.env:
            cmds.extend(self.env.exec_exp_cmds(exec_opts))

        return cmds

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.post_exp_cmds())

        if self.env:
            cmds.extend(self.env.post_exp_cmds())

        return cmds


class ParsedCmdlineConfigurer():
    """Dispatcher for configuring the cmdopts dictionary.

    Dispatches configuring to the selected platform and execution environment.
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
        if hasattr(module, 'ParsedCmdlineConfigurer'):
            self.platformg = module.ParsedCmdlineConfigurer(exec_env)
        else:
            self.platformg = None
            self.logger.debug("Skipping configuring cmdline from --platform=%s",
                              self.platform)

        module = pm.pipeline.get_plugin_module(self.exec_env)
        if hasattr(module, 'ParsedCmdlineConfigurer'):
            self.envg = module.ParsedCmdlineConfigurer(exec_env)
        else:
            self.envg = None
            self.logger.debug("Skipping configuring cmdline from --exec-env=%s",
                              self.exec_env)

    def __call__(self, args: argparse.Namespace) -> argparse.Namespace:
        # Configure for selected execution enivornment first, to check for
        # low-level details.
        args.__dict__['exec_env'] = self.exec_env

        if self.envg:
            self.envg(args)

        # Configure for selected platform
        args.__dict__['platform'] = self.platform

        if self.platformg:
            self.platformg(args)

        return args


class ExpConfigurer():
    """Perform platform-specific configuration for an :term:`Experimental Run`.

    For things can do programmatically (i.e., without needing a shell). This
    usually is things like creating directories, etc.  Called at the end of
    stage 1 during for each experimental run.

    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        module = pm.pipeline.get_plugin_module(cmdopts['platform'])
        self.platform = module.ExpConfigurer(self.cmdopts)

    def for_exp_run(self,
                    exp_input_root: pathlib.Path,
                    run_output_dir: pathlib.Path) -> None:
        self.platform.for_exp_run(exp_input_root, run_output_dir)

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        self.platform.for_exp(exp_input_root)

    def cmdfile_paradigm(self) -> str:
        return self.platform.cmdfile_paradigm()


class ExecEnvChecker():
    """Base class for verifying execution environments before running experiments.

    Platforms and/or execution environments needed to perform verification
    should derive from this class to use the common functionality present in it.

    """

    @staticmethod
    def parse_nodefile(nodefile: str) -> tp.List[types.ParsedNodefileSpec]:
        ret = []

        with utils.utf8open(nodefile, 'r') as f:
            lines = f.readlines()

            for line in lines:
                if parsed := ExecEnvChecker._parse_nodefile_line(line):
                    ret.append(parsed)

        return ret

    @staticmethod
    def _parse_nodefile_line(line: str) -> tp.Optional[types.ParsedNodefileSpec]:
        # Line starts with a comment--no parsing needed
        comment_re = r"^#"
        if res := re.search(comment_re, line):
            return None

        cores_re = r"^[0-9]+/"
        if res := re.search(cores_re, line):
            cores = int(line.split('/')[0])
            ssh = line.split('/')[1]
        else:
            cores = 1
            ssh = line

        identifier_re = r"[a-zA-Z0-9_.:]+"
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

        return types.ParsedNodefileSpec(hostname=hostname,
                                        n_cores=cores,
                                        login=login,
                                        port=port)

    def __init__(self, cmdopts: types.Cmdopts):
        self.cmdopts = cmdopts
        self.exec_env = self.cmdopts['exec_env']
        self.platform = self.cmdopts['platform']
        self.logger = logging.getLogger(__name__)

    def __call__(self) -> None:
        module = pm.pipeline.get_plugin_module(self.cmdopts['platform'])
        if hasattr(module, 'ExecEnvChecker'):
            module.ExecEnvChecker(self.cmdopts)()

        module = pm.pipeline.get_plugin_module(self.cmdopts['exec_env'])
        if hasattr(module, 'ExecEnvChecker'):
            module.ExecEnvChecker(self.cmdopts)()

    def check_connectivity(self,
                           login: str,
                           hostname: str,
                           port: int,
                           host_type: str) -> None:
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
        shellname = get_executable_shellname(name)

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
            error = "Bad --exec-env '{0}' for platform '{1}': cannot find '{2}'".format(self.exec_env,
                                                                                        self.platform,
                                                                                        name)
            raise RuntimeError(error)


def get_executable_shellname(base: str) -> str:
    if 'SIERRA_ARCH' in os.environ:
        arch = os.environ['SIERRA_ARCH']
        return f'{base}-{arch}'
    else:
        return base


def get_free_port() -> int:
    """Determine a free port using sockets.

    From
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
        logging.critical(("SIERRA host machine has > 1 non-loopback IP addresses"
                          "/network interfaces--SIERRA may select the wrong "
                          "one: %s"), active)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


__api__ = [
    'CmdlineParserGenerator',
    'ExpRunShellCmdsGenerator',
    'ExpShellCmdsGenerator',
    'ParsedCmdlineConfigurer',
    'ExpRunShellCmdsGenerator',
    'ExpShellCmdsGenerator',
    'ExecEnvChecker',
]
