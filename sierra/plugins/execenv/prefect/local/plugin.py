# Copyright 2025 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Prefect plugin for running SIERRA locally."""

# Core packages
import typing as tp
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """
    Generate the command to invoke prefect for local computing.
    """

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        flow_path = pathlib.Path(__file__).parent / "flow.py"
        server_url = "env PREFECT_API_URL=http://127.0.0.1:4200/api"

        # This starts a local server in the background which exclusively serves
        # this flow.
        return [
            types.ShellCmdSpec(
                cmd=f"{server_url} python3 {flow_path} &", shell=True, wait=True
            )
        ]

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        # There doesn't appear to be a clean way to get an adhoc/local prefect
        # server started via the serve() command to stop; 'prefect server stop'
        # with the PREFECT_API_URL set appropriately doesn't seem to work.
        return [
            types.ShellCmdSpec(cmd="killall prefect || true", shell=True, wait=True)
        ]

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> tp.List[types.ShellCmdSpec]:
        # The needed flow is already present on the server as a deployment, so
        # we can just run it directly as many times as we want.
        flow_cmd = (
            "prefect deployment run sierra/exec_exp "
            '--params=\'{{"input_root": "{0}","scratch_root": "{0}"}}\''
        )
        flow = flow_cmd.format(
            exec_opts["exp_input_root"], exec_opts["exp_scratch_root"]
        )

        spec = types.ShellCmdSpec(cmd=flow, shell=True, wait=True)

        return [spec]


__all__ = ["ExpShellCmdsGenerator"]
