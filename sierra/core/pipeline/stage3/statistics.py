# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
Classes for generating statistics within and across experiments in a batch.
"""

# Core packages
import multiprocessing as mp
import typing as tp
import queue
import logging
import pathlib

# 3rd party packages
import pandas as pd
import psutil

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, utils, stat_kernels, storage, batchroot
from sierra.core.pipeline.stage3 import gather

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.IConcreteBatchCriteria,
    gatherer_type: tp.Union[
        tp.Type[gather.DataGatherer], tp.Type[gather.ImagizeInputGatherer]
    ],
) -> None:
    """Process :term:`Raw Output Data` files for each :term:`Experiment`.

    Ideally this is done in parallel across experiments, but this can be changed
    to serial if memory on the SIERRA host machine is limited via
    ``--processing-serial``.
    """

    exp_to_proc = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, criteria
    )

    template_input_leaf = pathlib.Path(cmdopts["expdef_template"]).stem

    stat_opts = {
        "template_input_leaf": template_input_leaf,
        "df_verify": cmdopts["df_verify"],
        "dist_stats": cmdopts["dist_stats"],
        "project_imagizing": cmdopts["project_imagizing"],
        "processing_mem_limit": cmdopts["processing_mem_limit"],
        "storage": cmdopts["storage"],
        "df_homogenize": cmdopts["df_homogenize"],
    }

    pool_opts = {}
    if cmdopts["processing_serial"]:
        pool_opts["n_gatherers"] = 1
        pool_opts["n_processors"] = 1
    else:
        # Aways need to have at least one of each! If SIERRA is invoked on a
        # machine with 2 or less logical cores, the calculation with
        # psutil.cpu_count() will return 0 for # gatherers.
        pool_opts["n_gatherers"] = max(1, int(psutil.cpu_count() * 0.25))
        pool_opts["n_processors"] = max(1, int(psutil.cpu_count() * 0.75))

    with mp.Pool(
        processes=pool_opts["n_gatherers"] + pool_opts["n_processors"]
    ) as pool:
        _execute_for_batch(
            main_config, pathset, exp_to_proc, stat_opts, pool_opts, gatherer_type, pool
        )


def _execute_for_batch(
    main_config: types.YAMLDict,
    pathset: batchroot.PathSet,
    exp_to_proc: tp.List[pathlib.Path],
    stat_opts: types.SimpleDict,
    pool_opts: types.SimpleDict,
    gatherer_type: tp.Union[
        tp.Type[gather.DataGatherer], tp.Type[gather.ImagizeInputGatherer]
    ],
    pool,
) -> None:
    m = mp.Manager()
    gatherq = m.Queue()
    processq = m.Queue()

    for exp in exp_to_proc:
        gatherq.put(exp)

    # Start some threads gathering .csvs first to get things rolling.
    _logger.debug(
        "Starting %d gatherers, method=%s",
        pool_opts["n_gatherers"],
        mp.get_start_method(),
    )

    gathered = [
        pool.apply_async(
            _gather_worker, (gatherer_type, gatherq, processq, main_config, stat_opts)
        )
        for i in range(0, pool_opts["n_gatherers"])
    ]

    _logger.debug(
        "Starting %d processors, method=%s",
        pool_opts["n_processors"],
        mp.get_start_method(),
    )
    processed = [
        pool.apply_async(_process_worker, (processq, main_config, pathset, stat_opts))
        for i in range(0, pool_opts["n_processors"])
    ]

    # To capture the otherwise silent crashes when something goes wrong in
    # worker threads. Any assertions will show and any exceptions will be
    # re-raised.
    _logger.debug("Waiting for workers to finish")

    for g in gathered:
        g.get()

    for p in processed:
        p.get()

    pool.close()
    pool.join()
    _logger.debug("All threads finished")


def _gather_worker(
    gatherer_type: tp.Union[
        tp.Type[gather.DataGatherer], tp.Type[gather.ImagizeInputGatherer]
    ],
    gatherq: mp.Queue,
    processq: mp.Queue,
    main_config: types.YAMLDict,
    stat_opts: tp.Dict[str, str],
) -> None:

    gatherer = gatherer_type(main_config, stat_opts, processq)

    # Wait for 3 seconds after the queue is empty before bailing, at the
    # start. If that is not long enough then exponentially increase from
    # there until you find how long it takes to get the first item in the
    # queue, and use that as the appropriate timeout (plus a little
    # margin).
    timeout = 3
    got_item = False
    n_tries = 0
    while n_tries < 2:
        try:
            exp_output_root = gatherq.get(True, timeout)
            gatherer(exp_output_root)
            gatherq.task_done()
            got_item = True

        except queue.Empty:
            if got_item:
                break

            timeout *= 2
            n_tries += 1


def _process_worker(
    processq: mp.Queue,
    main_config: types.YAMLDict,
    pathset: batchroot.PathSet,
    stat_opts: tp.Dict[str, str],
) -> None:
    # Wait for 3 seconds after the queue is empty before bailing, at the
    # start. If that is not long enough then exponentially increase from
    # there until you find how long it takes to get the first item in the
    # queue, and use that as the appropriate timeout (plus a little
    # margin).
    timeout = 3
    got_item = False
    n_tries = 0
    while n_tries < 2:
        try:
            spec = processq.get(True, timeout)

            _proc_single_exp(main_config, stat_opts, pathset, spec)
            processq.task_done()
            got_item = True

        except queue.Empty:
            if got_item:
                break

            timeout *= 2
            n_tries += 1


def _proc_single_exp(
    main_config: types.YAMLDict,
    stat_opts: types.StrDict,
    pathset: batchroot.PathSet,
    spec: gather.ProcessSpec,
) -> None:
    """Generate statistics from output files for all runs within an experiment.

    .. IMPORTANT:: You *CANNOT* use logging ANYWHERE during processing .csv
       files. Why ? I *think* because of a bug in the logging module it If
       you get unlucky enough to spawn the process which enters the __call__()
       method in this class while another logging statement is in progress (and
       is therefore holding an internal logging module lock), then the
       underlying fork() call will copy the lock in the acquired state. Then,
       when this class goes to try to log something, it deadlocks with it

       You also can't just create loggers with unique names, as this seems to be
       something like the GIL, but for the logging module. Sometimes python
       sucks.
    """
    csv_concat = pd.concat(spec.dfs)
    exp_stat_root = pathset.stat_root / spec.gather.exp_name

    utils.dir_create_checked(exp_stat_root, exist_ok=True)

    by_row_index = csv_concat.groupby(csv_concat.index)

    dfs = {}
    if stat_opts["dist_stats"] in ["none", "all"]:
        dfs.update(stat_kernels.mean.from_groupby(by_row_index))

    if stat_opts["dist_stats"] in ["conf95", "all"]:
        dfs.update(stat_kernels.conf95.from_groupby(by_row_index))

    if stat_opts["dist_stats"] in ["bw", "all"]:
        dfs.update(stat_kernels.bw.from_groupby(by_row_index))

    for ext, df in dfs.items():
        opath = exp_stat_root / spec.gather.item_stem_path
        utils.dir_create_checked(opath.parent, exist_ok=True)
        opath = opath.with_suffix(ext)

        df = utils.df_fill(df, stat_opts["df_homogenize"])
        storage.df_write(df, opath, "storage.csv", index=False)


__all__ = [
    "proc_batch_exp",
]
