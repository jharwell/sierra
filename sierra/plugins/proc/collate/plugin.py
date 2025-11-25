# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
Classes for collating data within a :term:`Batch Experiment`.

Collation is the process of "lifting" data from :term:`Experimental Runs
<Experimental Run>` across all :term:`Experiment` for all experiments in a
:term:`Batch Experiment` into a single file (a reduce operation).  This is
needed to correctly calculate summary statistics for performance measures in
stage 3: you can't just run the calculated stddev through the calculations
because comparing curves of stddev is not meaningful.
"""

# Core packages
import multiprocessing as mp
import typing as tp
import queue
import logging
import pathlib

# 3rd party packages
import pandas as pd
import yaml

# Project packages
import sierra.core.variables.batch_criteria as bc
import sierra.core.plugin as pm
from sierra.core import types, storage, utils, config, batchroot
from sierra.core.pipeline.stage3 import gather

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: dict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """Generate :term:`Collated Output Data` files for each experiment.

    :term:`Collated Output Data` files generated from :term:`Raw Output Data`
    files across :term:`Experimental Runs <Experimental Run>`.  Gathered in
    parallel for each experiment for speed, unless disabled with
    ``--processing-parallelism``.
    """
    pool_opts = {}

    pool_opts["parallelism"] = cmdopts["processing_parallelism"]

    worker_opts = {
        "project": cmdopts["project"],
        "template_input_leaf": pathlib.Path(cmdopts["expdef_template"]).stem,
        "df_verify": cmdopts["df_verify"],
        "processing_mem_limit": cmdopts["processing_mem_limit"],
        "storage": cmdopts["storage"],
        "df_homogenize": cmdopts["df_homogenize"],
        "project_config_root": cmdopts["project_config_root"],
    }

    exp_to_proc = utils.exp_range_calc(
        cmdopts["exp_range"], pathset.output_root, criteria.gen_exp_names()
    )

    with mp.Pool(processes=pool_opts["parallelism"]) as pool:
        _execute_for_batch(
            main_config, pathset, exp_to_proc, worker_opts, pool_opts, pool
        )


def _execute_for_batch(
    main_config: types.YAMLDict,
    pathset: batchroot.PathSet,
    exp_to_proc: list[pathlib.Path],
    worker_opts: types.SimpleDict,
    pool_opts: types.SimpleDict,
    pool,
) -> None:
    m = mp.Manager()
    gatherq = m.Queue()
    processq = m.Queue()

    for exp in exp_to_proc:
        gatherq.put(exp)

    _logger.debug(
        "Starting %d gatherers, method=%s",
        pool_opts["parallelism"],
        mp.get_start_method(),
    )

    gathered = [
        pool.apply_async(_gather_worker, (gatherq, processq, main_config, worker_opts))
        for _ in range(0, pool_opts["parallelism"])
    ]
    _logger.debug("Waiting for gathering to finish")
    for g in gathered:
        g.get()

    _logger.debug(
        "Starting %d processors, method=%s",
        pool_opts["parallelism"],
        mp.get_start_method(),
    )
    processed = [
        pool.apply_async(
            _process_worker,
            (processq, main_config, pathset.stat_interexp_root, worker_opts),
        )
        for _ in range(0, pool_opts["parallelism"])
    ]

    # To capture the otherwise silent crashes when something goes wrong in
    # worker threads. Any assertions will show and any exceptions will be
    # re-raised.
    for p in processed:
        p.get()

    pool.close()
    pool.join()
    _logger.debug("Processing finished")


def _gather_worker(
    gatherq: mp.Queue,
    processq: mp.Queue,
    main_config: types.YAMLDict,
    gather_opts: types.SimpleDict,
) -> None:
    gatherer = ExpDataGatherer(main_config, gather_opts, processq)
    while True:
        # Wait for 3 seconds after the queue is empty before bailing
        try:
            exp_output_root = gatherq.get(True, 3)
            gatherer(exp_output_root)
            gatherq.task_done()

        except queue.Empty:
            break


def _process_worker(
    processq: mp.Queue,
    main_config: types.YAMLDict,
    batch_stat_interexp_root: pathlib.Path,
    process_opts: types.SimpleDict,
) -> None:
    while True:
        # Wait for 3 seconds after the queue is empty before bailing
        try:
            spec = processq.get(True, 3)
            _proc_single_exp(main_config, batch_stat_interexp_root, process_opts, spec)
            processq.task_done()
        except queue.Empty:
            break


class ExpDataGatherer(gather.BaseGatherer):
    """Gather :term:`Raw Output Data` files across all runs for :term:`Data Collation`.

    The configured output directory for each run is searched recursively for
    files to gather.  To be eligible for gathering and later processing, files
    must:

        - Be non-empty

        - Have a suffix which supported by the selected ``--storage`` plugin.

        - Have a name (last part of absolute path, including extension) which
          matches a configured :term:`Product` in a YAML file. E.g., a graph
          from the :ref:`plugins/prod/graphs` plugin
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def calc_gather_items(
        self, run_output_root: pathlib.Path, exp_name: str
    ) -> list[gather.GatherSpec]:
        proj_output_root = run_output_root / str(self.run_metrics_leaf)
        plugin = pm.pipeline.get_plugin_module(self.gather_opts["storage"])

        if not plugin.supports_output(pd.DataFrame):
            raise RuntimeError(
                "This plugin can only be used with storage plugins which support pd.DataFrame."
            )

        config_path = pathlib.Path(
            self.gather_opts["project_config_root"], config.PROJECT_YAML.collate
        )

        try:
            collate_config = yaml.load(utils.utf8open(config_path), yaml.FullLoader)

        except FileNotFoundError:
            self.logger.warning("%s does not exist!", config_path)
            collate_config = {}

        to_gather = []
        for item in proj_output_root.rglob("*"):
            # Must be a file (duh)
            if not item.is_file():
                continue

            # Has to be a supported suffix for storage plugin
            if (
                not any(plugin.supports_input(s) for s in item.suffixes)
                or item.stat().st_size == 0
            ):
                continue

            # Any number of perf metrics can be configured, so look for a match.
            files = collate_config["intra-exp"]
            perf_confs = [f for f in files if f["file"] in item.name]
            if not perf_confs:
                continue

            # If we get a file match, then all the columns from that file should
            # be added to the set of things to collate.
            for conf in perf_confs:
                to_gather.extend(
                    [
                        gather.GatherSpec(
                            exp_name=exp_name,
                            item_stem_path=item.relative_to(proj_output_root),
                            collate_col=col,
                        )
                        for col in conf["cols"]
                    ]
                )
        return to_gather


