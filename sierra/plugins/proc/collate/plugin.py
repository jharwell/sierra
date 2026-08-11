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
import queue
import logging
import pathlib
import typing as tp

# 3rd party packages
import polars as pl
import yaml

# Project packages
import sierra.core.variables.batch_criteria as bc
import sierra.core.plugin as pm
from sierra.core import types, storage, utils, config, batchroot
from sierra.core.pipeline.stage3 import gather
from sierra.plugins.proc.collate import cconfig
from sierra.plugins.proc.collate.cconfig import CollateSource, CollateTarget

_logger = logging.getLogger(__name__)


# Resolution rule shared with the statistics plugin; see
# :func:`sierra.core.pipeline.stage3.gather.file_matches`. Kept as a
# module-level alias so existing references (and tests) resolve locally.
_file_matches = gather.file_matches


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
        for _ in range(0, int(pool_opts["parallelism"]))
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
        for _ in range(0, int(pool_opts["parallelism"]))
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
    gatherq: queue.Queue,
    processq: queue.Queue,
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
    processq: queue.Queue,
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
        proj_output_root = run_output_root / str(self.run_output_leaf)
        plugin = pm.pipeline.get_plugin_module(str(self.gather_opts["storage"]))

        if not plugin.supports_output(pl.DataFrame):
            raise RuntimeError(
                "This plugin can only be used with storage plugins which support pl.DataFrame."
            )

        config_path = pathlib.Path(
            str(self.gather_opts["project_config_root"]), config.PROJECT_YAML.collate
        )

        try:
            collate_config = yaml.load(utils.utf8open(config_path), yaml.FullLoader)

        except FileNotFoundError:
            self.logger.warning("%s does not exist!", config_path)
            collate_config = None

        # Validate + normalize the whole file at once: every problem is reported
        # together (via cconfig.ConfigError) before any collation runs, and the
        # result is the list of CollateTarget objects consumed below.
        targets = cconfig.validate(collate_config)

        # Index the run's eligible output files once, then resolve each
        # configured target against them. Target-centric (not file-centric) so
        # that a target spanning several files becomes one spec carrying all its
        # sources.
        eligible = [
            item
            for item in proj_output_root.rglob("*")
            if item.is_file()
            and any(plugin.supports_input(s) for s in item.suffixes)
            and item.stat().st_size > 0
        ]

        to_gather = []
        for target in targets:
            # Every source of every target -- single- or multi-source -- must
            # resolve to exactly one eligible file. A configured 'file' that
            # matches more than one output is an ambiguous specification and is
            # a hard error (the researcher path-qualifies to disambiguate); one
            # that matches none means the run did not produce it, so the target
            # simply contributes nothing here.
            resolved = self._resolve_sources(target, eligible, proj_output_root)
            if resolved is None:
                continue

            output_stem = self._target_output_stem(target, resolved)
            to_gather.extend(
                [
                    gather.GatherSpec(
                        exp_name=exp_name,
                        sources=resolved,
                        collate_col=out_col,
                        output_stem=output_stem,
                    )
                    for out_col in self._target_output_cols(target)
                ]
            )

        return to_gather

    @staticmethod
    def _target_output_stem(
        target: "CollateTarget",
        resolved: tuple[gather.GatherSource, ...],
    ) -> str:
        """Resolve the output filename stem for a target.

        An explicitly-configured ``name`` always wins. Otherwise (single-source
        with a defaulted name) the sole resolved file's stem is used, which keeps
        historical single-file output filenames byte-for-byte unchanged.
        """
        if target.name_explicit:
            return target.name
        # Not explicit => single-source (multi-source always has an explicit
        # name), so exactly one resolved source.
        return (
            resolved[0].item_stem_path.name[: -len(resolved[0].item_stem_path.suffix)]
            or resolved[0].item_stem_path.name
        )

    def _resolve_sources(
        self,
        target: "CollateTarget",
        eligible: list[pathlib.Path],
        proj_output_root: pathlib.Path,
    ) -> tp.Optional[tuple[gather.GatherSource, ...]]:
        """Resolve every source of a target to exactly one run-relative path.

        Returns ``None`` if any source matches no eligible file (the target then
        contributes nothing for this run). Raises if any source matches more than
        one file: an ambiguous specification is never silently resolved, since a
        first-match choice would depend on incidental filesystem ordering/depth
        and could silently collate the wrong data or overwrite outputs.
        """
        resolved = []
        for source in target.sources:
            matches = [
                item
                for item in eligible
                if _file_matches(source.file, item, proj_output_root)
            ]
            if not matches:
                return None
            if len(matches) > 1:
                candidates = [str(m.relative_to(proj_output_root)) for m in matches]
                raise ValueError(
                    f"Ambiguous collation source '{source.file}'"
                    f"{' in target ' + repr(target.name) if target.name_explicit else ''}"
                    f" matches multiple output files: {candidates}. A configured "
                    "'file' must name exactly one output; path-qualify it "
                    "(e.g. 'subdir/name') to disambiguate."
                )
            resolved.append(
                gather.GatherSource(
                    item_stem_path=matches[0].relative_to(proj_output_root),
                    col_map=source.col_map,
                )
            )
        return tuple(resolved)

    @staticmethod
    def _target_output_cols(target: "CollateTarget") -> list[str]:
        cols = []
        for source in target.sources:
            cols.extend(source.output_cols)
        return cols


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

    col = spec.gather.collate_col

    # Build dictionary of columns instead of starting with empty DataFrame
    columns_dict = {}

    for i, df in enumerate(spec.dfs):
        assert col in df.columns, f"{col} not in {df.columns}"

        # Add column to dictionary
        columns_dict[spec.exp_run_names[i]] = df[col]

    # Create DataFrame from the dictionary of columns
    df = pl.DataFrame(columns_dict)

    # Output directory mirrors the primary source's location, so nested per-run
    # outputs stay nested in the collated outputs. Output *stem* is the target
    # name (which defaults to the file stem for single-source targets, so
    # single-file output filenames are unchanged).
    primary_parent = spec.gather.sources[0].item_stem_path.parent
    output_stem = spec.gather.output_stem

    parent = batch_stat_collate_root / spec.gather.exp_name / primary_parent
    utils.dir_create_checked(parent, exist_ok=True)

    fname = f"{output_stem}-{col}" + config.STORAGE_EXT["csv"]
    storage.df_write(df, parent / fname, "storage.csv")


__all__ = [
    "ExpDataGatherer",
    "proc_batch_exp",
]
