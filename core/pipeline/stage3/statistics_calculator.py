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
import logging
import multiprocessing as mp
import typing as tp
import queue

# 3rd party packages
import pandas as pd
import matplotlib.cbook as mplcbook

# Project packages
import core.utils
import core.variables.batch_criteria as bc
import core.config


class BatchExpParallelCalculator:
    """
    Averages the .csv output files for each experiment in the specified batch directory in parallel.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary parsed cmdline parameters.
        batch_exp_root: Directory for averaged .csv output (relative to current dir or
                           absolute).
    """

    def __init__(self, main_config: dict, cmdopts: dict):
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, criteria: bc.IConcreteBatchCriteria) -> None:

        exp_to_avg = core.utils.exp_range_calc(self.cmdopts,
                                               self.cmdopts['batch_output_root'],
                                               criteria)

        template_input_leaf, _ = os.path.splitext(
            os.path.basename(self.cmdopts['template_input_file']))

        avg_opts = {
            'template_input_leaf': template_input_leaf,
            'no_verify_results': self.cmdopts['no_verify_results'],
            'dist_stats': self.cmdopts['dist_stats'],
            'project_imagizing': self.cmdopts['project_imagizing'],
        }

        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for exp in exp_to_avg:
            _, leaf = os.path.split(exp)
            output_path = os.path.join(self.cmdopts['batch_output_root'], leaf)
            stat_path = os.path.join(self.cmdopts['batch_stat_root'], leaf)
            q.put((output_path, stat_path))

        for i in range(0, mp.cpu_count()):
            p = mp.Process(target=BatchExpParallelCalculator._thread_worker,
                           args=(q, self.main_config, avg_opts))
            p.start()

        q.join()

    @staticmethod
    def _thread_worker(q: mp.Queue,
                       main_config: dict,
                       avg_opts: tp.Dict[str, str]) -> None:
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                output_path, stat_path = q.get(True, 3)
                ExpStatisticsCalculator(main_config, avg_opts, output_path, stat_path)()
                q.task_done()
            except queue.Empty:
                break


