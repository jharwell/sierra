# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
Classes for generating statistics within and across experiments in a batch.
"""

# Core packages
import multiprocessing as mp
import queue
import logging
import pathlib
import os

# 3rd party packages
import pandas as pd
import yaml

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, utils, stat_kernels, storage, batchroot, config
from sierra.core.pipeline.stage3 import gather
import sierra.core.plugin as pm

_logger = logging.getLogger(__name__)


class DataGatherer(gather.BaseGatherer):
    """Gather :term:`Raw Output Data` files from all runs.

    The configured output directory for each run is searched recursively for
    files to gather.  To be eligible for gathering and later processing, files
    must:

        - Be non-empty

        - Have a suffix which supported by the selected ``--storage`` plugin.

        - Match an intra/inter experiment graph in ``graphs.yaml``.
    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        gather_opts: types.SimpleDict,
        processq: mp.Queue,
    ) -> None:
        super().__init__(main_config, gather_opts, processq)
        self.logger = logging.getLogger(__name__)
        config_path = pathlib.Path(gather_opts["project_config_root"]) / pathlib.Path(
            config.PROJECT_YAML.graphs
        )
        if utils.path_exists(config_path):
            _logger.debug("Filtering gathered data by graph generation targets")
            self.config = yaml.load(utils.utf8open(config_path), yaml.FullLoader)
        else:
            _logger.debug(
                "%s does not exist for project: not filtering gathered data",
                config.PROJECT_YAML.graphs,
            )

    def calc_gather_items(
        self, run_output_root: pathlib.Path, exp_name: str
    ) -> list[gather.GatherSpec]:
        to_gather = []
        proj_output_root = run_output_root / str(self.run_metrics_leaf)
        plugin = pm.pipeline.get_plugin_module(self.gather_opts["storage"])

        if not plugin.supports_output(pd.DataFrame):
            raise RuntimeError(
                "This plugin can only be used with storage plugins which support pd.DataFrame."
            )

        for item in proj_output_root.rglob("*"):
            if (
                item.is_dir()
                or not any(plugin.supports_input(s) for s in item.suffixes)
                or item.stat().st_size == 0
            ):
                continue

            filter_by_intra = "intra-exp" in self.config
            filter_by_inter = "inter-exp" in self.config

            filtered_intra = any(
                g["src_stem"] in str(item.relative_to(proj_output_root))
                for category in self.config["intra-exp"]
                for g in self.config["intra-exp"][category]
            )

            filtered_inter = any(
                g["src_stem"] in str(item.relative_to(proj_output_root))
                for category in self.config["inter-exp"]
                for g in self.config["inter-exp"][category]
            )

            # If both are present, we gather from it if there is a positive
            # match in either graph type category.
            if (
                filter_by_intra
                and filter_by_inter
                and (filtered_intra or filtered_inter)
            ):
                self.logger.trace(
                    "Gathering %s: match in %s [intra/inter]",
                    item.relative_to(proj_output_root),
                    config.PROJECT_YAML.graphs,
                )
                to_gather.append(
                    gather.GatherSpec(
                        exp_name=exp_name,
                        item_stem_path=item.relative_to(proj_output_root),
                        collate_col=None,
                    )
                )
                continue

            # If only intra-exp graphs are present, we gather from it if
            # there is a positive match in that category.
            if filter_by_intra and filtered_intra:
                self.logger.trace(
                    "Gathering %s: match in %s [intra]",
                    item.relative_to(proj_output_root),
                    config.PROJECT_YAML.graphs,
                )
                to_gather.append(
                    gather.GatherSpec(
                        exp_name=exp_name,
                        item_stem_path=item.relative_to(proj_output_root),
                        collate_col=None,
                    )
                )
                continue

            # If only inter-exp graphs are are present, we gather from it if
            # there is a positive match in that category.
            if filter_by_inter and filtered_inter:
                self.logger.trace(
                    "Gathering %s: match in %s [inter]",
                    item.relative_to(proj_output_root),
                    config.PROJECT_YAML.graphs,
                )
                to_gather.append(
                    gather.GatherSpec(
                        exp_name=exp_name,
                        item_stem_path=item.relative_to(proj_output_root),
                        collate_col=None,
                    )
                )
                continue

        return to_gather


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
    gatherer_type=DataGatherer,
) -> None:
    """Process :term:`Raw Output Data` files for each :term:`Experiment`.

    Ideally this is done in parallel across experiments, but this can be changed
    to serial if memory on the SIERRA host machine is limited via
    ``--processing-parallelism``.

    It *IS* faster to do all the gathering at once and THEN do all the
    processing, but that doesn't work for extremely large amounts of data
    generated per :term:`Experimental Run`.
    """
    exp_to_proc = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, criteria.gen_exp_names()
    )

    template_input_leaf = pathlib.Path(cmdopts["expdef_template"]).stem

    stat_opts = {
        "template_input_leaf": template_input_leaf,
        "df_verify": cmdopts["df_verify"],
        "dist_stats": cmdopts["dist_stats"],
        "processing_mem_limit": cmdopts["processing_mem_limit"],
        "storage": cmdopts["storage"],
        "project_config_root": cmdopts["project_config_root"],
        "df_homogenize": cmdopts["df_homogenize"],
    }

    pool_opts = {}
    parallelism = cmdopts["processing_parallelism"]

    # Aways need to have at least one of each! If SIERRA is invoked on a machine
    # with 2 or less logical cores, the calculation with psutil.cpu_count() will
    # return 0 for # gatherers.
    pool_opts["n_gatherers"] = max(1, int(parallelism * 0.25))
    pool_opts["n_processors"] = max(1, int(parallelism * 0.75))

    with mp.Pool(
        processes=pool_opts["n_gatherers"] + pool_opts["n_processors"]
    ) as pool:
        _execute_for_batch(
            main_config, pathset, exp_to_proc, stat_opts, pool_opts, gatherer_type, pool
        )

        pool.close()
        pool.join()


