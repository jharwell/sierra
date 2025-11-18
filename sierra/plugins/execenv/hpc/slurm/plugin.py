# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
HPC plugin for running SIERRA on HPC clusters using the SLURM scheduler.
"""

# Core packages
import typing as tp
import argparse
import shutil
import pathlib
import os

# 3rd party packages
import implements

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Configure SIERRA for SLURM HPC.

    Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

    - :envvar:`SLURM_CPUS_PER_TASK`

    - :envvar:`SLURM_TASKS_PER_NODE`

    - :envvar:`SLURM_JOB_NODELIST`

    - :envvar:`SLURM_JOB_ID`

    """

    keys = [
        "SLURM_CPUS_PER_TASK",
        "SLURM_TASKS_PER_NODE",
        "SLURM_JOB_NODELIST",
        "SLURM_JOB_ID",
    ]

    for k in keys:
        assert k in os.environ, f"Non-SLURM environment detected: '{k}' not found"

    assert not args.engine_vc, "Engine visual capture not supported on SLURM"

    # SLURM_TASKS_PER_NODE can be set to things like '1(x32),3', indicating
    # that not all nodes will run the same # of tasks. SIERRA expects all
    # nodes to have the same # tasks allocated to each (i.e., a homogeneous
    # allocation), so we check for this.
    assert (
        "," not in os.environ["SLURM_TASKS_PER_NODE"]
    ), "SLURM_TASKS_PER_NODE not homogeneous"

    return args


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """Generate the cmd to correctly invoke GNU Parallel on SLURM HPC."""

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        shell = shutil.which("bash")

        return [
            # Since parallel doesn't export any envvars to child processes by
            # default, we add some common ones.
            types.ShellCmdSpec(
                cmd='export PARALLEL="${PARALLEL} --env LD_LIBRARY_PATH"',
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

    def post_exp_cmds(self) -> list[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        jobid = os.environ["SLURM_JOB_ID"]
        nodelist = pathlib.Path(exec_opts["exp_input_root"], f"{jobid}-nodelist.txt")

        resume = ""
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts["exec_resume"]:
            resume = "--resume-failed"

        unique_nodes = types.ShellCmdSpec(
            cmd=f"scontrol show hostnames $SLURM_JOB_NODELIST > {nodelist}",
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

        log = pathlib.Path(exec_opts["exp_scratch_root"], "parallel.log")
        parallel = parallel.format(
            nodelist,
            exec_opts["n_jobs"],
            resume,
            log,
            exec_opts["exp_scratch_root"],
            exec_opts["cmdfile_stem_path"] + exec_opts["cmdfile_ext"],
        )
        parallel_spec = types.ShellCmdSpec(cmd=parallel, shell=True, wait=True)

        return [unique_nodes, parallel_spec]


__all__ = ["ExpShellCmdsGenerator", "cmdline_postparse_configure"]
