# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""HPC plugin for running experiments with an ad-hoc set of compute nodes.

E.g., whatever computers you happen to have laying around in the lab.

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
from sierra.core import types, utils
from sierra.core.experiment import bindings


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Configure SIERRA for ad-hoc HPC.

    May use the following environment variables:

    - :envvar:`SIERRA_NODEFILE` - If this is not defined ``--nodefile`` must be
      passed.

    """

    if args.nodefile is None:
        assert "SIERRA_NODEFILE" in os.environ, (
            "Non-hpc.adhoc environment detected: --nodefile not "
            "passed and 'SIERRA_NODEFILE' not found"
        )
        args.nodefile = os.environ["SIERRA_NODEFILE"]

    assert utils.path_exists(
        args.nodefile
    ), f"SIERRA_NODEFILE '{args.nodefile}' does not exist"

    assert not args.engine_vc, "Engine visual capture not supported on Adhoc"

    return args


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """Generate the cmd to invoke GNU Parallel in the ad-hoc HPC environment."""

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        shell = shutil.which("bash")

        return [
            # Since parallel doesn't export any envvars to child processes by
            # default, we add some common ones.
            types.ShellCmdSpec(
                cmd='export PARALLEL="${PARALLEL} --env LD_LIBRARY_PATH --env PYTHONPATH"',
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
        jobid = os.getpid()

        # Even if we are passed --nodelist, we still make our own copy of it, so
        # that the user can safely modify it (if they want to) after running
        # stage 1.
        nodelist = pathlib.Path(exec_opts["exp_input_root"], f"{jobid}-nodelist.txt")

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
        # GNU parallel cmd
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


__all__ = [
    "ExpShellCmdsGenerator",
    "cmdline_postparse_configure",
]
