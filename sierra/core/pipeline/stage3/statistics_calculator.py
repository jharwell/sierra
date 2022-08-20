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
Classes for generating statistics within and across experiments in a batch.
"""

# Core packages
import re
import multiprocessing as mp
import typing as tp
import queue
import time
import datetime
import logging
import pathlib

# 3rd party packages
import pandas as pd
import psutil

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, utils, stat_kernels, storage, config


class GatherSpec:
    """
    Data class for specifying .csv files to gather from an :term:`Experiment`.
    """

    def __init__(self,
                 exp_name: str,
                 item_stem: str,
                 imagize_csv_stem: tp.Optional[str]):
        self.exp_name = exp_name
        self.item_stem = item_stem
        self.imagize_csv_stem = imagize_csv_stem

    def for_imagizing(self):
        return self.imagize_csv_stem is not None


class BatchExpParallelCalculator:
    """Process :term:`Output .csv` files for each experiment in the batch.

    In parallel for speed.
    """

    def __init__(self, main_config: dict, cmdopts: types.Cmdopts):
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:

        exp_to_avg = utils.exp_range_calc(self.cmdopts,
                                          self.cmdopts['batch_output_root'],
                                          criteria)

        template_input_leaf = pathlib.Path(self.cmdopts['template_input_file']).stem

        avg_opts = {
            'template_input_leaf': template_input_leaf,
            'df_skip_verify': self.cmdopts['df_skip_verify'],
            'dist_stats': self.cmdopts['dist_stats'],
            'project_imagizing': self.cmdopts['project_imagizing'],
            'processing_mem_limit': self.cmdopts['processing_mem_limit'],
            'storage_medium': self.cmdopts['storage_medium'],
            'df_homogenize': self.cmdopts['df_homogenize']
        }

        if self.cmdopts['processing_serial']:
            n_gatherers = 1
            n_processors = 1
        else:
            # Aways need to have at least one of each! If SIERRA is invoked on a
            # machine with 2 or less logical cores, the calculation with
            # psutil.cpu_count() will return 0 for # gatherers.
            n_gatherers = max(1, int(psutil.cpu_count() * 0.25))
            n_processors = max(1, int(psutil.cpu_count() * 0.75))

        with mp.Pool(processes=n_gatherers + n_processors) as pool:
            self._execute(exp_to_avg, avg_opts, n_gatherers, n_processors, pool)

    def _execute(self,
                 exp_to_avg: tp.List[pathlib.Path],
                 avg_opts: types.SimpleDict,
                 n_gatherers: int,
                 n_processors: int,
                 pool) -> None:
        m = mp.Manager()
        gatherq = m.Queue()
        processq = m.Queue()

        for exp in exp_to_avg:
            gatherq.put(exp)

        # Start some threads gathering .csvs first to get things rolling.
        self.logger.debug("Starting %d gatherers, method=%s",
                          n_gatherers,
                          mp.get_start_method())
        gathered = [pool.apply_async(BatchExpParallelCalculator._gather_worker,
                                     (gatherq,
                                      processq,
                                      self.main_config,
                                      avg_opts)) for i in range(0, n_gatherers)]

        self.logger.debug("Starting %d processors, method=%s",
                          n_processors,
                          mp.get_start_method())
        processed = [pool.apply_async(BatchExpParallelCalculator._process_worker,
                                      (processq,
                                       self.main_config,
                                       self.cmdopts['batch_stat_root'],
                                       avg_opts)) for i in range(0, n_processors)]

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
                       avg_opts: tp.Dict[str, str]) -> None:
        gatherer = ExpCSVGatherer(main_config, avg_opts, processq)

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

    @staticmethod
    def _process_worker(processq: mp.Queue,
                        main_config: types.YAMLDict,
                        batch_stat_root: pathlib.Path,
                        avg_opts: tp.Dict[str, str]) -> None:
        calculator = ExpStatisticsCalculator(main_config,
                                             avg_opts,
                                             batch_stat_root)

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
                item = processq.get(True, timeout)
                key = list(item.keys())[0]

                calculator(key, item[key])
                processq.task_done()
                got_item = True

            except queue.Empty:
                if got_item:
                    break

                timeout *= 2
                n_tries += 1


class ExpCSVGatherer:
    """Gather all :term:`Output .csv` files from all runs within an experiment.

    "Gathering" in this context means creating a dictionary mapping which .csv
    came from where, so that statistics can be generated both across and with
    experiments in the batch.
    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 gather_opts: dict,
                 processq: mp.Queue) -> None:
        self.processq = processq
        self.gather_opts = gather_opts

        # Will get the main name and extension of the config file (without the
        # full absolute path).
        self.template_input_fname = self.gather_opts['template_input_leaf']

        self.main_config = main_config

        self.run_metrics_leaf = main_config['sierra']['run']['run_metrics_leaf']
        self.videos_leaf = 'videos'
        self.project_imagize = gather_opts['project_imagizing']

        self.logger = logging.getLogger(__name__)

    def __call__(self, exp_output_root: pathlib.Path) -> None:
        """Process the CSV files found in the output save path."""
        if not self.gather_opts['df_skip_verify']:
            self._verify_exp_outputs(exp_output_root)

        self.logger.info('Processing .csvs: %s...', exp_output_root.name)

        pattern = "{}_{}_output".format(re.escape(self.gather_opts['template_input_leaf']),
                                        r'\d+')

        runs = list(exp_output_root.iterdir())
        assert(all(re.match(pattern, r.name) for r in runs)),\
            f"Extra files/not all dirs in '{exp_output_root}' are exp runs"

        # Maps (unique .csv stem, optional parent dir) to the averaged dataframe
        to_gather = self._calc_gather_items(runs[0], exp_output_root.name)

        for item in to_gather:
            self._wait_for_memory()
            gathered = self._gather_item_from_sims(exp_output_root, item, runs)

            # Put gathered .csv list  in the process queue
            self.processq.put(gathered)

        self.logger.debug("Enqueued %s items from %s for processing",
                          len(to_gather),
                          exp_output_root.name)

    def _calc_gather_items(self,
                           run_output_root: pathlib.Path,
                           exp_name: str) -> tp.List[GatherSpec]:
        to_gather = []

        sim_output_root = run_output_root / self.run_metrics_leaf

        # The metrics folder should contain nothing but .csv files and
        # directories. For all directories it contains, they each should contain
        # nothing but .csv files (these are for video rendering later).
        for item in sim_output_root.iterdir():
            csv_stem = item.stem

            if item.is_file():
                to_gather.append(GatherSpec(exp_name=exp_name,
                                            item_stem=csv_stem,
                                            imagize_csv_stem=None))
            else:
                # This takes FOREVER, so only do it if we absolutely need to
                if not self.project_imagize:
                    continue

                for csv_fname in item.iterdir():
                    to_gather.append(GatherSpec(exp_name=exp_name,
                                                item_stem=csv_stem,
                                                imagize_csv_stem=csv_fname.stem))

        return to_gather

    def _gather_item_from_sims(self,
                               exp_output_root: pathlib.Path,
                               item: GatherSpec,
                               runs: tp.List[pathlib.Path]) -> tp.Dict[GatherSpec,
                                                                       tp.List[pd.DataFrame]]:
        gathered = {}  # type: tp.Dict[GatherSpec, pd.DataFrame]

        for run in runs:
            sim_output_root = run / self.run_metrics_leaf

            if item.for_imagizing():
                item_path = sim_output_root / item.item_stem / \
                    (item.imagize_csv_stem + config.kStorageExt['csv'])
            else:
                item_path = sim_output_root / \
                    (item.item_stem + config.kStorageExt['csv'])

            reader = storage.DataFrameReader(self.gather_opts['storage_medium'])
            df = reader(item_path, index_col=False)

            if df.dtypes[0] == 'object':
                df[df.columns[0]] = df[df.columns[0]].apply(lambda x: float(x))

            if item not in gathered:
                gathered[item] = []

            gathered[item].append(df)

        return gathered

    def _wait_for_memory(self) -> None:
        while True:
            mem = psutil.virtual_memory()
            avail = mem.available / mem.total
            free_percent = avail * 100
            free_limit = 100 - self.gather_opts['processing_mem_limit']

            if free_percent >= free_limit:
                return

            self.logger.info("Waiting for memory: avail=%s,min=%s",
                             free_percent,
                             free_limit)
            time.sleep(1)

    def _verify_exp_outputs(self, exp_output_root: pathlib.Path) -> None:
        """
        Verify the integrity of all runs in an experiment.

        Specifically:

        - All runs produced all CSV files.

        - All runs CSV files with the same name have the same # rows and
          columns.

        - No CSV files contain NaNs.
        """
        experiments = exp_output_root.iterdir()

        self.logger.info('Verifying results in %s...', str(exp_output_root))

        start = time.time()

        for exp1 in experiments:
            csv_root1 = exp1 / self.run_metrics_leaf

            for exp2 in experiments:
                csv_root2 = exp2 / self.run_metrics_leaf

                if not csv_root2.is_dir():
                    continue

                self._verify_exp_outputs_pairwise(csv_root1, csv_root2)

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Done verifying results in %s: %s",
                         exp_output_root,
                         sec)

    def _verify_exp_outputs_pairwise(self,
                                     csv_root1: pathlib.Path,
                                     csv_root2: pathlib.Path) -> None:
        for csv in csv_root2.iterdir():
            path1 = csv
            path2 = csv_root2 / csv.name

            # .csvs for rendering that we don't verify (for now...)
            if path1.is_dir() or path2.is_dir():
                self.logger.debug("Not verifying '%s': contains rendering data",
                                  str(path1))
                continue

            assert (utils.path_exists(path1) and utils.path_exists(path2)),\
                f"Either {path1} or {path2} does not exist"

            # Verify both dataframes have same # columns, and that
            # column sets are identical
            reader = storage.DataFrameReader(self.gather_opts['storage_medium'])
            df1 = reader(path1)
            df2 = reader(path2)

            assert (len(df1.columns) == len(df2.columns)), \
                (f"Dataframes from {path1} and {path2} do not have "
                 "the same # columns")
            assert(sorted(df1.columns) == sorted(df2.columns)),\
                f"Columns from {path1} and {path2} not identical"

            # Verify the length of all columns in both dataframes is the same
            for c1 in df1.columns:
                assert(all(len(df1[c1]) == len(df1[c2]) for c2 in df1.columns)),\
                    f"Not all columns from {path1} have same length"

                assert(all(len(df1[c1]) == len(df2[c2]) for c2 in df1.columns)),\
                    (f"Not all columns from {path1} and {path2} have "
                     "the same length")