def _execute_for_batch(
    main_config: types.YAMLDict,
    pathset: batchroot.PathSet,
    exp_to_proc: list[pathlib.Path],
    stat_opts: types.SimpleDict,
    pool_opts: types.SimpleDict,
    gatherer_type,
    pool,
) -> None:
    """
    Perform statistics generation on the :term:`Batch Experiment`.

    Gathers all :term:`Raw Output Data` files FIRST, and *then* does
    processing. This is almost 50% faster than doing a true producer-consumer
    queue, probably because there is much less traffic across processes and/or
    better disk I/O performance.
    """
    m = mp.Manager()
    gatherq = m.Queue()
    processq = m.Queue()

    for exp in exp_to_proc:
        gatherq.put(exp)

    _logger.debug(
        "Starting %d gatherers, method=%s",
        pool_opts["n_gatherers"],
        mp.get_start_method(),
    )

    gathered = [
        pool.apply_async(
            _gather_worker,
            (gatherer_type, gatherq, processq, main_config, stat_opts),
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

    _logger.debug("Waiting for workers to finish")

    # To capture the otherwise silent crashes when something goes wrong in
    # worker threads. Any assertions will show and any exceptions will be
    # re-raised.
    for g in gathered:
        g.get()

    for p in processed:
        p.get()

    _logger.debug("All workers finished")

    assert (
        gatherq.empty()
    ), f"Finished processing but gather queue has {gatherq.qsize()} items?"

    assert (
        processq.empty()
    ), f"Finished processing but process queue has {processq.qsize()} items?"


def _gather_worker(
    gatherer_type,
    gatherq: mp.Queue,
    processq: mp.Queue,
    main_config: types.YAMLDict,
    stat_opts: dict[str, str],
) -> None:
    gatherer = gatherer_type(main_config, stat_opts, processq)

    # Wait for 2 seconds after the queue is empty before bailing, at the
    # start. If that is not long enough then exponentially increase from
    # there until you find how long it takes to get the first item in the
    # queue, and use that as the appropriate timeout (plus a little
    # margin).
    timeout = 3
    got_item = False
    n_tries = 0
    while n_tries < config.GATHER_WORKER_RETRIES:
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

    _logger.trace(f"Gather worker {os.getpid()} exit")


def _process_worker(
    processq: mp.Queue,
    main_config: types.YAMLDict,
    pathset: batchroot.PathSet,
    stat_opts: dict[str, str],
) -> None:
    # Wait for 2 seconds after the queue is empty before bailing, at the
    # start. If that is not long enough then exponentially increase from
    # there until you find how long it takes to get the first item in the
    # queue, and use that as the appropriate timeout (plus a little
    # margin).
    timeout = 3
    got_item = False
    n_tries = 0
    while n_tries < config.PROCESS_WORKER_RETRIES:
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
    _logger.trace(f"Process worker {os.getpid()} exit")


def _proc_single_exp(
    main_config: types.YAMLDict,
    stat_opts: types.StrDict,
    pathset: batchroot.PathSet,
    spec: gather.ProcessSpec,
) -> None:
    """Generate statistics from output files for all runs within an experiment.

    You *CANNOT* use logging ANYWHERE during processing .csv files.  Why ?  I
    *think* because of a bug in the logging module it If you get unlucky enough
    to spawn the process which enters the __call__() method in this class while
    another logging statement is in progress (and is therefore holding an
    internal logging module lock), then the underlying fork() call will copy the
    lock in the acquired state.  Then, when this class goes to try to log
    something, it deadlocks with it.

    You also can't just create loggers with unique names, as this seems to be
    something like the GIL, but for the logging module.  Sometimes python sucks.
    """
    csv_concat = pd.concat(spec.dfs)
    exp_stat_root = pathset.stat_root / spec.gather.exp_name

    utils.dir_create_checked(exp_stat_root, exist_ok=True)

    by_row_index = csv_concat.groupby(csv_concat.index)

    dfs = {}

    if stat_opts["dist_stats"] in ["none", "all"]:
        dfs.update(stat_kernels.mean(by_row_index))

    if stat_opts["dist_stats"] in ["conf95", "all"]:
        dfs.update(stat_kernels.conf95(by_row_index))

    if stat_opts["dist_stats"] in ["bw", "all"]:
        dfs.update(stat_kernels.bw(by_row_index))

    for ext, df in dfs.items():
        opath = exp_stat_root / spec.gather.item_stem_path
        utils.dir_create_checked(opath.parent, exist_ok=True)
        opath = opath.with_suffix(ext)

        storage.df_write(
            utils.df_fill(df, stat_opts["df_homogenize"]),
            opath,
            "storage.csv",
            index=False,
        )


__all__ = ["proc_batch_exp"]
