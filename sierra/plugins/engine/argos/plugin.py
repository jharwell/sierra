# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
The plugin for the :term:`ARGoS` :term:`Engine`.
"""
# Core packages
import argparse
import os
import random
import typing as tp
import re
import shutil
import logging
import sys
import pathlib
import psutil

# 3rd party packages
import implements
import packaging.version

# Project packages
from sierra.core import config, types, utils, batchroot, execenv
from sierra.core.experiment import bindings, definition
import sierra.core.variables.batch_criteria as bc

_logger = logging.getLogger("engine.argos")


@implements.implements(bindings.IExpRunShellCmdsGenerator)
class ExpRunShellCmdsGenerator:
    def __init__(
        self,
        cmdopts: types.Cmdopts,
        criteria: bc.XVarBatchCriteria,
        n_agents: int,
        exp_num: int,
    ) -> None:
        self.cmdopts = cmdopts
        self.display_port = -1

    def pre_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> tp.List[types.ShellCmdSpec]:
        # When running ARGoS under Xvfb in order to headlessly render frames, we
        # need to start a per-instance Xvfb server that we tell ARGoS to use via
        # the DISPLAY environment variable, which will then be killed when the
        # shell GNU parallel spawns to run each line in the commands file exits.

        if host == "slave":
            if self.cmdopts["engine_vc"]:
                self.display_port = random.randint(0, 1000000)
                cmd1 = f"Xvfb :{self.display_port} -screen 0, 1600x1200x24 &"
                cmd2 = f"export DISPLAY=:{self.display_port};"
                spec1 = types.ShellCmdSpec(cmd=cmd1, shell=True, wait=True)
                spec2 = types.ShellCmdSpec(cmd=cmd2, shell=True, wait=True, env=True)
                return [spec1, spec2]

        return []

    def exec_run_cmds(
        self, host: str, input_fpath: pathlib.Path, run_num: int
    ) -> tp.List[types.ShellCmdSpec]:
        shellname = execenv.get_executable_shellname(config.kARGoS["launch_cmd"])
        cmd = "{0} -c {1}{2}".format(
            shellname, str(input_fpath), config.kARGoS["launch_file_ext"]
        )

        # ARGoS is pretty good about not printing stuff if we pass these
        # arguments. We don't want to pass > /dev/null so that we get the
        # text of any exceptions that cause ARGoS to crash.
        if self.cmdopts["exec_devnull"]:
            cmd += " --log-file /dev/null --logerr-file /dev/null"

        cmd += ";"

        return [types.ShellCmdSpec(cmd=cmd, shell=True, wait=True)]

    def post_run_cmds(
        self, host: str, run_output_root: pathlib.Path
    ) -> tp.List[types.ShellCmdSpec]:
        return []


@implements.implements(bindings.IExpShellCmdsGenerator)
class ExpShellCmdsGenerator:
    def __init__(self, cmdopts: types.Cmdopts, exp_num: int) -> None:
        self.cmdopts = cmdopts

    def pre_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        return []

    def exec_exp_cmds(self, exec_opts: types.StrDict) -> tp.List[types.ShellCmdSpec]:
        return []

    def post_exp_cmds(self) -> tp.List[types.ShellCmdSpec]:
        # Cleanup Xvfb processes which were started in the background. If SIERRA
        # was run with --exec-resume, then there may be no Xvfb processes to
        # kill, so we can't (in general) check the return code.
        if self.cmdopts["engine_vc"]:
            return [types.ShellCmdSpec(cmd="killall Xvfb", shell=True, wait=True)]

        return []


@implements.implements(bindings.IExpConfigurer)
class ExpConfigurer:
    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

    def for_exp_run(
        self, exp_input_root: pathlib.Path, run_output_root: pathlib.Path
    ) -> None:
        if self.cmdopts["engine_vc"]:
            argos = config.kRendering["argos"]
            frames_fpath = run_output_root / argos["frames_leaf"]
            utils.dir_create_checked(frames_fpath, exist_ok=True)

    def for_exp(self, exp_input_root: pathlib.Path) -> None:
        pass

    def parallelism_paradigm(self) -> str:
        return "per-exp"


def exec_env_check(cmdopts: types.Cmdopts) -> None:
    """
    Perform stage2 execution environment checks for the :term:`ARgoS` engine.

    Checks:

        - ARGoS can be found

        - ARGoS version supported

        - :envvar:`ARGOS_PLUGIN_PATH` is set

        - for :program:`Xvfb` if ``--engine-vc`` was passed.
    """
    keys = ["ARGOS_PLUGIN_PATH"]

    for k in keys:
        assert k in os.environ, f"Non-ARGoS environment detected: '{k}' not found"

    # Check we can find ARGoS
    proc = execenv.check_for_simulator(
        cmdopts["engine"], cmdopts["exec_env"], config.kARGoS["launch_cmd"]
    )

    # Check ARGoS version
    stdout = proc.stdout.decode("utf-8")
    stderr = proc.stderr.decode("utf-8")
    res = re.search(r"[0-9]+.[0-9]+.[0-9]+-beta[0-9]+", stdout)
    assert (
        res is not None
    ), f"ARGOS_VERSION not in stdout: stdout='{stdout}',stderr='{stderr}'"

    _logger.trace("Parsed ARGOS_VERSION: %s", res.group(0))  # type: ignore

    version = packaging.version.parse(res.group(0))
    min_version = config.kARGoS["min_version"]

    assert (
        version >= min_version
    ), f"ARGoS version {version} < min required {min_version}"

    if cmdopts["engine_vc"]:
        assert shutil.which("Xvfb") is not None, "Xvfb not found"


def cmdline_postparse_configure(
    env: str, args: argparse.Namespace
) -> argparse.Namespace:
    """
    Configure cmdline args after parsing for the :term:`ARGoS` engine.

    This sets arguments appropriately depending on what HPC environment is
    selected with ``--exec-env``.

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
    elif env == "hpc.adhoc":
        return _configure_hpc_adhoc(args)
    elif env == "hpc.slurm":
        return _configure_hpc_slurm(args)
    elif env == "hpc.pbs":
        return _configure_hpc_pbs(args)
    else:
        _logger.warning("Execution environment %s untested", env)
        return args


