# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""HPC plugin for running SIERRA locally.

Not necessarily HPC, but it fits well enough under that semantic umbrella.

"""

# Core packages
import typing as tp
import shutil
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core import types
from sierra.core.experiment import bindings


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """
    Generate the commands for local HPC (experiment-level parallelism).
    """

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
        resume = ""

        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts["exec_resume"]:
            resume = "--resume-failed"

        parallel = (
            "parallel {1} "
            "--jobs {2} "
            "--results {0} "
            "--joblog {3} "
            '--no-notice < "{4}"'
        )

        log = pathlib.Path(exec_opts["exp_scratch_root"], "parallel.log")
        parallel = parallel.format(
            exec_opts["exp_scratch_root"],
            resume,
            exec_opts["n_jobs"],
            log,
            exec_opts["cmdfile_stem_path"] + exec_opts["cmdfile_ext"],
        )

        return [types.ShellCmdSpec(cmd=parallel, shell=True, wait=True)]


@implements.implements(bindings.IBatchShellCmdsGenerator)
class BatchShellCmdsGenerator:
    """
    Generate the commands for local HPC (batch-level parallelism).
    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

    def pre_batch_cmds(self) -> list[types.ShellCmdSpec]:
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

    def post_batch_cmds(self) -> list[types.ShellCmdSpec]:
        return []

    def exec_batch_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        resume = ""

        # This can't be --resume, because then GNU parallel looks at the results
        # directory, and if there is stuff in it, (apparently) assumes that the
        # job finished...
        if exec_opts["exec_resume"]:
            resume = "--resume-failed"

        parallel = (
            "parallel {1} "
            "--jobs {2} "
            "--results {0} "
            "--joblog {3} "
            '--no-notice < "{4}"'
        )

        log = pathlib.Path(exec_opts["batch_scratch_root"], "parallel.log")
        parallel = parallel.format(
            exec_opts["batch_scratch_root"],
            resume,
            exec_opts["n_jobs"],
            log,
            exec_opts["cmdfile_stem_path"] + exec_opts["cmdfile_ext"],
        )

        return [types.ShellCmdSpec(cmd=parallel, shell=True, wait=True)]


__all__ = ["BatchShellCmdsGenerator", "ExpShellCmdsGenerator"]
