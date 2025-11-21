# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Provides engine-specific callbacks for the :term:`ROS1+Gazebo` engine.
"""
# Core packages
import argparse
import logging
import os
import re
import typing as tp
import sys
import pathlib
import psutil

# 3rd party packages
import packaging.version
import implements

# Project packages
from sierra.core import config, ros1, types, batchroot, execenv
from sierra.core.experiment import bindings, definition
import sierra.core.variables.batch_criteria as bc

_logger = logging.getLogger("ros1gazebo.plugin")


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator:
    def __init__(
        self,
        cmdopts: types.Cmdopts,
        criteria: bc.XVarBatchCriteria,
        exp_num: int,
        n_agents: tp.Optional[int],
    ) -> None:
        self.cmdopts = cmdopts
        self.gazebo_port = -1
        self.roscore_port = -1

    def pre_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> list[types.ShellCmdSpec]:
        if host == "master":
            return []

        # First, the cmd to start roscore. We need to be on a unique port so
        # that multiple ROS instances corresponding to multiple Gazebo
        # instances with the same topic names are considered distinct/not
        # accessible between instances of Gazebo.
        self.roscore_port = config.ROS["port_base"] + run_num * 2

        # roscore will run on each slave node used during stage 2, so we have to
        # use 'localhost' for binding.
        roscore_uri = types.ShellCmdSpec(
            cmd=f"export ROS_MASTER_URI=http://localhost:{self.roscore_port};",
            shell=True,
            wait=True,
            env=True,
        )
        # ROS/Gazebo don't provide options to not print stuff, so we have to use
        # the nuclear option.
        roscore_cmd = f"roscore -p {self.roscore_port} "
        if self.cmdopts["exec_devnull"]:
            roscore_cmd += "> /dev/null 2>&1 "

        roscore_cmd += "& "

        # Each experiment gets their own roscore. Because each roscore has a
        # different port, this prevents any robots from pre-emptively starting
        # the next experiment before the rest of the robots have finished the
        # current one.
        roscore_process = types.ShellCmdSpec(
            cmd=roscore_cmd,
            shell=True,
            wait=False,
        )

        # Second, the command to give Gazebo a unique port on the host during
        # stage 2. We need to be on a unique port so that multiple Gazebo
        # instances can be run in parallel.
        self.gazebo_port = config.ROS["port_base"] + run_num * 2 + 1

        # 2021/12/13: You can't use HTTPS for some reason or gazebo won't
        # start...
        gazebo_uri = types.ShellCmdSpec(
            cmd=f"export GAZEBO_MASTER_URI=http://localhost:{self.gazebo_port};",
            shell=True,
            env=True,
            wait=True,
        )

        return [roscore_uri, roscore_process, gazebo_uri]

    def exec_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> list[types.ShellCmdSpec]:
        if host == "master":
            return []

        # For ROS+gazebo, we have two files per experimental run:
        #
        # - One for the stuff that is run on the ROS master (can be
        #   nothing/empty file).
        #
        # - One for the stuff that describes what to run on each robot/how many
        #   robots to spawn.
        #
        # We COULD do it all in a single file, but in order to share base code
        # with the ROS+robot engine, we need to do it this way.
        #
        # 2022/02/28: I don't use the -u argument here to set ROS_MASTER_URI,
        # because ROS works well enough when only running on the localhost, in
        # terms of respecting whatever the envvar is set to.
        master = str(input_fpath) + "_master" + config.ROS["launch_file_ext"]
        robots = str(input_fpath) + "_robots" + config.ROS["launch_file_ext"]

        cmd = "{} --wait {} {} ".format(config.ROS["launch_cmd"], master, robots)

        # ROS/Gazebo don't provide options to not print stuff, so we have to use
        # the nuclear option.
        if self.cmdopts["exec_devnull"]:
            cmd += "> /dev/null 2>&1"

        cmd += ";"
        return [types.ShellCmdSpec(cmd=cmd, shell=True, wait=True)]

    def post_run_cmds(
        self, host: str, run_output_root: pathlib.Path
    ) -> list[types.ShellCmdSpec]:
        return []


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts
        self.exp_num = exp_num

    def pre_exp_cmds(self) -> list[types.ShellCmdSpec]:
        # 2025-09-11 [JRH]: This was a NASTY bug which got triggered when
        # running SIERRA in a venv. ROS is installed system-wide, but mixing
        # venv+system packages via a --system venv caused all sorts of problems
        # because the venv versions were often mixing newer with older packages
        # at load time. So, we have to allow the venv interpreter to find the
        # system-wide packages AFTER everything is loaded by modifying the
        # PYTHONPATH for the sub-shell that SIERRA runs everything in.
        #
        # Hopefully this is better in ROS2.

        return [
            types.ShellCmdSpec(
                cmd="export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages/",
                shell=True,
                wait=True,
                env=True,
            ),
        ]

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> list[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> list[types.ShellCmdSpec]:
        # Cleanup roscore and gazebo processes which are still active because
        # they don't know how to clean up after themselves.
        #
        # This is OK to do even when we have multiple Gazebo+ROS instances on
        # the same machine, because we only run these commands after an
        # experiment finishes, so there isn't anything currently running we
        # might accidentally kill.
        #
        # Can't use killall, because that returns non-zero if things
        # are cleaned up nicely.
        return [
            types.ShellCmdSpec(
                cmd="if pgrep gzserver; then pkill gzserver; fi;", shell=True, wait=True
            ),
            types.ShellCmdSpec(
                cmd="if pgrep rosmaster; then pkill rosmaster; fi;",
                shell=True,
                wait=True,
            ),
            types.ShellCmdSpec(
                cmd="if pgrep roscore; then pkill roscore; fi;", shell=True, wait=True
            ),
            types.ShellCmdSpec(
                cmd="if pgrep rosout; then pkill rosout; fi;", shell=True, wait=True
            ),
        ]


@implements.implements(bindings.IExpConfigurer)
class ExpConfigurer:
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

    def for_exp_run(
        self, exp_input_root: pathlib.Path, run_output_root: pathlib.Path
    ) -> None:
        pass

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        pass

    def parallelism_paradigm(self) -> str:
        return "per-exp"


def cmdline_postparse_configure(
    env: str, args: argparse.Namespace
) -> argparse.Namespace:
    """
    Configure cmdline args after parsing for the :term:`ROS1+Gazebo` engine.

    This sets arguments appropriately depending on what HPC environment is
    selected with ``--execenv``:

    - hpc.local

    - hpc.adhoc

    - hpc.slurm

    - hpc.pbs
    """
    # No configuration needed for stages 3-5
    if not any(stage in args.pipeline for stage in [1, 2]):
        return args

    if env == "hpc.local":
        return _configure_hpc_local(args)

    if env == "hpc.adhoc":
        return _configure_hpc_adhoc(args)

    if env == "hpc.slurm":
        return _configure_hpc_slurm(args)

    if env == "hpc.pbs":
        return _configure_hpc_pbs(args)

    raise RuntimeError(f"'{env}' unsupported on ROS1+Gazebo")


def _configure_hpc_pbs(args: argparse.Namespace) -> argparse.Namespace:
    # For now, nothing to do. If more stuff with physics engine
    # configuration is implemented, this may change.
    _logger.debug(
        "Allocated %s physics threads/run, %s parallel runs/node",
        args.physics_n_threads,
        args.exec_jobs_per_node,
    )
    return args


def _configure_hpc_slurm(args: argparse.Namespace) -> argparse.Namespace:
    # We rely on the user to request their job intelligently so that
    # SLURM_TASKS_PER_NODE is appropriate.
    if args.exec_jobs_per_node is None:
        res = re.search(r"^[^\(]+", os.environ["SLURM_TASKS_PER_NODE"])
        assert (
            res is not None
        ), "Unexpected format in SLURM_TASKS_PER_NODE: '{}'".format(
            os.environ["SLURM_TASKS_PER_NODE"]
        )
        args.exec_jobs_per_node = int(res.group(0))

    _logger.debug(
        "Allocated %s physics threads/run, %s parallel runs/node",
        args.physics_n_threads,
        args.exec_jobs_per_node,
    )
    return args


def _configure_hpc_adhoc(args: argparse.Namespace) -> argparse.Namespace:
    nodes = execenv.parse_nodefile(args.nodefile)
    ppn = sys.maxsize
    for node in nodes:
        ppn = min(ppn, node.n_cores)

    if args.exec_jobs_per_node is None:
        args.exec_jobs_per_node = int(float(args.n_runs) / len(nodes))

    _logger.debug(
        "Allocated %s physics threads/run, %s parallel runs/node",
        args.physics_n_threads,
        args.exec_jobs_per_node,
    )

    return args


def _configure_hpc_local(args: argparse.Namespace) -> argparse.Namespace:
    # For now. If more physics engine configuration is added, this will
    # change.
    ppn_per_run_req = 1

    if args.exec_jobs_per_node is None:
        parallel_jobs = int(psutil.cpu_count() / float(ppn_per_run_req))

    if parallel_jobs == 0:
        _logger.warning(
            (
                "Local machine has %s logical cores, but "
                "%s threads/run requested; "
                "allocating anyway"
            ),
            psutil.cpu_count(),
            ppn_per_run_req,
        )
        parallel_jobs = 1

    # Make sure we don't oversubscribe cores--each simulation needs at
    # least 1 core.
    args.exec_jobs_per_node = min(args.n_runs, parallel_jobs)

    _logger.debug(
        "Allocated %s physics threads/run, %s parallel runs/node",
        args.physics_n_threads,
        args.exec_jobs_per_node,
    )
    return args


def execenv_check(cmdopts: types.Cmdopts) -> None:
    """
    Verify execution environment in stage 2 for :term:`ROS1+Gazebo`.

    Check for:

        - :envvar:`ROS_VERSION` is ROS1.

        - :envvar:`ROS_DISTRO` is {kinetic/noetic}.

        - :program:`gazebo` can be found and the version is supported.
    """
    keys = ["ROS_DISTRO", "ROS_VERSION"]

    for k in keys:
        assert k in os.environ, f"Non-ROS+Gazebo environment detected: '{k}' not found"

    # Check ROS distro
    assert os.environ["ROS_DISTRO"] in [
        "kinetic",
        "noetic",
    ], "SIERRA only supports ROS1 kinetic,noetic"

    # Check ROS version
    assert (
        os.environ["ROS_VERSION"] == "1"
    ), "Wrong ROS version: this plugin is for ROS1"

    # Check we can find Gazebo
    version = execenv.check_for_simulator(
        cmdopts["engine"], cmdopts["execenv"], config.GAZEBO["launch_cmd"]
    )

    # Check Gazebo version
    stdout = version.stdout.decode("utf-8")
    stderr = version.stderr.decode("utf-8")
    res = re.search(r"[0-9]+.[0-9]+.[0-9]+", stdout)
    assert (
        res is not None
    ), f"Gazebo version not in std: have stdout='{stdout}',stderr='{stderr}'"

    version = packaging.version.parse(res.group(0))
    min_version = packaging.version.parse(config.GAZEBO["min_version"])

    assert (
        version >= min_version
    ), f"Gazebo version {version} < min required {min_version}"


def population_size_from_pickle(
    adds_def: tp.Union[definition.AttrChangeSet, definition.ElementAddList],
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
) -> int:
    return ros1.callbacks.population_size_from_pickle(adds_def, main_config, cmdopts)


def population_size_from_def(
    exp_def: definition.BaseExpDef, main_config: types.YAMLDict, cmdopts: types.Cmdopts
) -> int:
    return ros1.callbacks.population_size_from_def(exp_def, main_config, cmdopts)


def agent_prefix_extract(main_config: types.YAMLDict, cmdopts: types.Cmdopts) -> str:
    return ros1.callbacks.robot_prefix_extract(main_config, cmdopts)


def pre_exp_diagnostics(
    cmdopts: types.Cmdopts, pathset: batchroot.PathSet, logger: logging.Logger
) -> None:
    s = "batch_exp_root='%s',runs/exp=%s,threads/job=%s,n_jobs=%s"
    logger.info(
        s,
        pathset.root,
        cmdopts["n_runs"],
        cmdopts["physics_n_threads"],
        cmdopts["exec_jobs_per_node"],
    )


__all__ = ["cmdline_postparse_configure", "execenv_check"]
