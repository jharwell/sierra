#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""
HPC plugin for running SIERRA on AWS using AWS Batch (which is basically SLURM).
"""

# Core packages
import argparse
import shutil
import pathlib
import os
import logging

# 3rd party packages
import implements

# Project packages
from sierra.core import types, utils
from sierra.core.experiment import bindings

_logger = logging.getLogger(__name__)


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Configure SIERRA for AWS Batch HPC.

    Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

        - :envvar:`AWS_BATCH_JOB_ID`

        - :envvar:`AWS_BATCH_JOB_NUM_NODES`
    """

    keys = [
        "AWS_BATCH_JOB_ID",
        "AWS_BATCH_JOB_NUM_NODES",
    ]

    for k in keys:
        assert k in os.environ, f"Non-AWS Batch environment detected: '{k}' not found"

    if args.nodefile is None:
        assert "SIERRA_NODEFILE" in os.environ, (
            "Non-hpc.awsbatch environment detected: --nodefile not "
            "passed and 'SIERRA_NODEFILE' not found"
        )
        args.nodefile = os.environ["SIERRA_NODEFILE"]

    assert utils.path_exists(
        args.nodefile
    ), f"SIERRA_NODEFILE '{args.nodefile}' does not exist"

    assert not args.engine_vc, "Engine visual capture not supported on AWS Batch"

    return args


@implements.implements(bindings.IBatchShellCmdsGenerator)
class BatchShellCmdsGenerator:
    """Generate the cmd to correctly invoke GNU Parallel on AWS Batch HPC."""

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

    def pre_batch_cmds(self) -> list[types.ShellCmdSpec]:
        shell = shutil.which("bash")

        return [
            # Since parallel doesn't export any envvars to child processes by
            # default, we add some common ones.
            types.ShellCmdSpec(
                cmd='export PARALLEL="${PARALLEL} --env PATH --env LD_LIBRARY_PATH --env PYTHONPATH"',
                shell=True,
                wait=True,
                env=True,
            ),
            # Make sure GNU parallel uses the right shell, because it seems to
            # defaults to /bin/sh since all cmds are run in a python shell which
            # does not have $SHELL set.
            types.ShellCmdSpec(
                cmd=f"export PARALLEL_SHELL={shell}", shell=True, wait=True, env=True
            ),
        ]

    def post_batch_cmds(self) -> list[types.ShellCmdSpec]:
        return []

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        # To avoid concurrent batch jobs stomping on each other since the
        # nodelist is written to --sierra-root, which by definition has to be
        # shared storage.
        jobid = os.environ["AWS_BATCH_JOB_ID"]
        nodelist = pathlib.Path(exec_opts["batch_root"], f"{jobid}-nodelist.txt")

        resume = ""
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts["exec_resume"]:
            resume = "--resume-failed"

        # Make sure there are no duplicate nodes
        unique_nodes = types.ShellCmdSpec(
            cmd="sort -u {} > {}".format(exec_opts["nodefile"], nodelist),
            shell=True,
            wait=True,
        )

        parallel = (
            "parallel {2} "
            "--jobs {1} "
            "--results {4} "
            "--joblog {3} "
            "--sshloginfile {0} "
            '--workdir {4} < "{5}"'
        )

        log = pathlib.Path(exec_opts["batch_scratch_root"], "parallel.log")

        parallel = parallel.format(
            nodelist,
            exec_opts["n_jobs"],
            resume,
            log,
            exec_opts["batch_scratch_root"],
            exec_opts["cmdfile_stem_path"] + exec_opts["cmdfile_ext"],
        )
        parallel_spec = types.ShellCmdSpec(cmd=parallel, shell=True, wait=True)

        return [unique_nodes, parallel_spec]


__all__ = ["BatchShellCmdsGenerator", "cmdline_postparse_configure"]
