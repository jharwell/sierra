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

"""
Classes for collating data from all :term:`Experimental Run` across all
:term:`Experiment` for all experiments in a :term:`Batch Experiment`. This is
needed to correctly calculate summary statistics for performance measures in
stage 4: you can't just run the calculated stddev through the calculations for
flexibility (for example) because comparing curves of stddev is not
meaningful. Stage 4 needs access to raw-(er) run data to construct a
`distribution` of performance measure values to then calculate the summary
statistics (such as stddev) over.

"""

# Core packages
import os
import multiprocessing as mp
import typing as tp
import queue
import logging  # type: tp.Any

# 3rd party packages
import pandas as pd
import numpy as np

# Project packages
import sierra.core.utils
import sierra.core.variables.batch_criteria as bc
import sierra.core.config
import sierra.core.storage as storage
import sierra.core.plugin_manager as pm
from sierra.core import types


class ExperimentalRunParallelCollator:
    """Gathers .csv output files from each :term:`Experimental Run` in each
    :term:`Experiment` for generating deliverables in stage 4 (in parallel for
    speed).

    """

    def __init__(self, main_config: dict, cmdopts: types.Cmdopts):
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:
        if self.cmdopts['serial_processing']:
            n_gatherers = 1
            n_processors = 1
        else:
            n_gatherers = int(mp.cpu_count() * 0.25)
            n_processors = int(mp.cpu_count() * 0.75)

        pool = mp.Pool(processes=n_gatherers + n_processors)

        m = mp.Manager()
        gatherq = m.Queue()
        processq = m.Queue()

        for exp in os.listdir(self.cmdopts['batch_output_root']):
            gatherq.put((self.cmdopts['batch_output_root'], exp))

        gathered = [pool.apply_async(ExperimentalRunParallelCollator._gather_worker,
                                     (gatherq,
                                      processq,
                                      self.main_config,
                                      self.cmdopts['project'],
                                      self.cmdopts['storage_medium'])) for _ in range(0, n_gatherers)]

        processed = [pool.apply_async(ExperimentalRunParallelCollator._process_worker,
                                      (processq,
                                       self.main_config,
                                       self.cmdopts['batch_stat_collate_root'],
                                       self.cmdopts['storage_medium'])) for _ in range(0, n_processors)]

        # To capture the otherwise silent crashes when something goes wrong in
        # worker threads. Any assertions will show and any exceptions will be
        # re-raised.
        [g.get() for g in gathered]
        [p.get() for p in processed]

        pool.close()
        pool.join()

    @staticmethod
    def _gather_worker(gatherq: mp.Queue,
                       processq: mp.Queue,
                       main_config: dict,
                       project: str,
                       storage_medium: str) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                batch_output_root, exp = gatherq.get(True, 3)
                module = pm.module_load_tiered(project=project,
                                               path='pipeline.stage3.run_collator')
                module.ExperimentalRunCSVGatherer(main_config,
                                                  batch_output_root,
                                                  exp,
                                                  storage_medium,
                                                  processq)()
                gatherq.task_done()

            except queue.Empty:
                break

    @staticmethod
    def _process_worker(processq: mp.Queue,
                        main_config: dict,
                        batch_stat_pm_root: str,
                        storage_medium) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                item = processq.get(True, 3)

                exp_leaf = list(item.keys())[0]
                gathered_runs, gathered_dfs = item[exp_leaf]
                ExperimentalRunCollator(main_config,
                                        batch_stat_pm_root,
                                        exp_leaf,
                                        storage_medium,
                                        gathered_runs,
                                        gathered_dfs)()
                processq.task_done()
            except queue.Empty:
                break


