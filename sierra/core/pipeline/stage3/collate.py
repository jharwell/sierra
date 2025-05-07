# Copyright 2019 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
Classes for collating data within a :term:`Batch Experiment`.

Collation is the process of "lifting" data from :term:`Experimental Runs
<Experimental Run>` across all :term:`Experiment` for all experiments in a
:term:`Batch Experiment` into a single file (a reduce operation).  This is
needed to correctly calculate summary statistics for performance measures in
stage 4: you can't just run the calculated stddev through the calculations
because comparing curves of stddev is not meaningful.  Stage 4 needs access to
raw-(er) run data to construct a *distribution* of values to then calculate
summary statistics (such as stddev) over.
"""

# Core packages
import multiprocessing as mp
import typing as tp
import queue
import logging
import pathlib

# 3rd party packages
import pandas as pd
import numpy as np
import psutil

# Project packages
import sierra.core.variables.batch_criteria as bc
import sierra.core.plugin_manager as pm
from sierra.core import types, storage, utils, config, batchroot
from sierra.core.pipeline.stage3 import gather

_logger = logging.getLogger(__name__)


def proc_batch_exp(main_config: dict,
                   cmdopts: types.Cmdopts,
                   pathset: batchroot.PathSet,
                   criteria: bc.IConcreteBatchCriteria) -> None:
    """Generate :term:`Collated Output Data` files for each experiment.

    :term:`Collated Output Data` files generated from :term:`Raw Output Data`
    files across :term:`Experimental Runs <Experimental Run>`.  Gathered in
    parallel for each experiment for speed, unless disabled with
    ``--processing-serial``.
    """

    pool_opts = {}

    if cmdopts['processing_serial']:
        pool_opts['n_gatherers'] = 1
        pool_opts['n_processors'] = 1
    else:
        # Aways need to have at least one of each! If SIERRA is invoked on a
        # machine with 2 or less logical cores, the calculation with
        # psutil.cpu_count() will return 0 for # gatherers.
        pool_opts['n_gatherers'] = max(1, int(psutil.cpu_count() * 0.25))
        pool_opts['n_processors'] = max(1, int(psutil.cpu_count() * 0.75))

    worker_opts = {
        'project': cmdopts['project'],
        'template_input_leaf': pathlib.Path(cmdopts['expdef_template']).stem,
        'df_skip_verify': cmdopts['df_skip_verify'],
        'dist_stats': cmdopts['dist_stats'],
        'processing_mem_limit': cmdopts['processing_mem_limit'],
        'storage': cmdopts['storage'],
        'df_homogenize': cmdopts['df_homogenize']
    }

    exp_to_proc = utils.exp_range_calc(cmdopts["exp_range"],
                                       pathset.output_root,
                                       criteria)

    with mp.Pool(processes=pool_opts['n_gatherers'] +
                 pool_opts['n_processors']) as pool:

        _execute_for_batch(main_config,
                           pathset,
                           exp_to_proc,
                           worker_opts,
                           pool_opts,
                           pool)


def _execute_for_batch(main_config: types.YAMLDict,
                       pathset: batchroot.PathSet,
                       exp_to_proc: tp.List[pathlib.Path],
                       worker_opts: types.SimpleDict,
                       pool_opts: types.SimpleDict,
                       pool) -> None:
    m = mp.Manager()
    gatherq = m.Queue()
    processq = m.Queue()

    for exp in exp_to_proc:
        gatherq.put(exp)

    _logger.debug("Starting %d gatherers, method=%s",
                  pool_opts['n_gatherers'],
                  mp.get_start_method())

    gathered = [pool.apply_async(_gather_worker,
                                 (gatherq,
                                  processq,
                                  main_config,
                                  worker_opts)) for _ in range(0, pool_opts['n_gatherers'])]

    _logger.debug("Starting %d processors, method=%s",
                  pool_opts['n_processors'],
                  mp.get_start_method())
    processed = [pool.apply_async(_process_worker,
                                  (processq,
                                   main_config,
                                   pathset.stat_collate_root,
                                   worker_opts)) for _ in range(0, pool_opts['n_processors'])]

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


def _gather_worker(gatherq: mp.Queue,
                   processq: mp.Queue,
                   main_config: types.YAMLDict,
                   gather_opts: types.SimpleDict) -> None:
    gatherer = ExpDataGatherer(main_config,
                               gather_opts,
                               processq)
    while True:
        # Wait for 3 seconds after the queue is empty before bailing
        try:
            exp_output_root = gatherq.get(True, 3)
            gatherer(exp_output_root)
            gatherq.task_done()

        except queue.Empty:
            break


def _process_worker(processq: mp.Queue,
                    main_config: types.YAMLDict,
                    batch_stat_collate_root: pathlib.Path,
                    process_opts: types.SimpleDict) -> None:
    while True:
        # Wait for 3 seconds after the queue is empty before bailing
        try:
            spec = processq.get(True, 3)
            _proc_single_exp(main_config,
                             batch_stat_collate_root,
                             process_opts,
                             spec)
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
          matches a configured :term:`Performance File`.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def calc_gather_items(self,
                          run_output_root: pathlib.Path,
                          exp_name: str) -> tp.List[gather.GatherSpec]:
        to_gather = []
        proj_output_root = run_output_root / self.run_metrics_leaf
        plugin = pm.pipeline.get_plugin_module(self.gather_opts['storage'])

        for item in proj_output_root.rglob("*"):
            # Must be a file (duh)
            if not item.is_file():
                continue

            # Has to be a supported suffix for storage plugin
            if not any(s in plugin.suffixes() for s in
                       item.suffixes) or item.stat().st_size == 0:
                continue

            # Must be a configured perf file
            intra_perf_csv = self.main_config['sierra']['perf']['intra_perf_csv']
            if intra_perf_csv not in item.name:
                continue

            to_gather.append(gather.GatherSpec(exp_name=exp_name,
                                               item_stem_path=item.relative_to(
                                                   proj_output_root),
                             perfcol=self.main_config['sierra']['perf']['intra_perf_col']))
        return to_gather


def _proc_single_exp(main_config: types.YAMLDict,
                     batch_stat_collate_root: pathlib.Path,
                     process_opts: types.SimpleDict,
                     spec: gather.ProcessSpec) -> None:
    """Collate :term:`Experimental Run Data` files together (reduce operation).

    :term:`Experimental Run Data` files gathered from N :term:`Experimental Runs
    <Experimental Run>` are combined together into a single :term:`Summary .csv`
    per :term:`Experiment` with 1 column per run.
    """
    # To support inverted performance measures where smaller is better
    invert_perf = main_config['sierra']['perf'].get('inverted', False)
    intra_perf_csv = pathlib.Path(main_config['sierra']['perf']['intra_perf_csv'])
    intra_perf_col = main_config['sierra']['perf']['intra_perf_col']

    utils.dir_create_checked(batch_stat_collate_root, exist_ok=True)

    collated = {}

    # TODO: Make this actually support multiple perf columns.
    key = (intra_perf_csv, intra_perf_col)
    collated[key] = pd.DataFrame(index=spec.dfs[0].index,
                                 columns=spec.exp_run_names)
    for i, df in enumerate(spec.dfs):
        assert intra_perf_col in df.columns, \
            f"{intra_perf_col} not in {df.columns}"

        perf_df = df[intra_perf_col]
        # Invert performance if configured.
        if invert_perf:
            perf_df = 1.0 / perf_df
            # This is a bit of a hack. But also not a hack at all,
            # because infinite performance is not possible. This
            # is... Schrodinger's Hack.
            perf_df = perf_df.replace([-np.inf, np.inf], 0)

        collated[key][spec.exp_run_names[i]] = perf_df

    for (perf_file_path, col) in collated:
        df = utils.df_fill(collated[(perf_file_path, col)],
                           process_opts['df_homogenize'])
        fname = f'{spec.gather.exp_name}-{perf_file_path.stem}-{col}' + \
            config.kStorageExt['csv']
        opath = batch_stat_collate_root / fname
        storage.df_write(df, opath, 'storage.csv', index=False)


__all__ = [
    'proc_batch_exp',
    'ExpDataGatherer',
]
