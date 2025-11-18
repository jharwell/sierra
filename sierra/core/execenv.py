#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Common functionality for ``--execenv`` plugins to use."""

# Core packages
import typing as tp
import re
import pwd
import os
import subprocess
import shutil
import logging
import argparse

# 3rd party packages
import implements

# Project packages
from sierra.core import utils, types, config
from sierra.core.trampoline import cmdline_parser
from sierra.core.experiment import bindings
import sierra.core.plugin as pm

_logger = logging.getLogger(__name__)


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """Dispatcher for shell cmd generation for an :term:`Experiment`.

    Dispatches generation to the selected execution environment.  Called during
    stage 2 to run shell commands immediately before running a given
    :term:`Experiment`, to run shell commands to actually run the experiment,
    and to run shell commands immediately after the experiment finishes.
    """

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts

        module = pm.pipeline.get_plugin_module(self.cmdopts["execenv"])
        if hasattr(module, "ExpShellCmdsGenerator"):
            self.env = module.ExpShellCmdsGenerator(self.cmdopts, exp_num)
        else:
            _logger.debug(
                (
                    "Skipping generating experiment shell commands "
                    "for --execenv=%s: does not define ExpShellCmdsGenerator"
                ),
                self.cmdopts["execenv"],
            )

            self.env = None

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.env:
            cmds.extend(self.env.pre_exp_cmds())

        return cmds

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.env:
            cmds.extend(self.env.exec_exp_cmds(exec_opts))

        return cmds

    def post_exp_cmds(self) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.env:
            cmds.extend(self.env.post_exp_cmds())

        return cmds


