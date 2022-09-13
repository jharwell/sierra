# Copyright 2019 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""Classes for collating data within a :term:`Batch Experiment`.

Collation is the process of "lifting" data from :term:`Experimental Runs
<Experimental Run>` across all :term:`Experiment` for all experiments in a
:term:`Batch Experiment` into a single CSV (a reduce operation).  This is needed
to correctly calculate summary statistics for performance measures in stage 4:
you can't just run the calculated stddev through the calculations for
flexibility (for example) because comparing curves of stddev is not
meaningful. Stage 4 needs access to raw-(er) run data to construct a
`distribution` of performance measure values to then calculate the summary
statistics (such as stddev) over.

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
from sierra.core import types, storage, utils, config


class ExperimentalRunParallelCollator:
    """Generates :term:`Collated .csv` files for each :term:`Experiment`.

    :term:`Collated .csv` files generated from :term:`Output .csv` files across
     :term:`Experimental Runs <Experimental Run>`.  Gathered in parallel for
     each experiment for speed, unless disabled with ``--processing-serial``.

    """

    def __init__(self, main_config: dict, cmdopts: types.Cmdopts):
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        if self.cmdopts['processing_serial']:
            n_gatherers = 1
            n_processors = 1
        else:
            # Aways need to have at least one of each! If SIERRA is invoked on a
            # machine with 2 or less logical cores, the calculation with
            # psutil.cpu_count() will return 0 for # gatherers.
            n_gatherers = max(1, int(psutil.cpu_count() * 0.25))
            n_processors = max(1, int(psutil.cpu_count() * 0.75))

        pool = mp.Pool(processes=n_gatherers + n_processors)

        m = mp.Manager()
        gatherq = m.Queue()
        processq = m.Queue()

        exp_to_proc = utils.exp_range_calc(self.cmdopts,
                                           self.cmdopts['batch_output_root'],
                                           criteria)

        for exp in exp_to_proc:
            gatherq.put((self.cmdopts['batch_output_root'], exp.name))

        self.logger.debug("Starting %d gatherers, method=%s",
                          n_gatherers,
                          mp.get_start_method())

        gathered = [pool.apply_async(ExperimentalRunParallelCollator._gather_worker,
                                     (gatherq,
                                      processq,
                                      self.main_config,
                                      self.cmdopts['project'],
                                      self.cmdopts['storage_medium'])) for _ in range(0, n_gatherers)]

        self.logger.debug("Starting %d processors, method=%s",
                          n_processors,
                          mp.get_start_method())
        processed = [pool.apply_async(ExperimentalRunParallelCollator._process_worker,
                                      (processq,
                                       self.main_config,
                                       self.cmdopts['batch_stat_collate_root'],
                                       self.cmdopts['storage_medium'],
                                       self.cmdopts['df_homogenize'])) for _ in range(0, n_processors)]

        # To capture the otherwise silent crashes when something goes wrong in
        # worker threads. Any assertions will show and any exceptions will be
        # re-raised.
        self.logger.debug("Waiting for workers to finish")
        for g in gathered:
            g.get()

        for p in processed:
            p.get()

        pool.close()
        pool.join()
        self.logger.debug("All threads finished")

    @staticmethod
    def _gather_worker(gatherq: mp.Queue,
                       processq: mp.Queue,
                       main_config: types.YAMLDict,
                       project: str,
                       storage_medium: str) -> None:
        module = pm.module_load_tiered(project=project,
                                       path='pipeline.stage3.run_collator')
        gatherer = module.ExperimentalRunCSVGatherer(main_config,
                                                     storage_medium,
                                                     processq)
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                batch_output_root, exp = gatherq.get(True, 3)
                gatherer(batch_output_root, exp)
                gatherq.task_done()

            except queue.Empty:
                break

    @staticmethod
    def _process_worker(processq: mp.Queue,
                        main_config: types.YAMLDict,
                        batch_stat_collate_root: pathlib.Path,
                        storage_medium: str,
                        df_homogenize: str) -> None:
        collator = ExperimentalRunCollator(main_config,
                                           batch_stat_collate_root,
                                           storage_medium,
                                           df_homogenize)
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                item = processq.get(True, 3)

                exp_leaf = list(item.keys())[0]
                gathered_runs, gathered_dfs = item[exp_leaf]
                collator(gathered_runs, gathered_dfs, exp_leaf)
                processq.task_done()
            except queue.Empty:
                break


