# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
HPC plugin for running SIERRA on HPC clusters using the TORQUE-PBS scheduler.
"""

# Core packages
import os
import typing as tp
import argparse
import shutil
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Configure SIERRA for PBS HPC.

    Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

    - :envvar:`PBS_NUM_PPN`

    - :envvar:`PBS_NODEFILE`

    - :envvar:`PBS_JOBID`
    """

    keys = ["PBS_NUM_PPN", "PBS_NODEFILE", "PBS_JOBID"]

    for k in keys:
        assert k in os.environ, f"Non-PBS environment detected: '{k}' not found"

    assert (
        args.exec_jobs_per_node is not None
    ), "--exec-jobs-per-node is required (can't be computed from PBS)"

    assert not args.engine_vc, "Engine visual capture not supported on PBS"

    return args


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """Generate the cmd to invoke GNU Parallel on PBS HPC."""

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
        resume = ""
        jobid = os.environ["PBS_JOBID"]
        nodelist = pathlib.Path(exec_opts["exp_input_root"], f"{jobid}-nodelist.txt")

        resume = ""
        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts["exec_resume"]:
            resume = "--resume-failed"

        unique_nodes = types.ShellCmdSpec(
            cmd=f"sort -u $PBS_NODEFILE > {nodelist}", shell=True, wait=True
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


__all__ = ["cmdline_postparse_configure"]
