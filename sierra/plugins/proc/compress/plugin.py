# Copyright 2025 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Plugin for compressing experiment data. Currently only works with .tar.gz files.
"""

# Core packages
import multiprocessing as mp
import typing as tp
import logging
import pathlib
import shutil

# 3rd party packages
import tarfile

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, utils, batchroot

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Comcompress data for each :term:`Experiment` in the :term:`Batch Experiment`.

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
            _build_tasklist_for_exp(
                pathset.output_root / exp.name,
                run_metrics_leaf,
                cmdopts["compress_remove_after"],
            )
        )

    _logger.debug("Starting %s workers, method=%s", parallelism, mp.get_start_method())
    with mp.Pool(processes=parallelism, maxtasksperchild=1) as pool:
        processed = [pool.starmap_async(_worker, tasks)]
        _logger.debug("Waiting for workers to finish")

        for p in processed:
            p.get()

        pool.close()
        pool.join()

    _logger.debug("All workers finished")


def _build_tasklist_for_exp(
    exp_output_root: pathlib.Path,
    run_metrics_leaf: pathlib.Path,
    remove_after: bool,
) -> list[tuple[pathlib.Path, pathlib.Path, bool]]:
    """Add root dir each experimental run to queue for processing.

    Enqueueing for processing is done at the file-level rather than
    per-experiment, so that for systems with more CPUs than experiments you
    still get maximum throughput.
    """
    return [
        (
            exp_output_root,
            exp.relative_to(exp_output_root) / run_metrics_leaf,
            remove_after,
        )
        for exp in exp_output_root.iterdir()
    ]


def _worker(
    exp_output_root: pathlib.Path, relpath: pathlib.Path, remove_after: bool
) -> None:
    """Compress the output root for a single experiment into a tarball.

    Arguments:
        exp_output_root: Output root for the :term:`Experiment`.

        relpath: Path to the actual tarball relative to the experiment root.
    """

    if not (exp_output_root / relpath).exists():
        _logger.warning(
            "Cannot compress: %s does not exist", (exp_output_root / relpath)
        )
        return

    with tarfile.open(
        (exp_output_root / relpath).with_suffix(".tar.gz"), "w:gz"
    ) as tar:
        tar.add(
            str(exp_output_root / relpath), arcname=relpath.relative_to(relpath.parent)
        )

    if remove_after:
        shutil.rmtree(exp_output_root / relpath)


__all__ = ["proc_batch_exp"]
