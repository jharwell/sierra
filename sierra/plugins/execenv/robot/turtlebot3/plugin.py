# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Robot plugin for running SIERRA with a set of Turtlebot3 robots.

"""

# Core packages
import os
import logging
import typing as tp
import argparse
import shutil
import pathlib

# 3rd party packages
import implements

# Project packages
from sierra.core import types, execenv, utils
from sierra.core.experiment import bindings

_logger = logging.getLogger(__name__)


def cmdline_postparse_configure(args: argparse.Namespace) -> argparse.Namespace:
    """
    Configure SIERRA for the turtlebot3 execution environment.

    May use the following environment variables:

    - :envvar:`SIERRA_NODEFILE` - If this is not defined ``--nodefile`` must be
      passed.
    """
    if args.nodefile is None:
        assert "SIERRA_NODEFILE" in os.environ, (
            "Non-robot.turtlebot3 environment detected: --nodefile not "
            "passed and 'SIERRA_NODEFILE' not found"
        )
        args.nodefile = os.environ["SIERRA_NODEFILE"]

    assert utils.path_exists(
        args.nodefile
    ), f"SIERRA_NODEFILE '{args.nodefile}' does not exist"
    _logger.info("Using '%s' as robot hostnames file", args.nodefile)

    assert not args.engine_vc, "Engine visual capture not supported on robot.turtlebot3"

    return args


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    """Generate the cmds to invoke GNU Parallel to launch ROS on the turtlebots."""

    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> list[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        jobid = os.getpid()

        # Even if we are passed --nodelist, we still make our own copy of it, so
        # that the user can safely modify it (if they want to) after running
        # stage 1.
        nodelist = pathlib.Path(
            exec_opts["exp_input_root"], "{}-nodelist.txt".format(jobid)
        )

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

        # Make sure GNU parallel uses the right shell, because it seems to
        # defaults to /bin/sh since all cmds are run in a python shell which
        # does not have $SHELL set.
        use_bash = types.ShellCmdSpec(
            cmd="export PARALLEL_SHELL={}".format(shutil.which("bash")),
            shell=True,
            env=True,
            wait=True,
        )

        ret = [use_bash, unique_nodes]

        # 1 GNU parallel command to launch each experimental run, because each
        # run might use all available nodes/robots.
        for i in range(self.cmdopts["n_runs"]):
            ret.extend(self._generate_for_run(i, exec_opts, resume, nodelist))

        return ret

    def _generate_for_run(
        self, i: int, exec_opts: dict, resume: str, nodelist: pathlib.Path
    ) -> list[types.ShellCmdSpec]:
        ret = []
        # GNU parallel cmd for robots (slaves)
        robots = (
            "parallel {2} "
            "--jobs {1} "
            "--results {4} "
            "--joblog {3} "
            "--sshloginfile {0} "
            '--workdir {4} < "{5}"'
        )

        robots_ipath = (
            exec_opts["cmdfile_stem_path"] + f"_run{i}_slave" + exec_opts["cmdfile_ext"]
        )

        robot_log = pathlib.Path(
            exec_opts["exp_scratch_root"], f"parallel-slaves-run{i}.log"
        )

        robots = robots.format(
            nodelist,
            exec_opts["n_jobs"],
            resume,
            robot_log,
            exec_opts["exp_scratch_root"],
            robots_ipath,
        )

        # If no master is spawned, then we need to wait for this GNU
        # parallel cmd. If the master is spawned, then we wait for THAT
        # command; waiting for both results in the master never starting
        # because that cmd is never run.
        robots_spec = types.ShellCmdSpec(
            cmd=robots, shell=True, wait=self.cmdopts["no_master_node"]
        )
        ret.append(robots_spec)

        if not self.cmdopts["no_master_node"]:
            ros_master = "parallel {3} --results {1} --joblog {0} '--workdir {1} < {2}'"

            ros_master_ipath = (
                exec_opts["cmdfile_stem_path"]
                + f"_run{i}_master"
                + exec_opts["cmdfile_ext"]
            )

            master_log = pathlib.Path(
                exec_opts["exp_scratch_root"], f"parallel-master-run{i}.log"
            )
            ros_master = ros_master.format(
                master_log, exec_opts["exp_scratch_root"], ros_master_ipath, resume
            )

            master_spec = types.ShellCmdSpec(
                cmd=ros_master, shell=True, wait=not self.cmdopts["no_master_node"]
            )
            ret.append(master_spec)

        wait = 'echo "{0} seconds until launching next run!"; ' "sleep {0}s ;".format(
            self.cmdopts["exec_inter_run_pause"]
        )
        wait_spec = types.ShellCmdSpec(cmd=wait, shell=True, wait=True)
        ret.append(wait_spec)

        return ret


def execenv_check(cmdopts: types.Cmdopts) -> None:
    """
    Verify execution environment in stage 2 for the :term:`ROS1+Robot` engine.

    Checks that a valid list of IPs for robots is set/passed, and checks that
    they are reachable.
    """
    nodes = execenv.parse_nodefile(cmdopts["nodefile"])
    for node in nodes:
        if int(node.n_cores) != 1:
            _logger.warning(
                (
                    "Nodefile %s, host %s has multiple "
                    "cores; turtlebots are single core"
                ),
                cmdopts["nodefile"],
                node.hostname,
            )
        if not cmdopts["skip_online_check"]:
            execenv.check_connectivity(
                cmdopts, node.login, node.hostname, node.port, "turtlebot3"
            )


__all__ = ["ExpShellCmdsGenerator", "cmdline_postparse_configure", "execenv_check"]
