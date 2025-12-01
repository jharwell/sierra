# Copyright 2025 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Plugin for copying non-deterministic experiment data.
"""

# Core packages
import multiprocessing as mp
import logging
import pathlib
import shutil
import os

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, utils, batchroot, config
from sierra.core import plugin as pm

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Copy data for each :term:`Experiment` in the :term:`Batch Experiment`.

    Ideally this is done in parallel across experiments, but this can be changed
    to serial if memory on the SIERRA host machine is limited via
    ``--processing-parallelism``.
    """

    exp_to_proc = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, criteria.gen_exp_names()
    )

    parallelism = cmdopts["processing_parallelism"]

    tasks = []
    run_metrics_leaf = main_config["sierra"]["run"]["run_metrics_leaf"]

    for exp in exp_to_proc:
        tasks.extend(
            [
                (
                    run_output_root,
                    pathset.stat_root / exp.name,
                    run_metrics_leaf,
                    cmdopts["storage"],
                    cmdopts["dataop"],
                )
                for run_output_root in (pathset.output_root / exp.name).iterdir()
            ]
        )

    _logger.debug("Starting %s workers, method=%s", parallelism, mp.get_start_method())
    with mp.Pool(processes=parallelism) as pool:
        pool.starmap(_worker, tasks)

    _logger.debug("All workers finished")


def _worker(
    run_output_root: pathlib.Path,
    exp_stat_root: pathlib.Path,
    run_metrics_leaf: str,
    storage: str,
    dataop: str,
) -> None:
    """Copy all files in the output root for a run to the statistics root.

    Arguments:
        run_output_root: Output root for the :term:`Experimental Run`.

        exp_stat_root: Path to the statistics root for the :term:`Experiment`.

        run_metrics_leaf: Relative prefix in the run output root for data.

        storage: Storage medium.
    """
    plugin = pm.pipeline.get_plugin_module(storage)
    for item in (run_output_root / run_metrics_leaf).rglob("*"):
        if (
            item.is_dir()
            or item.stat().st_size == 0
            or not any(plugin.supports_input(s) for s in item.suffixes)
        ):
            continue
        utils.dir_create_checked(exp_stat_root, exist_ok=True)
        dest = (exp_stat_root / item.name).with_suffix(
            config.STATS["mean"].exts["mean"]
        )
        if dataop == "move":
            item.rename(dest)
        elif dataop == "copy":
            with item.open("rb") as fsrc, dest.open("wb") as fdest:
                os.sendfile(fdest.fileno(), fsrc.fileno(), 0, item.stat().st_size)


__all__ = ["proc_batch_exp"]