class ExpStatisticsCalculator:
    """Generate statistics from output files for all runs within an experiment.

    .. IMPORTANT:: You *CANNOT* use logging ANYWHERE during processing .csv
       files. Why ? I *think* because of a bug in the logging module itself. If
       you get unlucky enough to spawn the process which enters the __call__()
       method in this class while another logging statement is in progress (and
       is therefore holding an internal logging module lock), then the
       underlying fork() call will copy the lock in the acquired state. Then,
       when this class goes to try to log something, it deadlocks with itself.

       You also can't just create loggers with unique names, as this seems to be
       something like the GIL, but for the logging module. Sometimes python
       sucks.
    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 avg_opts: dict,
                 batch_stat_root: pathlib.Path) -> None:
        self.avg_opts = avg_opts

        # will get the main name and extension of the config file (without the
        # full absolute path)
        self.template_input_fname = self.avg_opts['template_input_leaf']

        self.main_config = main_config
        self.batch_stat_root = batch_stat_root

        self.intra_perf_csv = main_config['sierra']['perf']['intra_perf_csv']
        self.intra_perf_col = main_config['sierra']['perf']['intra_perf_col']

    def __call__(self,
                 gather_spec: GatherSpec,
                 gathered_dfs: tp.List[pd.DataFrame]) -> None:

        csv_concat = pd.concat(gathered_dfs)

        exp_stat_root = self.batch_stat_root / gather_spec.exp_name
        utils.dir_create_checked(exp_stat_root, exist_ok=True)

        # Create directory for averaged .csv files for imagizing later.
        if gather_spec.for_imagizing():
            utils.dir_create_checked(exp_stat_root / gather_spec.item_stem,
                                     exist_ok=True)

        by_row_index = csv_concat.groupby(csv_concat.index)

        dfs = {}
        if self.avg_opts['dist_stats'] in ['none', 'all']:
            dfs.update(stat_kernels.mean.from_groupby(by_row_index))

        if self.avg_opts['dist_stats'] in ['conf95', 'all']:
            dfs.update(stat_kernels.conf95.from_groupby(by_row_index))

        if self.avg_opts['dist_stats'] in ['bw', 'all']:
            dfs.update(stat_kernels.bw.from_groupby(by_row_index))

        for ext in dfs:
            opath = exp_stat_root / gather_spec.item_stem

            if gather_spec.for_imagizing():
                opath /= (gather_spec.imagize_csv_stem + ext)

            else:
                opath = opath.with_suffix(ext)

            df = utils.df_fill(dfs[ext], self.avg_opts['df_homogenize'])
            writer = storage.DataFrameWriter(self.avg_opts['storage_medium'])
            writer(df, opath, index=False)


__api__ = [
    'GatherSpec',
    'BatchExpParallelCalculator',
    'ExpCSVGatherer',
    'ExpStatisticsCalculator'
]
