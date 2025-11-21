# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Terminal interface for pltaform plugins.

Classes for generating the commands to run :term:`experiments <Batch
Experiment>` on multiple :term:`engines <Engine>` using multiple execution
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

# Project packages
import sierra.core.plugin as pm
from sierra.core import types
from sierra.core.experiment import bindings
import sierra.core.variables.batch_criteria as bc
from sierra.core.trampoline import cmdline_parser

_logger = logging.getLogger(__name__)


def cmdline_postparse_configure(
    engine: str, execenv: str, args: argparse.Namespace
) -> argparse.Namespace:
    """Dispatcher for configuring the cmdopts dictionary.

    Dispatches configuring to the selected ``--engine`` and ``--execenv``.
    Called before the pipeline starts to add modify existing cmdline arguments
    after initial parsing.  ``engine`` and ``execenv`` are needed as
    arguments as they are not present in ``args``; they are "bootstrap" cmdline
    args needed to be parsed first to build the parser for the set of cmdline
    arguments accepted.
    """
    # Configure for selected engine
    module = pm.pipeline.get_plugin_module(engine)

    if hasattr(module, "cmdline_postparse_configure"):
        args = module.cmdline_postparse_configure(execenv, args)
    else:
        _logger.debug(
            (
                "Skipping configuring cmdline from --engine='%s': "
                "does not define cmdline_postparse_configure()"
            ),
            engine,
        )

    return args


def execenv_check(cmdopts: types.Cmdopts) -> None:
    """Dispatcher for verifying execution environments in stage 2.

    This is required because what is needed to create experiments in stage 1 for
    a engine is not necessarily the same as what is needed (in terms of
    envvars, daemons, etc.) when running them.

    """
    module = pm.pipeline.get_plugin_module(cmdopts["engine"])
    if hasattr(module, "execenv_check"):
        module.execenv_check(cmdopts)
    else:
        _logger.debug(
            (
                "Skipping execution environment check for "
                "--engine=%s: does not define execenv_check()"
            ),
            cmdopts["engine"],
        )


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator:
    """Dispatcher for shell cmd generation for an :term:`Experimental Run`.

    Dispatches generation to the selected engine.
    Called during stage 1 to add shell commands which should be run immediately
    before and after the shell command to actually execute a single
    :term:`Experimental Run` to the commands file to be fed to whatever the tool
    a given execution environment environment uses to run cmds (e.g., GNU
    parallel).

    """

    def __init__(
        self,
        cmdopts: types.Cmdopts,
        criteria: bc.XVarBatchCriteria,
        exp_num: int,
        n_agents: tp.Optional[int],
    ) -> None:
        self.cmdopts = cmdopts
        self.criteria = criteria
        module = pm.pipeline.get_plugin_module(self.cmdopts["engine"])

        if hasattr(module, "ExpRunShellCmdsGenerator"):
            self.engine = module.ExpRunShellCmdsGenerator(
                self.cmdopts, self.criteria, exp_num, n_agents
            )
        else:
            self.engine = None

    def pre_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> list[types.ShellCmdSpec]:
        cmds = []
        if self.engine:
            cmds.extend(self.engine.pre_run_cmds(host, input_fpath, run_num))

        return cmds

    def exec_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.engine:
            cmds.extend(self.engine.exec_run_cmds(host, input_fpath, run_num))

        return cmds

    def post_run_cmds(
        self, host: str, run_output_root: pathlib.Path
    ) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.engine:
            cmds.extend(self.engine.post_run_cmds(host, run_output_root))

        return cmds


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """Dispatcher for shell cmd generation for an :term:`Experiment`.

    Dispatches generation to the selected engine.  Called during stage 2 to
    run shell commands immediately before running a given :term:`Experiment`, to
    run shell commands to actually run the experiment, and to run shell commands
    immediately after the experiment finishes.
    """

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts

        module = pm.pipeline.get_plugin_module(self.cmdopts["engine"])
        if hasattr(module, "ExpShellCmdsGenerator"):
            self.engine = module.ExpShellCmdsGenerator(self.cmdopts, exp_num)
        else:
            _logger.debug(
                (
                    "Skipping generating experiment shell commands "
                    "for --engine=%s: does not define ExpShellCmdsGenerator"
                ),
                self.cmdopts["engine"],
            )

            self.engine = None

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.engine:
            cmds.extend(self.engine.pre_exp_cmds())

        return cmds

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.engine:
            cmds.extend(self.engine.exec_exp_cmds(exec_opts))

        return cmds

    def post_exp_cmds(self) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.engine:
            cmds.extend(self.engine.post_exp_cmds())

        return cmds


@implements.implements(bindings.IBatchShellCmdsGenerator)
class BatchShellCmdsGenerator:
    """Dispatcher for shell cmd generation for a :term:`Batch Experiment`.

    Dispatches generation to the selected engine.  Called during stage 2 to run
    shell commands immediately before running a given :term:`Batch Experiment`,
    to run shell commands to actually run the experiment, and to run shell
    commands immediately after the whole experiment finishes.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

        module = pm.pipeline.get_plugin_module(self.cmdopts["engine"])
        if hasattr(module, "BatchShellCmdsGenerator"):
            self.engine = module.BatchShellCmdsGenerator(self.cmdopts)
        else:
            _logger.debug(
                (
                    "Skipping generating batch experiment shell commands "
                    "for --engine=%s: does not define BatchShellCmdsGenerator"
                ),
                self.cmdopts["engine"],
            )

            self.engine = None

    def pre_batch_cmds(self) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.engine:
            cmds.extend(self.engine.pre_batch_cmds())

        return cmds

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.engine:
            cmds.extend(self.engine.exec_batch_cmds(exec_opts))

        return cmds

    def post_batch_cmds(self) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.engine:
            cmds.extend(self.engine.post_batch_cmds())

        return cmds


class ExpConfigurer:
    """Perform engine-specific configuration for an :term:`Experimental Run`.

    For things can do programmatically (i.e., without needing a shell). This
    usually is things like creating directories, etc.  Called at the end of
    stage 1 during for each experimental run.

    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        module = pm.pipeline.get_plugin_module(cmdopts["engine"])
        self.engine = module.ExpConfigurer(self.cmdopts)

    def for_exp_run(
        self, exp_input_root: pathlib.Path, run_output_root: pathlib.Path
    ) -> None:
        self.engine.for_exp_run(exp_input_root, run_output_root)

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        self.engine.for_exp(exp_input_root)

    def parallelism_paradigm(self) -> str:
        return self.engine.parallelism_paradigm()


def get_local_ip():
    """
    Get the local IP address of the SIERRA host machine.
    """
    # Get all IP addresses for the hostname
    hostname = socket.gethostname()

    # Get all address info
    addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)

    # Extract unique IPv4 addresses, excluding loopback
    all_ips = {addr[4][0] for addr in addr_info if not addr[4][0].startswith("127.")}
    non_loopback_ips = [ip for ip in all_ips if not ip.startswith("127.")]

    if len(non_loopback_ips) > 1:
        logging.critical(
            (
                "SIERRA host machine has >1 non-loopback IP addresses"
                "/network interfaces--SIERRA may select the wrong "
                "one: %s"
            ),
            non_loopback_ips,
        )

        logging.critical("Using primary IP: %s", non_loopback_ips[0])

    return non_loopback_ips[0]


__all__ = [
    "ExpRunShellCmdsGenerator",
    "ExpRunShellCmdsGenerator",
    "ExpShellCmdsGenerator",
    "ExpShellCmdsGenerator",
    "cmdline_postparse_configure",
]