def _proc_single_exp(
    main_config: types.YAMLDict,
    batch_stat_collate_root: pathlib.Path,
    process_opts: types.SimpleDict,
    spec: gather.ProcessSpec,
) -> None:
    """Collate :term:`Raw Output Data` files together (reduce operation).

    :term:`Raw Output Data` files gathered from N :term:`Experimental Runs
    <Experimental Run>` are combined together into a single :term:`Batch Summary
    Data` file per :term:`Experiment` with 1 column per run.
    """
    utils.dir_create_checked(batch_stat_collate_root, exist_ok=True)

    collated = {}

    key = (spec.gather.item_stem_path, spec.gather.collate_col)
    collated[key] = pd.DataFrame(index=spec.dfs[0].index, columns=spec.exp_run_names)
    for i, df in enumerate(spec.dfs):
        assert (
            spec.gather.collate_col in df.columns
        ), f"{spec.gather.collate_col} not in {df.columns}"

        collate_df = df[spec.gather.collate_col]
        collated[key][spec.exp_run_names[i]] = collate_df

    for k, v in collated.items():
        file_path, col = k
        df = utils.df_fill(v, process_opts["df_homogenize"])
        parent = batch_stat_collate_root / spec.gather.exp_name / file_path.parent
        utils.dir_create_checked(parent, exist_ok=True)

        # This preserves the directory structure of stuff in the per-run output
        # run; if something is in a subdir there, it will show up in a subdir in
        # the collated outputs too.
        fname = f"{file_path.stem}-{col}" + config.STORAGE_EXT["csv"]
        storage.df_write(df, parent / fname, "storage.csv", index=False)


__all__ = [
    "ExpDataGatherer",
    "proc_batch_exp",
]