def _configure_hpc_pbs(args: argparse.Namespace) -> argparse.Namespace:
    _logger.debug("Configuring ARGoS for PBS execution")
    # For HPC, we want to use the the maximum # of simultaneous jobs per
    # node such that there is no thread oversubscription. We also always
    # want to allocate each physics engine its own thread for maximum
    # performance, per the original ARGoS paper.
    #
    # However, PBS does not have an environment variable for # jobs/node, so
    # we have to rely on the user to set this appropriately.
    args.physics_n_engines = int(
        float(os.environ["PBS_NUM_PPN"]) / args.exec_jobs_per_node
    )

    _logger.debug(
        "Allocated %s physics engines/run, %s parallel runs/node",
        args.physics_n_engines,
        args.exec_jobs_per_node,
    )

    return args


def _configure_hpc_slurm(args: argparse.Namespace) -> argparse.Namespace:
    _logger.debug("Configuring ARGoS for SLURM execution")
    # For HPC, we want to use the the maximum # of simultaneous jobs per
    # node such that there is no thread oversubscription. We also always
    # want to allocate each physics engine its own thread for maximum
    # performance, per the original ARGoS paper.
    #
    # We rely on the user to request their job intelligently so that
    # SLURM_TASKS_PER_NODE is appropriate.
    if args.exec_jobs_per_node is None:
        res = re.search(r"^[^\(]+", os.environ["SLURM_TASKS_PER_NODE"])
        assert (
            res is not None
        ), "Unexpected format in SLURM_TASKS_PER_NODE: '{0}'".format(
            os.environ["SLURM_TASKS_PER_NODE"]
        )
        args.exec_jobs_per_node = int(res.group(0))

    args.physics_n_engines = int(os.environ["SLURM_CPUS_PER_TASK"])

    _logger.debug(
        "Allocated %s physics engines/run, %s parallel runs/node",
        args.physics_n_engines,
        args.exec_jobs_per_node,
    )

    return args


def _configure_hpc_local(args: argparse.Namespace) -> argparse.Namespace:
    _logger.debug("Configuring ARGoS for LOCAL execution")
    if any(stage in args.pipeline for stage in [1, 2]):
        assert (
            args.physics_n_engines is not None
        ), "--physics-n-engines is required for --exec-env=hpc.local when running stage{1,2}"

    ppn_per_run_req = args.physics_n_engines

    if args.exec_jobs_per_node is None:
        # Every physics engine gets at least 1 core
        parallel_jobs = int(psutil.cpu_count() / float(ppn_per_run_req))
        if parallel_jobs == 0:
            _logger.warning(
                (
                    "Local machine has %s logical cores, but "
                    "%s physics engines/run requested; "
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
        "Allocated %s physics engines/run, %s parallel runs/node",
        args.physics_n_engines,
        args.exec_jobs_per_node,
    )

    return args


def _configure_hpc_adhoc(args: argparse.Namespace) -> argparse.Namespace:
    _logger.debug("Configuring ARGoS for ADHOC execution")

    nodes = execenv.parse_nodefile(args.nodefile)
    ppn = sys.maxsize
    for node in nodes:
        ppn = min(ppn, node.n_cores)

    # For HPC, we want to use the the maximum # of simultaneous jobs per
    # node such that there is no thread oversubscription. We also always
    # want to allocate each physics engine its own thread for maximum
    # performance, per the original ARGoS paper.
    if args.exec_jobs_per_node is None:
        args.exec_jobs_per_node = int(float(args.n_runs) / len(nodes))

    args.physics_n_engines = int(ppn / args.exec_jobs_per_node)

    _logger.debug(
        "Allocated %s physics engines/run, %s parallel runs/node",
        args.physics_n_engines,
        args.exec_jobs_per_node,
    )
    return args


def population_size_from_pickle(
    chgs: tp.Union[definition.AttrChangeSet, definition.ElementAddList],
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
) -> int:
    for path, attr, value in chgs:
        if path == ".//arena/distribute/entity" and attr == "quantity":
            return int(value)

    return -1


def arena_dims_from_criteria(
    criteria: bc.XVarBatchCriteria,
) -> tp.List[utils.ArenaExtent]:
    dims = []
    for exp in criteria.gen_attr_changelist():
        for c in exp:
            if c.path == ".//arena" and c.attr == "size":
                d = utils.Vector3D.from_str(c.value)
                dims.append(utils.ArenaExtent(d))

    assert len(dims) > 0, "Scenario dimensions not contained in batch criteria"

    return dims


def robot_type_from_def(exp_def: definition.BaseExpDef) -> tp.Optional[str]:
    """
    Get the entity type of the robots managed by ARGoS.

    .. NOTE:: Assumes homgeneous systems.
    """
    for robot in config.kARGoS["spatial_hash2D"]:
        if exp_def.has_element(f".//arena/distribute/entity/{robot}"):
            return robot

    return None


def population_size_from_def(
    exp_def: definition.BaseExpDef, main_config: types.YAMLDict, cmdopts: types.Cmdopts
) -> int:
    return population_size_from_pickle(exp_def.attr_chgs, main_config, cmdopts)


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
