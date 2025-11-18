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
    Generate commands to invoke :term:`Prefect` for local computing.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        self.api_url = "http://127.0.0.1:4200/api"

    def pre_batch_cmds(self) -> list[types.ShellCmdSpec]:
        flow_path = pathlib.Path(__file__).parent / "../flow.py"
        no_prompt = "PREFECT_CLI_PROMPT=false"

        return [
            # We obviously have to start a local server. We don't have to wait
            # for the command, because it is backgrounded.
            types.ShellCmdSpec(
                cmd=f"env {no_prompt} prefect server start &",
                shell=True,
                wait=False,
            ),
            types.ShellCmdSpec(
                cmd="sleep 10",
                shell=True,
                wait=True,
            ),
            types.ShellCmdSpec(
                cmd="prefect config set PREFECT_API_URL={}".format(self.api_url),
                shell=True,
                wait=True,
            ),
            # 2025-07-29 [JRH]: This doesn't work (workers ignore it and start #
            # simultaneous sims corresponding to # cores available on the
            # machine), despite all the docs saying it should. I THINK it's
            # because global concurrency limits/task concurrency limits only
            # work with prefect cloud.
            #
            # Concurrency limit has to be set BEFORE starting workers.
            types.ShellCmdSpec(
                cmd="echo 'y' | prefect gcl delete sierra-exec-jobs-per-node || true",
                shell=True,
                wait=True,
            ),
            types.ShellCmdSpec(
                cmd="prefect gcl create sierra-exec-jobs-per-node --limit {}".format(
                    self.cmdopts["exec_jobs_per_node"]
                ),
                shell=True,
                wait=True,
            ),
            types.ShellCmdSpec(
                cmd="prefect work-pool create --type process {}".format(
                    self.cmdopts["work_pool"],
                ),
                shell=True,
                wait=True,
            ),
            # We only need to start 1 worker, since each worker can
            # handle arbitrary concurrency limits. We use a unique name for the pool
            # and queue names to avoid conflicts if we are on a shared server and
            # trying to run prefect locally.
            types.ShellCmdSpec(
                cmd="{} prefect worker start "
                "--pool={} "
                "--work-queue={} &".format(
                    no_prompt,
                    self.cmdopts["work_pool"],
                    self.cmdopts["work_queue"],
                ),
                shell=True,
                wait=False,
            ),
            types.ShellCmdSpec(
                cmd="until prefect work-pool ls | grep -q 'sierra'; do sleep 1; done",
                shell=True,
                wait=True,
            ),
            # Deploy SIERRA's local experiment execution flow. This flow
            # executes all runs in all experiments in the batch in parallel. We
            # use a unique name for the pool name to avoid conflicts if we are
            # on a shared server and trying to run prefect locally.
            types.ShellCmdSpec(
                cmd="{} prefect deploy {}:sierra --name sierra/local --pool {} --work-queue {}".format(
                    no_prompt,
                    flow_path,
                    self.cmdopts["work_pool"],
                    self.cmdopts["work_queue"],
                ),
                shell=True,
                wait=True,
            ),
        ]

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        # The needed flow is already present on the server as a deployment, so
        # we can just run it directly as many times as we want. You don't need
        # to set the queue/pool--it is inferred from the flow you are running.
        flow_cmd = (
            "prefect deployment run sierra/local "
            '--params=\'{{"input_root": "{0}","scratch_root": "{1}"}}\' --watch'
        )
        # Since this execenv is batch level, so are the outputs and scratch
        # dirs.
        flow = flow_cmd.format(exec_opts["batch_root"], exec_opts["batch_scratch_root"])
        spec = types.ShellCmdSpec(cmd=flow, shell=True, wait=True)

        return [spec]

    def post_batch_cmds(self) -> list[types.ShellCmdSpec]:
        return [
            types.ShellCmdSpec(cmd="killall prefect || true", shell=True, wait=True),
        ]


__all__ = ["BatchShellCmdsGenerator"]
