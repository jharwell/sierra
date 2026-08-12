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

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Configure SIERRA for PBS HPC.

    Uses the following environment variables (if any of them are not defined an
    assertion will be triggered):

    - :envvar:`PBS_NODEFILE`

    - :envvar:`PBS_JOBID`
    """

    keys = ["PBS_NODEFILE", "PBS_JOBID"]

    for k in keys:
        assert k in os.environ, f"Non-PBS environment detected: '{k}' not found"

    assert (
        args.exec_jobs_per_node is not None
    ), "--exec-jobs-per-node is required (can't be computed from PBS)"

    assert not args.engine_vc, "Engine visual capture not supported on PBS"

    return args


class ExpShellCmdsGenerator(bindings.IExpShellCmdsGenerator):
    """Generate the cmd to invoke GNU Parallel on PBS HPC."""

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        shell = shutil.which("bash")

        return [
            # Since parallel doesn't export any envvars to child processes by
            # default, we add some common ones.
            types.ShellCmdSpec(
                cmd='export PARALLEL="--env LD_LIBRARY_PATH --env PYTHONPATH"',
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

        # 2026-08-14 [JRH]: # GNU parallel only runs a task remotely (over ssh)
        # when its --sshloginfile names a host it considers non-local; for such
        # hosts it opens a fresh, non-login ssh shell that inherits almost none
        # of the submitting environment. PBS populates $PBS_NODEFILE with the
        # node's registered hostname, so on a single-node allocation that name
        # is the local machine's own hostname -- and parallel, not recognizing
        # it as local, sshes to us and runs whatever in a stripped environment
        # where e.g., PYTHONPATH, PATH, and LD_LIBRARY_PATH are
        # absent unless explicitly forwarded.
        #
        # When the allocation is a single node that IS the local host, write ":"
        # (GNU parallel's token for "run locally") instead of the
        # hostname. Local tasks are forked, not sshed, so they inherit the full
        # submitting environment and need no --env forwarding at all -- exactly
        # what the slurm execenv gets for free (see its plugin). Multi-node
        # allocations keep the real hostnames and distribute over ssh as normal;
        # for those, env forwarding via $PARALLEL --env must cover
        # all needed envvars.
        cmd = (
            f'if [ "$(sort -u "$PBS_NODEFILE" | wc -l)" -eq 1 ] && '
            f'[ "$(sort -u "$PBS_NODEFILE")" = "$(hostname)" ]; then '
            f'echo ":" > "{nodelist}"; '
            f'else sort -u "$PBS_NODEFILE" > "{nodelist}"; fi'
        )
        unique_nodes = types.ShellCmdSpec(cmd=cmd, shell=True, wait=True)

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