class ExperimentalRunCSVGatherer:
    """Gather :term:`Output .csv` files across all runs within an experiment.

    This class can be extended/overriden using a :term:`Project` hook. See
    :ref:`ln-sierra-tutorials-project-hooks` for details.

    Attributes:

        processq: The multiprocessing-safe producer-consumer queue that the data
                  gathered from experimental runs will be placed in for
                  processing.

        storage_medium: The name of the storage medium plugin to use to extract
                        dataframes from when reading run data.

        main_config: Parsed dictionary of main YAML configuration.

        logger: The handle to the logger for this class. If you extend this
                class, you should save/restore this variable in tandem with
                overriding it in order to get logging messages have unique
                logger names between this class and your derived class, in order
                to reduce confusion.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 storage_medium: str,
                 processq: mp.Queue) -> None:
        self.processq = processq

        self.storage_medium = storage_medium
        self.main_config = main_config

        self.run_metrics_leaf = main_config['sierra']['run']['run_metrics_leaf']

        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 batch_output_root: pathlib.Path,
                 exp_leaf: str):
        """
        Gather CSV data from all experimental runs in an experiment.

        Gathered data is put in a queue for processing.

        Arguments:

            exp_leaf: The name of the experiment directory within the
                      ``batch_output_root``.

        """
        self.logger.info('Gathering .csvs: %s...', exp_leaf)

        exp_output_root = batch_output_root / exp_leaf

        runs = sorted(exp_output_root.iterdir())

        gathered = []
        for run in runs:
            run_output_root = run / self.run_metrics_leaf
            gathered.append(self.gather_csvs_from_run(run_output_root))

        names = [run.name for run in runs]
        self.processq.put({exp_leaf: (names, gathered)})

    def gather_csvs_from_run(self,
                             run_output_root: pathlib.Path) -> tp.Dict[tp.Tuple[str, str],
                                                                       pd.DataFrame]:
        """Gather all data from a single run within an experiment.

        Returns:

           dict: A dictionary of <(CSV file name, CSV performance column),
                 dataframe> key-value pairs. The CSV file name is the leaf part
                 of the path with the extension included.

        """

        intra_perf_csv = self.main_config['sierra']['perf']['intra_perf_csv']
        intra_perf_leaf = intra_perf_csv.split('.')[0]
        intra_perf_col = self.main_config['sierra']['perf']['intra_perf_col']

        reader = storage.DataFrameReader(self.storage_medium)
        perf_path = run_output_root / (intra_perf_leaf +
                                       config.kStorageExt['csv'])
        perf_df = reader(perf_path, index_col=False)

        return {
            (intra_perf_leaf, intra_perf_col): perf_df[intra_perf_col],
        }


class ExperimentalRunCollator:
    """Collate gathered :term:`Output .csv` files together (reduce operation).

    :term:`Output .csv`s gathered from N :term:`Experimental Runs <Experimental
    Run>` are combined together into a single :term:`Summary .csv` per
    :term:`Experiment` with 1 column per run.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 batch_stat_collate_root: pathlib.Path,
                 storage_medium: str,
                 df_homogenize: str) -> None:
        self.main_config = main_config
        self.batch_stat_collate_root = batch_stat_collate_root
        self.df_homogenize = df_homogenize

        self.storage_medium = storage_medium

        # To support inverted performance measures where smaller is better
        self.invert_perf = main_config['sierra']['perf'].get('inverted', False)
        self.intra_perf_csv = main_config['sierra']['perf']['intra_perf_csv']

        utils.dir_create_checked(self.batch_stat_collate_root, exist_ok=True)

    def __call__(self,
                 gathered_runs: tp.List[str],
                 gathered_dfs: tp.List[tp.Dict[tp.Tuple[str, str], pd.DataFrame]],
                 exp_leaf: str) -> None:
        collated = {}

        for run in gathered_runs:
            run_dfs = gathered_dfs[gathered_runs.index(run)]

            for csv_leaf, col in run_dfs.keys():
                csv_df = run_dfs[(csv_leaf, col)]

                # Invert performance if configured.
                if self.invert_perf and csv_leaf in self.intra_perf_csv:
                    csv_df = 1.0 / csv_df

                    # Because of the requirement that P(N) >= 0 for flexibility
                    # (1/0 = inf gives a crash with DTW), if the current level
                    # of performance is 0, it stays 0.
                    #
                    # This is a bit of a hack. But also not a hack at all,
                    # because infinite performance is not possible. This
                    # is... Schrodinger's Hack.
                    csv_df = csv_df.replace([-np.inf, np.inf], 0)

                if (csv_leaf, col) not in collated:
                    collated[(csv_leaf, col)] = pd.DataFrame(index=csv_df.index,
                                                             columns=gathered_runs)
                collated[(csv_leaf, col)][run] = csv_df

        for (csv_leaf, col) in collated:
            writer = storage.DataFrameWriter(self.storage_medium)
            df = utils.df_fill(collated[(csv_leaf, col)], self.df_homogenize)
            fname = f'{exp_leaf}-{csv_leaf}-{col}' + config.kStorageExt['csv']
            opath = self.batch_stat_collate_root / fname
            writer(df, opath, index=False)


__api__ = [
    'ExperimentalRunParallelCollator',
    'ExperimentalRunCSVGatherer',
    'ExperimentalRunCollator'


]
