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


@prefect.task()
def exec_exp_run(
    cmd: list[str],
    scratch_stdout: pathlib.Path,
) -> None:
    """Execute the given command.

    Arguments:
        cmd: Command to execute a single :term:`Experimental Run`.

        log_directory: where to write stdout/stderr to
    """
    flow_run_id = prefect.runtime.task_run.id

    with open(str(scratch_stdout) + f"_{flow_run_id}", "w") as stdout:
        subprocess.run(
            cmd, stdout=stdout, stderr=subprocess.STDOUT, shell=True, check=True
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
    with open(input_root / "commands.txt") as f:
        commands = [line.strip() for line in f.readlines()]

    logger = prefect.get_run_logger()

    scratch_stdouts = [scratch_root / f"stdout_run{i}" for i in range(0, len(commands))]
    logger.info("%s %s", commands, scratch_stdouts)
    sim_results = exec_exp_run.map(commands, scratch_stdouts)
    sim_results.wait()


if __name__ == "__main__":
    sierra.deploy(name="exec_exp")
