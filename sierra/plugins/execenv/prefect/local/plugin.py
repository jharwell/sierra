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


@implements.implements(bindings.IBatchShellCmdsGenerator)
class BatchShellCmdsGenerator:
    """
    Generate the command to invoke prefect for local computing.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        self.server_url = "PREFECT_API_URL=http://127.0.0.1:4200/api"

    def pre_batch_cmds(self) -> tp.List[types.ShellCmdSpec]:
        flow_path = pathlib.Path(__file__).parent / "flow.py"
        no_prompt = "PREFECT_CLI_PROMPT=false"

        ret = [
            # We obviously have to start a local server. We don't have to wait
            # for the command, because it is backgrounded.
            types.ShellCmdSpec(
                cmd=f"env {self.server_url} {no_prompt} prefect server start &",
                shell=True,
                wait=False,
            ),
            # Deploy SIERRA's local experiment execution flow. This flow
            # executes all runs in all experiments in the batch in parallel. We
            # don't have to wait for the command, because it is
            # backgrounded. We use a unique name for the pool name to avoid
            # conflicts if we are on a shared server and trying to run prefect
            # locally.
            types.ShellCmdSpec(
                cmd=f"env {self.server_url} {no_prompt} prefect deploy {flow_path}:sierra --name sierra/local --pool sierra-pool &",
                shell=True,
                wait=False,
            ),
        ]

        assert (
            self.cmdopts["exec_jobs_per_node"] > 0
        ), "--exec-jobs-per-node must be > 0 to start workers"

        # We have to start a bunch of worker nodes.  We use a unique name for
        # the pool and queue names to avoid conflicts if we are on a shared
        # server and trying to run prefect locally.
        worker_start = f"env {self.server_url} {no_prompt} prefect worker start --pool=sierra-pool --work-queue=sierra-queue&"

        for i in range(self.cmdopts["exec_jobs_per_node"]):
            ret.append(types.ShellCmdSpec(cmd=worker_start, shell=True, wait=False))

        return ret

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> tp.List[types.ShellCmdSpec]:
        # The needed flow is already present on the server as a deployment, so
        # we can just run it directly as many times as we want.
        flow_cmd = (
            "{0} prefect deployment run sierra/exec_exp "
            '--params=\'{{"input_root": "{1}","scratch_root": "{2}"}}\''
        )
        # Since this execenv is batch level, so are the outputs and scratch
        # dirs.
        flow = flow_cmd.format(
            self.server_url, exec_opts["batch_root"], exec_opts["batch_scratch_root"]
        )
        spec = types.ShellCmdSpec(cmd=flow, shell=True, wait=False)

        return [spec]

    def post_batch_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return [
            types.ShellCmdSpec(
                cmd=f"until [ $({self.server_url} prefect flow-run ls --state RUNNING | wc -l) -eq 0 ]; do sleep 1; done;",
                shell=True,
                wait=True,
            ),
            types.ShellCmdSpec(cmd="killall prefect || true", shell=True, wait=True),
        ]


__all__ = ["BatchShellCmdsGenerator"]