@implements.implements(bindings.IBatchShellCmdsGenerator)
class BatchShellCmdsGenerator:
    """Dispatcher for shell cmd generation for a :term:`Batch Experiment`.

    Dispatches generation to the selected execution environment.  Called during
    stage 2 to run shell commands immediately before running a given
    :term:`Batch Experiment`, to run shell commands to actually run the
    experiment, and to run shell commands immediately after the whole experiment
    finishes.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

        module = pm.pipeline.get_plugin_module(self.cmdopts["execenv"])
        if hasattr(module, "BatchShellCmdsGenerator"):
            self.env = module.BatchShellCmdsGenerator(self.cmdopts)
        else:
            _logger.debug(
                (
                    "Skipping generating batch experiment shell commands "
                    "for --execenv=%s: does not define BatchShellCmdsGenerator"
                ),
                self.cmdopts["execenv"],
            )

            self.env = None

    def pre_batch_cmds(self) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.env:
            cmds.extend(self.env.pre_batch_cmds())

        return cmds

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.env:
            cmds.extend(self.env.exec_batch_cmds(exec_opts))

        return cmds

    def post_batch_cmds(self) -> list[types.ShellCmdSpec]:
        cmds = []

        if self.env:
            cmds.extend(self.env.post_batch_cmds())

        return cmds


def cmdline_postparse_configure(
    execenv: str, args: argparse.Namespace
) -> argparse.Namespace:
    """Dispatcher for configuring the cmdopts dictionary.

    Dispatches configuring to the selected ``--execenv``.  Called before the
    pipeline starts to add modify existing cmdline arguments after initial
    parsing.

    ``execenv`` is needed as an arguments as it is not present in ``args``; it
    is a "bootstrap" cmdline arg needed to be parsed first to build the parser
    for the set of cmdline arguments accepted.
    """
    logger = logging.getLogger(__name__)

    # Configure for selected execution enivornment first, to check for
    # low-level details.
    module = pm.pipeline.get_plugin_module(execenv)

    if hasattr(module, "cmdline_postparse_configure"):
        args = module.cmdline_postparse_configure(args)
    else:
        logger.debug(
            (
                "Skipping configuring cmdline from --execenv=%s: "
                "does not define cmdline_postparse_configure()"
            ),
            execenv,
        )

    return args


def execenv_check(cmdopts: types.Cmdopts) -> None:
    """Dispatcher for verifying execution environments in stage 2.

    This is required because what is needed to create experiments in stage 1 for
    an execution environment is not necessarily the same as what is needed (in
    terms of envvars, daemons, etc.) when running them.
    """
    module = pm.pipeline.get_plugin_module(cmdopts["execenv"])
    if hasattr(module, "execenv_check"):
        module.execenv_check(cmdopts)
    else:
        _logger.debug(
            (
                "Skipping execution environment check for "
                "--execenv=%s: does not define execenv_check()"
            ),
            cmdopts["execenv"],
        )


def parse_nodefile(nodefile: str) -> list[types.ParsedNodefileSpec]:
    """
    Parse a text file containing a list of computational resources to use.

    Assumed to be GNU-parallel style.
    """
    ret = []  # type: list[types.ParsedNodefileSpec]

    with utils.utf8open(nodefile, "r") as f:
        lines = f.readlines()

        for line in lines:
            if parsed := _parse_nodefile_line(line):
                ret.extend([parsed])

    return ret


def _parse_nodefile_line(line: str) -> tp.Optional[types.ParsedNodefileSpec]:
    # Line starts with a comment--no parsing needed
    comment_re = r"^#"
    if res := re.search(comment_re, line):
        return None

    cores_re = r"^[0-9]+/"
    if res := re.search(cores_re, line):
        cores = int(line.split("/")[0])
        ssh = line.split("/")[1]
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

    return types.ParsedNodefileSpec(
        hostname=hostname, n_cores=cores, login=login, port=port
    )


def check_connectivity(
    cmdopts: types.Cmdopts, login: str, hostname: str, port: int, host_type: str
) -> None:
    """
    Check if passwordless connection to the specified host+login works.
    """
    hostname = hostname.split(":")[0]
    _logger.info("Checking connectivity to %s", hostname)
    ssh_diag = f"{host_type},port={port} via {login}@{hostname}"
    nc_diag = f"{host_type},port={port} via {hostname}"

    res = None
    res2 = None
    if cmdopts["online_check_method"] == "ping+ssh":
        try:
            _logger.debug("Attempt to ping %s, type=%s", hostname, host_type)
            timeout = config.ENGINE["ping_timeout"]
            res = subprocess.run(
                f"ping -c 3 -W {timeout} {hostname}",
                shell=True,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            _logger.fatal("Unable to ping %s, type=%s", hostname, host_type)
            _logger.fatal(
                "stdout=%s, stderr=%s",
                res.stdout.decode("utf-8") if res else None,
                res.stderr.decode("utf-8") if res else None,
            )
            raise
        _logger.debug("%s is alive, type=%s", hostname, host_type)
    elif cmdopts["online_check_method"] == "nc+ssh":
        try:
            _logger.debug("Check for ssh tunnel to %s", nc_diag)
            timeout = config.ENGINE["ping_timeout"]
            res = subprocess.run(
                f"nc -z {hostname} {port}",
                shell=True,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            _logger.fatal("No ssh tunnel to %s", nc_diag)
            _logger.fatal(
                "stdout=%s, stderr=%s",
                res.stdout.decode("utf-8") if res else None,
                res.stderr.decode("utf-8") if res else None,
            )
            raise
        _logger.debug("ssh tunnel to %s alive", nc_diag)

    try:

        _logger.debug("Verify ssh to %s", ssh_diag)
        res2 = subprocess.run(
            (
                f"ssh -p{port} "
                "-o PasswordAuthentication=no "
                "-o StrictHostKeyChecking=no "
                "-o BatchMode=yes "
                f"{login}@{hostname} exit"
            ),
            shell=True,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        _logger.fatal("Unable to connect to %s", ssh_diag)
        _logger.fatal(
            "stdout=%s, stderr=%s",
            res2.stdout.decode("utf-8") if res2 else None,
            res2.stderr.decode("utf-8") if res2 else None,
        )
        raise
    _logger.info("%s@%s online", host_type, hostname)


def check_for_simulator(
    engine: str, execenv: str, name: str
) -> subprocess.CompletedProcess[bytes]:
    """
    Check if the specified executable name exists/is findable.

    Returns the version string for the executable. Requires the executable
    respect/accept ``-v``.

    """
    shellname = get_executable_arch_aware(name)

    version_cmd = f"{shellname} -v"
    _logger.debug("Check version for '%s' via '%s'", shellname, version_cmd)

    # Don't check the return code, because some siulators return -1 with -v
    # (sigh).
    if shutil.which(shellname):
        return subprocess.run(
            version_cmd,
            capture_output=True,
            shell=True,
            check=False,
        )

    raise RuntimeError(
        f"Bad --execenv '{execenv}' for engine '{engine}': cannot find '{name}'"
    )


def get_executable_arch_aware(base: str) -> str:
    """
    Get the executable name in an :envvar:`SIERRA_ARCH`-aware way.

    Returns <base>-<arch> if the envvar is set, and <base> otherwise.
    """
    if "SIERRA_ARCH" in os.environ:
        arch = os.environ["SIERRA_ARCH"]
        return f"{base}-{arch}"

    return base


__all__ = [
    "ExpShellCmdsGenerator",
    "check_connectivity",
    "check_for_simulator",
    "cmdline_postparse_configure",
    "get_executable_arch_aware",
    "parse_nodefile",
]