class ExperimentalRunCSVGatherer:
    """
    Gather necessary :term:`Output .csv` files from all :term:`Experimental Runs
    <Experimental Run>` within a single :term:`Experiment` so that performance
    measures can be generated during stage 4.

    This class can be extended/overriden using a :term:`Project` hook. See
    :ref:`ln-tutorials-project-hooks` for details.

    Attributes:
        processq: The multiprocessing-safe producer-consumer queue that the data
                  gathered from experimental runs will be placed in for
                  processing.

        exp_leaf: The name of the experiment directory within the
                  ``batch_output_root``.

        storage_medium: The name of the storage medium plugin to use to extract
                        dataframes from when reading run data.

        exp_output_root: The absolute path to the experiment directory to gather
                         data from.

        main_config: Parsed dictionary of main YAML configuration.

        run_metrics_leaf: The name of the directory within the output directory
                          for each experimental run in which the data can be
                          found.

        logger: The handle to the logger for this class. If you extend this
                class, you should save/restore this variable in tandem with
                overriding it in order to get loggingmessages have unique
                logger names between this class and your derived class, in order
                to reduce confusion.

    """

    def __init__(self,
                 main_config: dict,
                 batch_output_root: str,
                 exp_leaf: str,
                 storage_medium: str,
                 processq: mp.Queue) -> None:
        self.processq = processq

        self.exp_leaf = exp_leaf
        self.storage_medium = storage_medium
        self.exp_output_root = os.path.join(batch_output_root, exp_leaf)
        self.main_config = main_config

        self.run_metrics_leaf = main_config['sierra']['run']['run_metrics_leaf']

        self.logger = logging.getLogger(__name__)

    def __call__(self):
        """
        Gather data from all experimental runs within a single experiment and
        put them in the queue for processing.
        """
        self.logger.info('Gathering .csvs: %s...', self.exp_leaf)

        runs = sorted(os.listdir(self.exp_output_root))

        gathered = []
        for run in runs:
            gathered.append(self.gather_csvs_from_run(run))

        self.processq.put({self.exp_leaf: (runs, gathered)})

    def gather_csvs_from_run(self,
                             run: str) -> tp.Dict[tp.Tuple[str, str], pd.DataFrame]:
        """
        Gather all data from a single run within an experiment, so that
        it can be placed in the queue for processing.

        Returns:
           A dictionary of <(``.csv`` file name, ``.csv`` performance column),
           dataframe> key-value pairs. The ``.csv`` file name is the leaf part
           of the path with the extension included.
        """

        intra_perf_csv = self.main_config['sierra']['perf']['intra_perf_csv']
        intra_perf_leaf = intra_perf_csv.split('.')[0]
        intra_perf_col = self.main_config['sierra']['perf']['intra_perf_col']

        run_output_root = os.path.join(self.exp_output_root,
                                       run,
                                       self.run_metrics_leaf)

        reader = storage.DataFrameReader(self.storage_medium)
        perf_df = reader(os.path.join(run_output_root,
                                      intra_perf_leaf + '.csv'),
                         index_col=False)

        return {
            (intra_perf_leaf, intra_perf_col): perf_df[intra_perf_col],
        }


class ExperimentalRunCollator:
    """
    Collate gathered .csvs together gathered from N :term:`Experimental Runs
    <Experimental Run>` together into a single :term:`Summary .csv` per
    experiment with 1 column per run.

    """

    def __init__(self,
                 main_config: dict,
                 batch_stat_collate_root: str,
                 exp_leaf: str,
                 storage_medium: str,
                 gathered_runs: tp.List[str],
                 gathered_dfs: tp.List[tp.Dict[tp.Tuple[str, str], pd.DataFrame]]) -> None:
        self.exp_leaf = exp_leaf
        self.storage_medium = storage_medium
        self.gathered_runs = gathered_runs
        self.gathered_dfs = gathered_dfs

        self.main_config = main_config
        self.batch_stat_collate_root = batch_stat_collate_root

        # To support inverted performance measures where smaller is better
        self.invert_perf = main_config['sierra']['perf'].get('inverted', False)
        self.intra_perf_csv = main_config['sierra']['perf']['intra_perf_csv']

        sierra.core.utils.dir_create_checked(
            self.batch_stat_collate_root, exist_ok=True)

    def __call__(self):
        collated = {}
        for run in self.gathered_runs:
            run_dfs = self.gathered_dfs[self.gathered_runs.index(run)]
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
                                                             columns=self.gathered_runs)
                collated[(csv_leaf, col)][run] = csv_df

        for (csv_leaf, col) in collated.keys():

            writer = storage.DataFrameWriter(self.storage_medium)
            writer(collated[(csv_leaf, col)].fillna(0),
                   os.path.join(self.batch_stat_collate_root,
                                self.exp_leaf + '-' + csv_leaf + '-' + col + '.csv'),
                   index=False)


__api__ = [
    'ExperimentalRunParallelCollator',
    'ExperimentalRunCSVGatherer',
    'ExperimentalRunCollator'
]