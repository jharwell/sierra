# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
HPC plugin for running SIERRA on HPC clusters using the SLURM scheduler.
"""

# Core packages
import typing as tp
import argparse
import pathlib
import os
import json

# 3rd party packages
import implements

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings


@implements.implements(bindings.IBatchShellCmdsGenerator)
class BatchShellCmdsGenerator:
    """
    Generate commands to invoke :term:`Prefect` for remote computing using docker.
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts
        self.api_url = os.environ["PREFECT_API_URL"]

    def pre_batch_cmds(self) -> list[types.ShellCmdSpec]:
        flow_path = pathlib.Path(__file__).parent / "../flow.py"
        no_prompt = "PREFECT_CLI_PROMPT=false"

        # --sierra-root is always mounted; users can specify whatever other dirs
        # from the host system are needed in the container to actually run
        # things. We mount all extra dirs read/write because we can't know what
        # the engine will be using them for. For --sierra-root, the scratch dir
        # under there gets written, so rw is appropriate is well.
        volumes = ["{0}:{0}:rw".format(self.cmdopts["sierra_root"])] + [
            f"{m}:rw" for m in self.cmdopts["docker_extra_mounts"]
        ]
        job_vars = {
            "image": self.cmdopts["docker_image"],
            # Only pull the image if it doesn't exist locally
            "image_pull_policy": "IfNotPresent",
            "volumes": volumes,
        }

        # Run as your user, to avoid issues with files in mounted volumes
        # being owned by root when the container exits.
        if self.cmdopts["docker_is_host_user"]:
            job_vars["user"] = f"{os.getuid()}:{os.getgid()}"

        ret = [
            # Make sure that the image has prefect installed and accessible.
            types.ShellCmdSpec(
                cmd="which prefect",
                shell=True,
                wait=True,
            ),
            types.ShellCmdSpec(
                cmd="prefect config set PREFECT_API_URL={}".format(self.api_url),
                shell=True,
                wait=True,
            ),
        ]

        build = (
            "{} prefect deploy {}:sierra "
            "--name sierra/dockerremote "
            "--job-variable '{}' "
            "--pool {} "
            "--work-queue {}"
        ).format(
            no_prompt,
            flow_path,
            json.dumps(job_vars),
            self.cmdopts["work_pool"],
            self.cmdopts["work_queue"],
        )
        ret.append(
            types.ShellCmdSpec(
                cmd=build,
                shell=True,
                wait=True,
            ),
        )
        return ret

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        # The needed flow is already present on the server as a deployment, so
        # we can just run it directly as many times as we want. You don't need
        # to set the queue/pool--it is inferred from the flow you are running.
        flow_cmd = (
            "prefect deployment run sierra/dockerremote "
            '--params=\'{{"input_root": "{0}","scratch_root": "{1}"}}\' --watch'
        )
        # Since this execenv is batch level, so are the outputs and scratch
        # dirs.
        flow = flow_cmd.format(exec_opts["batch_root"], exec_opts["batch_scratch_root"])
        spec = types.ShellCmdSpec(cmd=flow, shell=True, wait=True)

        return [spec]

    def post_batch_cmds(self) -> list[types.ShellCmdSpec]:
        return []


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Configure SIERRA to use :term:`Prefect` to run remotely using docker.

    Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

    - :envvar:`PREFECT_API_URL`
    """

    keys = [
        "PREFECT_API_URL",
    ]

    for k in keys:
        assert k in os.environ, f"Non-Prefect environment detected: '{k}' not found"

    return args


__all__ = ["BatchShellCmdsGenerator", "cmdline_postparse_configure"]
