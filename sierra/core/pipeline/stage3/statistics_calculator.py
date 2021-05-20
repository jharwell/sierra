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
Classes for generating statistics from all :term:`Simulation` results within an :term:`Experiment`
for all experiments in a :term:`Batch Experiment`.
"""

# Core packages
import os
import re
import multiprocessing as mp
import typing as tp
import queue
import time
import logging

# 3rd party packages
import pandas as pd
import psutil

# Project packages
import sierra.core.utils
import sierra.core.variables.batch_criteria as bc
import sierra.core.config
import sierra.core.stat_kernels


class BatchExpParallelCalculator:
    """
    Averages the .csv output files for each experiment in the specified batch directory in parallel.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary parsed cmdline parameters.
        batch_exp_root: Directory for averaged .csv output (relative to current dir or
                           absolute).
    """

    def __init__(self, main_config: dict, cmdopts: tp.Dict[str, tp.Any]):
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:

        exp_to_avg = sierra.core.utils.exp_range_calc(self.cmdopts,
                                               self.cmdopts['batch_output_root'],
                                               criteria)

        template_input_leaf, _ = os.path.splitext(
            os.path.basename(self.cmdopts['template_input_file']))

        avg_opts = {
            'template_input_leaf': template_input_leaf,
            'no_verify_results': self.cmdopts['no_verify_results'],
            'dist_stats': self.cmdopts['dist_stats'],
            'project_imagizing': self.cmdopts['project_imagizing'],
            'processing_mem_limit': self.cmdopts['processing_mem_limit']
        }

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

        for exp in exp_to_avg:
            _, leaf = os.path.split(exp)
            gatherq.put((self.cmdopts['batch_output_root'], leaf))

        # Start some threads gathering .csvs first to get things rolling.
        gathered = [pool.apply_async(BatchExpParallelCalculator._gather_worker,
                                     (gatherq,
                                      processq,
                                      self.main_config,
                                      avg_opts)) for i in range(0, n_gatherers)]

        processed = [pool.apply_async(BatchExpParallelCalculator._process_worker,
                                      (processq,
                                       self.main_config,
                                       self.cmdopts['batch_stat_root'],
                                       avg_opts)) for i in range(0, n_processors)]

        # To capture the otherwise silent crashes when something goes wrong in worker threads. Any
        # assertions will show and any exceptions will be re-raised.
        [g.get() for g in gathered]
        [p.get() for p in processed]

        pool.close()
        pool.join()

    @staticmethod
    def _gather_worker(gatherq: mp.Queue,
                       processq: mp.Queue,
                       main_config: dict,
                       avg_opts: tp.Dict[str, str]) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                batch_output_root, exp = gatherq.get(True, 3)
                ExpCSVGatherer(main_config, avg_opts, batch_output_root, exp, processq)()
                gatherq.task_done()

            except queue.Empty:
                break

    @staticmethod
    def _process_worker(processq: mp.Queue,
                        main_config: dict,
                        batch_stat_root: str,
                        avg_opts: tp.Dict[str, str]) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                item = processq.get(True, 3)

                key = list(item.keys())[0]
                ExpStatisticsCalculator(main_config,
                                        avg_opts,
                                        batch_stat_root,
                                        key,
                                        item[key])()
                processq.task_done()
            except queue.Empty:
                break


class ExpCSVGatherer:
    """Gather all :term:`Output .csv` files from a set of :term:`Simulations<Simulation>` within a
    single :term:`Experiment`.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        template_input_leaf: Leaf(i.e. no preceding path to the template XML configuration file
                                  for the experiment.
        no_verify: Should result verification be skipped?

    """

    def __init__(self,
                 main_config: dict,
                 gather_opts: dict,
                 batch_output_root: str,
                 exp_leaf: str,
                 processq: mp.Queue) -> None:
        self.processq = processq
        self.gather_opts = gather_opts

        # will get the main name and extension of the config file (without the full absolute path)
        self.template_input_fname = os.path.basename(self.gather_opts['template_input_leaf'])

        self.exp_leaf = exp_leaf
        self.exp_output_root = os.path.join(batch_output_root, exp_leaf)
        self.main_config = main_config

        self.sim_metrics_leaf = main_config['sim']['sim_metrics_leaf']
        self.videos_leaf = 'videos'
        self.project_imagize = gather_opts['project_imagizing']

        # to be formatted like: self.input_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.output_name_format = format_base + "_output"

        self.logger = logging.getLogger(__name__)

    def __call__(self):
        """Process the CSV files found in the output save path"""
        if not self.gather_opts['no_verify_results']:
            self._verify_exp()

        self.logger.info('Processing .csvs: %s...', self.exp_leaf)

        pattern = self.output_name_format.format(re.escape(self.gather_opts['template_input_leaf']),
                                                 r'\d+')

        simulations = os.listdir(self.exp_output_root)

        assert(all(re.match(pattern, s) for s in simulations)),\
            "FATAL: Extraneous files/not all dirs in '{0}' are simulation runs".format(
                self.exp_output_root)

        # Maps (unique .csv stem, optional parent dir) to the averaged dataframe
        to_gather = self._calc_gather_items(simulations[0])

        for item in to_gather:
            self._wait_for_memory()
            gathered = self._gather_item_from_sims(item, simulations)
            # Put gathered .csv list  in the process queue

            self.processq.put(gathered)

        self.logger.debug("Enqueued %s items from %s for processing",
                          len(to_gather),
                          self.exp_leaf)

    def _calc_gather_items(self, sim0: str) -> tp.List[tp.Tuple[str, str, str]]:
        sim_output_root = os.path.join(self.exp_output_root, sim0, self.sim_metrics_leaf)
        to_gather = []

        # The metrics folder should contain nothing but .csv files and directories. For all
        # directories it contains, they each should contain nothing but .csv files (these are
        # for video rendering later).
        for item in os.listdir(sim_output_root):
            item_path = os.path.join(sim_output_root, item)
            item_stem = os.path.splitext(item)[0]

            if os.path.isfile(item_path):
                to_gather.append((self.exp_leaf, item_stem, ''))
            else:
                # This takes FOREVER, so only do it if we absolutely need to
                if not self.project_imagize:
                    continue

                for csv in os.listdir(item_path):
                    to_gather.append((self.exp_leaf, csv, item_stem))
        return to_gather

    def _gather_item_from_sims(self,
                               item: tp.Tuple[str, str, str],
                               simulations: tp.List[str]) -> tp.Dict[tp.Tuple[str, str, str],
                                                                     tp.List[pd.DataFrame]]:
        exp_leaf, csv_stem, dir_leaf = item
        gathered = dict()  # type: tp.Dict[tp.Tuple[str, str, str], pd.DataFrame]

        for sim in simulations:
            sim_output_root = os.path.join(self.exp_output_root, sim, self.sim_metrics_leaf)

            if dir_leaf != '':
                item_path = os.path.join(sim_output_root, dir_leaf, csv_stem)
            else:
                item_path = os.path.join(sim_output_root, dir_leaf, csv_stem + '.csv')

            df = sierra.core.utils.pd_csv_read(item_path, index_col=False)
            if df.dtypes[0] == 'object':
                df[df.columns[0]] = df[df.columns[0]].apply(lambda x: float(x))

            if item not in gathered:
                gathered[item] = []

            gathered[item].append(df)

        return gathered

    def _wait_for_memory(self):
        while True:
            mem = psutil.virtual_memory()
            avail = mem.available / mem.total
            free_percent = avail * 100
            free_limit = 100 - int(self.gather_opts['processing_mem_limit'])

            if free_percent >= free_limit:
                return

            time.sleep(1)

    def _verify_exp(self):
        """
        Verify the integrity of all simulations in an experiment.

        Specifically:

        - All simulations produced all ``.csv`` files.
        - All simulation ``.csv`` files have the same # rows/columns.
        - No simulation ``.csv``files contain NaNs.
        """
        experiments = os.listdir(self.exp_output_root)

        self.logger.info('Verifying results in %s...', self.exp_output_root)

        for exp1 in experiments:
            csv_root1 = os.path.join(self.exp_output_root,
                                     exp1,
                                     self.sim_metrics_leaf)

            for exp2 in experiments:
                csv_root2 = os.path.join(self.exp_output_root,
                                         exp2,
                                         self.sim_metrics_leaf)

                if not os.path.isdir(csv_root2):
                    continue

                for csv in os.listdir(csv_root2):
                    path1 = os.path.join(csv_root1, csv)
                    path2 = os.path.join(csv_root2, csv)

                    # .csvs for rendering that we don't verify (for now...)
                    if os.path.isdir(path1) or os.path.isdir(path2):
                        self.logger.debug("Not verifying %s: contains rendering data",
                                          path1)
                        continue

                    assert (sierra.core.utils.path_exists(path1) and sierra.core.utils.path_exists(path2)),\
                        "FATAL: Either {0} or {1} does not exist".format(path1, path2)

                    # Verify both dataframes have same # columns, and that column sets are identical
                    df1 = sierra.core.utils.pd_csv_read(path1)
                    df2 = sierra.core.utils.pd_csv_read(path2)
                    assert (len(df1.columns) == len(df2.columns)), \
                        "FATAL: Dataframes from {0} and {1} do not have same # columns".format(
                            path1, path2)
                    assert(sorted(df1.columns) == sorted(df2.columns)),\
                        "FATAL: Columns from {0} and {1} not identical".format(path1, path2)

                    # Verify the length of all columns in both dataframes is the same
                    for c1 in df1.columns:
                        assert(all(len(df1[c1]) == len(df1[c2]) for c2 in df1.columns)),\
                            "FATAL: Not all columns from {0} have same length".format(path1)
                        assert(all(len(df1[c1]) == len(df2[c2]) for c2 in df1.columns)),\
                            "FATAL: Not all columns from {0} and {1} have same length".format(path1,
                                                                                              path2)


class ExpStatisticsCalculator:
    """Generate statistics from all of :term:`Output .csv` files from a set of
    :term:`Simulations<Simulation>` within a single :term:`Experiment`.

    .. IMPORTANT:: You *CANNOT* use logging ANYWHERE during processing .csv files. Why ? I *think*
       because of a bug in the logging module itself. If you get unlucky enough to spawn the process
       which enters the __call__() method in this class while another logging statement is in
       progress (and is therefore holding an internal logging module lock), then the underlying
       fork() call will copy the lock in the acquired state. Then, when this class goes to try to
       log something, it deadlocks with itself.

       You also can't just create loggers with unique names, as this seems to be something like the
       GIL, but for the logging module. Sometimes python sucks.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        template_input_leaf: Leaf(i.e. no preceding path to the template XML configuration file
                                  for the experiment.
        no_verify: Should result verification be skipped?
        exp_output_root: Directory for averaged .csv output(relative to current dir or
                         absolute).

    """

    def __init__(self,
                 main_config: dict,
                 avg_opts: dict,
                 batch_stat_root: str,
                 gathered_key: tp.Tuple[str, str, str],
                 gathered_dfs: tp.List[pd.DataFrame]) -> None:
        self.avg_opts = avg_opts
        self.gathered_key = gathered_key
        self.gathered_dfs = gathered_dfs

        # will get the main name and extension of the config file (without the full absolute path)
        self.template_input_fname = os.path.basename(self.avg_opts['template_input_leaf'])

        self.main_config = main_config

        self.stat_root = os.path.join(batch_stat_root, gathered_key[0])
        self.project_imagize = avg_opts['project_imagizing']

        self.intra_perf_csv = main_config['perf']['intra_perf_csv']
        self.intra_perf_col = main_config['perf']['intra_perf_col']

        sierra.core.utils.dir_create_checked(self.stat_root, exist_ok=True)

        # to be formatted like: self.input_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.output_name_format = format_base + "_output"

    def __call__(self):
        # All CSV files with the same base name will be processed together
        exp_leaf, csv_fname, dir_leaf = self.gathered_key

        csv_concat = pd.concat(self.gathered_dfs)

        # Create directory for averaged .csv files for imagizing later.
        if dir_leaf != '':
            sierra.core.utils.dir_create_checked(os.path.join(self.stat_root, dir_leaf),
                                          exist_ok=True)

        by_row_index = csv_concat.groupby(csv_concat.index)

        if self.avg_opts['dist_stats'] in ['conf95', 'all']:
            dfs = sierra.core.stat_kernels.conf95.from_groupby(by_row_index)
            for ext in dfs.keys():
                opath = os.path.join(self.stat_root, dir_leaf, csv_fname + ext)
                sierra.core.utils.pd_csv_write(dfs[ext], opath, index=False)

        if self.avg_opts['dist_stats'] in ['bw', 'all']:
            dfs = sierra.core.stat_kernels.bw.from_groupby(by_row_index)
            for ext in dfs.keys():
                opath = os.path.join(self.stat_root, dir_leaf, csv_fname + ext)
                sierra.core.utils.pd_csv_write(dfs[ext], opath, index=False)
