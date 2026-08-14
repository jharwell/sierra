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
import typing as tp

# 3rd party packages
import polars as pl
import yaml

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, utils, storage, batchroot, config
from sierra.core.pipeline.stage3 import gather
import sierra.core.plugin as pm
from sierra.plugins.proc.statistics import kernels

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
        processq: queue.Queue,
    ) -> None:
        super().__init__(main_config, gather_opts, processq)
        self.logger = logging.getLogger(__name__)
        config_path = pathlib.Path(
            str(gather_opts["project_config_root"])
        ) / pathlib.Path(config.PROJECT_YAML.graphs)
        if utils.path_exists(config_path):
            _logger.debug("Filtering gathered data by graph generation targets")
            self.config = yaml.load(utils.utf8open(config_path), yaml.FullLoader)
        else:
            _logger.debug(
                "%s does not exist for project: not filtering gathered data",
                config.PROJECT_YAML.graphs,
            )

    def inspect_materialized_df(
        self, df: pl.DataFrame, spec: gather.GatherSpec
    ) -> None:
        nonnumeric = [col for col in df.columns if not df[col].dtype.is_numeric()]
        if nonnumeric and self.gather_opts["spread"] != "mean":
            self.logger.warning(
                (
                    "Non-numeric columns only support mean aggregation via "
                    "mode(): %s from %s; columns will be dropped"
                ),
                nonnumeric,
                spec,
            )

    def calc_gather_items(
        self, run_output_root: pathlib.Path, exp_name: str
    ) -> list[gather.GatherSpec]:
        to_gather = []
        proj_output_root = run_output_root / str(self.run_output_leaf)
        plugin = pm.pipeline.get_plugin_module(str(self.gather_opts["storage"]))

        if not plugin.supports_output(pl.DataFrame):
            raise RuntimeError(
                "This plugin can only be used with storage plugins which support pl.DataFrame."
            )

        for item in proj_output_root.rglob("*"):
            if (
                item.is_dir()
                or not any(plugin.supports_input(s) for s in item.suffixes)
                or item.stat().st_size == 0
            ):
                continue

            # An output file is gathered for statistics iff some graph in a
            # present category names it. Matching is exact (relative to the
            # output root) and shared with the collation plugin via
            # gather.file_matches -- a graph 'src' names exactly one file,
            # rooted, path-qualified for nesting. This replaces the former
            # substring test, under which e.g. 'output1D' matched every path
            # containing that string (nested copies, 'output1D_extended', ...),
            # silently gathering files no graph actually referenced.
            matched = self._matches_any_graph(item, proj_output_root)
            if matched is None:
                continue

            self.logger.trace(
                "Gathering %s: match in %s [%s]",
                item.relative_to(proj_output_root),
                config.PROJECT_YAML.graphs,
                matched,
            )
            to_gather.append(
                gather.GatherSpec(
                    exp_name=exp_name,
                    sources=[
                        gather.GatherSource(
                            item_stem_path=item.relative_to(proj_output_root),
                        )
                    ],
                    collate_col=None,
                )
            )

        return to_gather

    def _matches_any_graph(
        self, item: pathlib.Path, proj_output_root: pathlib.Path
    ) -> tp.Optional[str]:
        """Return which graph category names ``item``, or ``None`` if none do.

        A category filters only if it is present in the graph config. Within a
        present category, a graph names the file iff its ``src`` matches
        exactly (via :func:`gather.file_matches`). The return value ("intra",
        "inter", "intra/inter", or ``None``) is used only for logging; the gather
        decision is simply "matched something".
        """

        def _graph_srcs(g: dict) -> list:
            """Get source file(s) a graph reads from.

            A single-source graph names one ``src``; a multi-source graph
            (intra-exp only) names several files inside ``sources``. Statistics
            must be gathered for every file any graph reads, so both spellings
            contribute their file(s) here.
            """
            if "sources" in g:
                return [s["file"] for s in g["sources"]]
            return [g["src"]]

        def _cat_matches(section: str) -> bool:
            if section not in self.config:
                return False

            return any(
                gather.file_matches(src, item, proj_output_root)
                for category in self.config[section]
                for g in self.config[section][category]
                for src in _graph_srcs(g)
            )

        intra = _cat_matches("intra-exp")
        inter = _cat_matches("inter-exp")

        if intra and inter:
            return "intra/inter"
        if intra:
            return "intra"
        if inter:
            return "inter"
        return None


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
        "spread": cmdopts["spread"],
        "center": cmdopts["center"],
        "processing_mem_limit": cmdopts["processing_mem_limit"],
        "storage": cmdopts["storage"],
        "project_config_root": cmdopts["project_config_root"],
    }

    pool_opts = {}  # type: types.SimpleDict
    parallelism = cmdopts["processing_parallelism"]

    # Aways need to have at least one of each! If SIERRA is invoked on a machine
    # with 2 or less logical cores, the calculation with psutil.cpu_count() will
    # return 0 for # gatherers.
    pool_opts["n_gatherers"] = max(1, int(parallelism * 0.25))
    pool_opts["n_processors"] = max(1, int(parallelism * 0.75))

    with mp.Pool(
        processes=int(pool_opts["n_gatherers"]) + int(pool_opts["n_processors"])
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
        for i in range(0, int(pool_opts["n_gatherers"]))
    ]

    _logger.debug(
        "Starting %d processors, method=%s",
        pool_opts["n_processors"],
        mp.get_start_method(),
    )

    processed = [
        pool.apply_async(_process_worker, (processq, main_config, pathset, stat_opts))
        for i in range(0, int(pool_opts["n_processors"]))
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
    gatherq: queue.Queue,
    processq: queue.Queue,
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
    processq: queue.Queue,
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

    You *CANNOT* use logging ANYWHERE during processing :term:`Raw Output Data`
    files.  Why ?  I *think* because of a bug in the logging module it If you
    get unlucky enough to spawn the process which enters the ``__call__()``
    method in this class while another logging statement is in progress (and is
    therefore holding an internal logging module lock), then the underlying
    ``fork()`` call will copy the lock in the acquired state.  Then, when this
    class goes to try to log something, it deadlocks with it.

    You also can't just create loggers with unique names, as this seems to be
    something like the GIL, but for the logging module.  Sometimes python sucks.
    """
    # Add row index to each DataFrame BEFORE concatenating
    indexed_dfs = [df.with_row_index("row_idx") for df in spec.dfs]

    assert all(
        df.shape[1] == spec.dfs[0].shape[1] for df in spec.dfs
    ), "Not all dataframes have same # columns for {} in {}: exps={},shapes={}".format(
        spec.gather.primary_stem_path,
        spec.gather.exp_name,
        [str(e) for e in spec.exp_run_names],
        [str(df.shape) for df in spec.dfs],
    )

    # Now concatenate - this will have multiple rows with the same row_idx
    csv_concat = pl.concat(indexed_dfs, how="vertical")

    # Group by row_idx - now each group has N runs worth of data
    by_row_index = csv_concat.group_by("row_idx")
    exp_stat_root = pathset.stat_root / spec.gather.exp_name

    utils.dir_create_checked(exp_stat_root, exist_ok=True)

    dfs = {}
    if stat_opts["center"] == "mean":
        dfs.update(kernels.mean(by_row_index, csv_concat))
        if stat_opts["spread"] == "conf95":
            dfs.update(kernels.conf95(by_row_index, csv_concat))
        if stat_opts["spread"] == "bw":
            dfs.update(kernels.bw(by_row_index, csv_concat))

    elif stat_opts["center"] == "median":
        dfs.update(kernels.median(by_row_index, csv_concat))
        if stat_opts["spread"] == "iqr":
            dfs.update(kernels.iqr(by_row_index, csv_concat))

    for ext, df in dfs.items():
        opath = exp_stat_root / spec.gather.primary_stem_path
        utils.dir_create_checked(opath.parent, exist_ok=True)
        opath = opath.with_suffix(ext)

        storage.df_write(
            df,
            opath,
            "storage.csv",
        )


__all__ = ["proc_batch_exp"]
