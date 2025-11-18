#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Glue for bridging SIERRA <-> prefect for executing local builds."""


# Core packages
import pathlib
import subprocess


# 3rd party packages
import prefect

# Project packages
from sierra.core import utils


@prefect.task(tags=["sierra-exec-jobs-per-node"])
def exec_exp_run(
    cmd: list[str],
    scratch_path: pathlib.Path,
) -> None:
    """Execute the given command.

    Arguments:
        cmd: Command to execute a single :term:`Experimental Run`.

        scratch_path: Where to write stdout/stderr to.
    """
    flow_run_id = prefect.runtime.task_run.id

    with (
        utils.utf8open(str(scratch_path) + f"_{flow_run_id}_stdout", "w") as stdout,
        utils.utf8open(str(scratch_path) + f"_{flow_run_id}_stderr", "w") as stderr,
    ):
        subprocess.run(
            cmd,
            stdout=stdout,
            stderr=stderr,
            shell=True,
            check=True,
        )


@prefect.flow
def sierra(
    input_root: pathlib.Path,
    scratch_root: pathlib.Path,
) -> None:
    """Generate commands, execute the simulation, and package the data.

    Arguments:
        input_root: Path to the input directory for the :term:`Experiment`.

        scratch_root: Path to the scratch directory for the :term:`Experiment`.
    """
    commands = []
    with utils.utf8open(input_root / "commands.txt") as f:
        commands = [line.strip() for line in f.readlines()]

    scratch_stdouts = [scratch_root / f"_run{i}" for i in range(0, len(commands))]

    sim_results = exec_exp_run.map(commands, scratch_stdouts)
    sim_results.wait()