class ExpStatisticsCalculator:
    """Generate statistics from all of :term:`Output .csv` files from a set of
    :term:`Simulations<Simulation>` within a single :term:`Experiment`.

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
                 exp_output_root: str,
                 exp_stat_root: str) -> None:
        self.avg_opts = avg_opts

        # will get the main name and extension of the config file (without the full absolute path)
        self.template_input_fname = os.path.basename(self.avg_opts['template_input_leaf'])

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.main_config = main_config

        self.stat_root = exp_stat_root
        self.sim_metrics_leaf = main_config['sim']['sim_metrics_leaf']
        self.project_frames_leaf = main_config['sierra']['project_frames_leaf']
        self.argos_frames_leaf = main_config['sim']['argos_frames_leaf']
        self.videos_leaf = 'videos'
        self.project_imagize = avg_opts['project_imagizing']

        # To support inverted performance measures where smaller is better
        self.invert_perf = main_config['perf']['inverted']
        self.intra_perf_csv = main_config['perf']['intra_perf_csv']
        self.intra_perf_col = main_config['perf']['intra_perf_col']

        core.utils.dir_create_checked(self.stat_root, exist_ok=True)

        # to be formatted like: self.input_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.output_name_format = format_base + "_output"
        self.logger = logging.getLogger(__name__)

    def __call__(self):
        if not self.avg_opts['no_verify_results']:
            self._verify_exp()
        self._process_csvs()

    def _process_csvs(self):
        """Process the CSV files found in the output save path"""

        self.logger.info('Processing results: %s...', self.exp_output_root)

        pattern = self.output_name_format.format(re.escape(self.avg_opts['template_input_leaf']),
                                                 r'\d+')

        # Check to make sure all directories are simulation runs, skipping directories as needed.
        simulations = sim_dir_filter(os.listdir(self.exp_output_root),
                                     self.main_config,
                                     self.videos_leaf)

        assert(all(re.match(pattern, s) for s in simulations)),\
            "FATAL: Extraneous files/not all dirs in '{0}' are simulation runs".format(
                self.exp_output_root)

        # Maps (unique .csv stem, optional parent dir) to the averaged dataframe
        csvs = dict()  # type: tp.Dict[tp.Tuple[str, str], tp.List]
        for sim in simulations:
            self._gather_csvs_from_sim(sim, csvs)

        self._process_csvs_within_exp(csvs)

    def _gather_csvs_from_sim(self, sim: str, csvs: dict) -> None:
        csv_root = os.path.join(self.exp_output_root, sim, self.sim_metrics_leaf)

        # The metrics folder should contain nothing but .csv files and directories. For all
        # directories it contains, they each should contain nothing but .csv files (these are
        # for video rendering later).
        for item in os.listdir(csv_root):
            item_path = os.path.join(csv_root, item)
            item_stem = os.path.splitext(item)[0]
            if os.path.isfile(item_path):
                df = core.utils.pd_csv_read(item_path, index_col=False)
                if df.dtypes[0] == 'object':
                    df[df.columns[0]] = df[df.columns[0]].apply(lambda x: float(x))

                if (item_stem, '') not in csvs:
                    csvs[(item_stem, '')] = []

                csvs[(item_stem, '')].append(df)
            else:
                # This takes FOREVER, so only do it if we absolutely need to
                if not self.project_imagize:
                    continue
                for csv_fname in os.listdir(item_path):
                    csv_path = os.path.join(item_path, csv_fname)
                    df = core.utils.pd_csv_read(csv_path, index_col=False)
                    if (csv_fname, item_stem) not in csvs:
                        csvs[(csv_fname, item_stem)] = []
                    csvs[(csv_fname, item_stem)].append(df)

    def _process_csvs_within_exp(self, csvs: dict) -> None:
        # All CSV files with the same base name will be processed together
        for csv_fname in csvs:
            csv_concat = pd.concat(csvs[csv_fname])
            if (self.invert_perf and csv_fname[0] in self.intra_perf_csv):
                csv_concat[self.intra_perf_col] = 1.0 / csv_concat[self.intra_perf_col]
                self.logger.debug("Inverted performance column: df stem=%s,col=%s",
                                  csv_fname[0],
                                  self.intra_perf_col)

            # Create directory for averaged .csv files for imagizing later.
            if csv_fname[1] != '':
                core.utils.dir_create_checked(os.path.join(self.stat_root, csv_fname[1]),
                                              exist_ok=True)

            by_row_index = csv_concat.groupby(csv_concat.index)
            csv_fname_stem = csv_fname[0].split('.')[0]

            # We always at least calculate the mean
            csv_mean = by_row_index.mean()
            core.utils.pd_csv_write(csv_mean,
                                    os.path.join(self.stat_root,
                                                 csv_fname[1],
                                                 csv_fname[0]) + core.config.kStatsExtensions['mean'],
                                    index=False)

            # Write out standard deviation to calculate confidence intervals later
            if self.avg_opts['dist_stats'] == 'conf95' or self.avg_opts['dist_stats'] == 'all':
                csv_stddev = by_row_index.std().round(8)
                core.utils.pd_csv_write(csv_stddev,
                                        os.path.join(self.stat_root,
                                                     csv_fname_stem) + core.config.kStatsExtensions['stddev'],
                                        index=False)

            # Write out min, max, median, q1, q2 to calculate boxplots later
            if self.avg_opts['dist_stats'] == 'bw' or self.avg_opts['dist_stats'] == 'all':

                csv_min = by_row_index.min().round(8)
                csv_max = by_row_index.max().round(8)
                csv_median = by_row_index.median().round(8)
                csv_q1 = by_row_index.quantile(0.25).round(8)
                csv_q3 = by_row_index.quantile(0.75).round(8)

                csv_whislo = csv_q1 - 1.5 * (csv_q3 - csv_q1)
                csv_whishi = csv_q3 + 1.5 * (csv_q3 - csv_q1)

                core.utils.pd_csv_write(csv_min,
                                        os.path.join(self.stat_root,
                                                     csv_fname_stem + core.config.kStatsExtensions['mean']),
                                        index=False)

                core.utils.pd_csv_write(csv_max,
                                        os.path.join(self.stat_root,
                                                     csv_fname_stem + core.config.kStatsExtensions['max']),
                                        index=False)
                core.utils.pd_csv_write(csv_median,
                                        os.path.join(self.stat_root,
                                                     csv_fname_stem + core.config.kStatsExtensions['median']),
                                        index=False)
                core.utils.pd_csv_write(csv_q1,
                                        os.path.join(self.stat_root,
                                                     csv_fname_stem + core.config.kStatsExtensions['q1']),
                                        index=False)

                core.utils.pd_csv_write(csv_q3,
                                        os.path.join(self.stat_root,
                                                     csv_fname_stem + core.config.kStatsExtensions['q3']),
                                        index=False)

                core.utils.pd_csv_write(csv_whislo,
                                        os.path.join(self.stat_root,
                                                     csv_fname_stem + core.config.kStatsExtensions['whislo']),
                                        index=False)

                core.utils.pd_csv_write(csv_whishi,
                                        os.path.join(self.stat_root,
                                                     csv_fname_stem + core.config.kStatsExtensions['whishi']),
                                        index=False)

    def _verify_exp(self):
        """
        Verify the integrity of all simulations in an experiment.

        Specifically:

        - All simulations produced all ``.csv`` files.
        - All simulation ``.csv`` files have the same # rows/columns.
        - No simulation ``.csv``files contain NaNs.
        """
        experiments = sim_dir_filter(os.listdir(self.exp_output_root),
                                     self.main_config,
                                     self.videos_leaf)

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

                    assert (core.utils.path_exists(path1) and core.utils.path_exists(path2)),\
                        "FATAL: Either {0} or {1} does not exist".format(path1, path2)

                    # Verify both dataframes have same # columns, and that column sets are identical
                    df1 = core.utils.pd_csv_read(path1)
                    df2 = core.utils.pd_csv_read(path2)
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


def sim_dir_filter(exp_dirs: tp.List[str], main_config: dict, videos_leaf: str) -> tp.List[str]:
    project_frames_leaf = main_config['sierra']['project_frames_leaf']
    argos_frames_leaf = main_config['sim']['argos_frames_leaf']
    models_leaf = main_config['sierra']['models_leaf']

    return [e for e in exp_dirs if e not in [project_frames_leaf,
                                             argos_frames_leaf,
                                             videos_leaf,
                                             models_leaf]]
