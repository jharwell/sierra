# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Terminal interface for pltaform plugins.

Classes for generating the commands to run :term:`experiments <Batch
Experiment>` on multiple :term:`platforms <Platform>` using multiple execution
methods.

"""

# Core packages
import typing as tp
import argparse
import socket
import logging
import pathlib

# 3rd party packages
import implements
import netifaces

# Project packages
import sierra.core.plugin_manager as pm
from sierra.core import types
from sierra.core.experiment import bindings
import sierra.core.variables.batch_criteria as bc

_logger = logging.getLogger(__name__)


def cmdline_parser(platform: str) -> tp.Optional[argparse.ArgumentParser]:
    """
    Dispatches cmdline parser creation to selected platform.

    If the selected platform does not define a cmdline, None is returned.
    """
    module = pm.pipeline.get_plugin_module(platform)
    if hasattr(module, 'cmdline_parser'):
        return module.cmdline_parser()

    return None


def cmdline_postparse_configure(platform: str,
                                exec_env: str,
                                args: argparse.Namespace) -> argparse.Namespace:
    """Dispatcher for configuring the cmdopts dictionary.

    Dispatches configuring to the selected ``--platform`` and ``--exec-env``.
    Called before the pipeline starts to add modify existing cmdline arguments
    after initial parsing.  ``platform`` and ``exec_env`` are needed as
    arguments as they are not present in ``args``; they are "bootstrap" cmdline
    args needed to be parsed first to build the parser for the set of cmdline
    arguments accepted.
    """
    # Configure for selected platform
    args.__dict__['platform'] = platform
    module = pm.pipeline.get_plugin_module(platform)

    if hasattr(module, 'cmdline_postparse_configure'):
        args = module.cmdline_postparse_configure(exec_env, args)
    else:
        _logger.debug(("Skipping configuring cmdline from --platform='%s': "
                      "does not define hook"),
                      platform)

    return args


def exec_env_check(cmdopts: types.Cmdopts) -> None:
    """Dispatcher for verifying execution environments in stage 2.

    This is required because what is needed to create experiments in stage 1 for
    a platform is not necessarily the same as what is needed (in terms of
    envvars, daemons, etc.) when running them.

    """
    module = pm.pipeline.get_plugin_module(cmdopts['platform'])
    if hasattr(module, 'exec_env_check'):
        module.exec_env_check(cmdopts)
    else:
        _logger.debug(("Skipping execution environment check for "
                       "--platform='%s': does not define hook"),
                      cmdopts['platform'])


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator():
    """Dispatcher for shell cmd generation for an :term:`Experimental Run`.

    Dispatches generation to the selected platform.
    Called during stage 1 to add shell commands which should be run immediately
    before and after the shell command to actually execute a single
    :term:`Experimental Run` to the commands file to be fed to whatever the tool
    a given execution environment environment uses to run cmds (e.g., GNU
    parallel).

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 criteria: bc.BatchCriteria,
                 n_agents: int,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.criteria = criteria
        module = pm.pipeline.get_plugin_module(self.cmdopts['platform'])

        if hasattr(module, 'ExpRunShellCmdsGenerator'):
            self.platform = module.ExpRunShellCmdsGenerator(self.cmdopts,
                                                            self.criteria,
                                                            n_agents,
                                                            exp_num)
        else:
            self.platform = None

    def pre_run_cmds(self,
                     host: str,
                     input_fpath: pathlib.Path,
                     run_num: int) -> tp.List[types.ShellCmdSpec]:
        cmds = []
        if self.platform:
            cmds.extend(self.platform.pre_run_cmds(host, input_fpath, run_num))

        return cmds

    def exec_run_cmds(self,
                      host: str,
                      input_fpath: pathlib.Path,
                      run_num: int) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.exec_run_cmds(host, input_fpath, run_num))

        return cmds

    def post_run_cmds(self, host: str) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.post_run_cmds(host))

        return cmds


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator():
    """Dispatcher for shell cmd generation for an :term:`Experiment`.

    Dispatches generation to the selected platform.  Called during stage 2 to
    run shell commands immediately before running a given :term:`Experiment`, to
    run shell commands to actually run the experiment, and to run shell commands
    immediately after the experiment finishes.
    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 exp_num: int) -> None:
        self.cmdopts = cmdopts

        module = pm.pipeline.get_plugin_module(self.cmdopts['platform'])
        if hasattr(module, 'ExpShellCmdsGenerator'):
            _logger.debug(("Skipping generating experiment shell commands "
                           "for --platform=%s"),
                          self.cmdopts['platform'])

            self.platform = module.ExpShellCmdsGenerator(self.cmdopts,
                                                         exp_num)
        else:
            self.platform = None

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.pre_exp_cmds())

        return cmds

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.exec_exp_cmds(exec_opts))

        return cmds

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        cmds = []

        if self.platform:
            cmds.extend(self.platform.post_exp_cmds())

        return cmds


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
    'cmdline_parser',
    'cmdline_postparse_configure',
    'exec_env_checker',
    'ExpRunShellCmdsGenerator',
    'ExpShellCmdsGenerator',
    'ExpRunShellCmdsGenerator',
    'ExpShellCmdsGenerator',
]
