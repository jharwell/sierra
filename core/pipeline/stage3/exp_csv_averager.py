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
Classes for averaging (1) all simulations within an experiment, (2) all experiments in a batched
experiment.
"""

import os
import re
import logging
import multiprocessing as mp
import typing as tp
import queue

import pandas as pd


import core.utils
import core.variables.batch_criteria as bc


class BatchedExpCSVAverager:
    """
    Averages the .csv output files for each experiment in the specified batch directory.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        cmdopts: Dictionary parsed cmdline parameters.
        batch_exp_root: Directory for averaged .csv output (relative to current dir or
                           absolute).
    """

    def __init__(self, main_config: dict, cmdopts: dict, batch_output_root: str):
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.batch_output_root = batch_output_root

    def __call__(self, criteria: bc.IConcreteBatchCriteria):

        exp_to_avg = core.utils.exp_range_calc(self.cmdopts, self.batch_output_root, criteria)

        template_input_leaf, _ = os.path.splitext(
            os.path.basename(self.cmdopts['template_input_file']))

        avg_opts = {
            'template_input_leaf': template_input_leaf,
            'no_verify_results': self.cmdopts['no_verify_results'],
            'gen_stddev': self.cmdopts['gen_stddev'],
            'project_imagizing': self.cmdopts['project_imagizing'],
        }

        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        for exp in exp_to_avg:
            path = os.path.join(self.batch_output_root, exp)
            if os.path.isdir(path):
                q.put(path)

        for i in range(0, mp.cpu_count()):
            p = mp.Process(target=BatchedExpCSVAverager.__thread_worker,
                           args=(q, self.main_config, avg_opts))
            p.start()

        q.join()

    @staticmethod
    def __thread_worker(q: mp.Queue, main_config: dict, avg_opts: tp.Dict[str, str]):
        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                path = q.get(True, 3)
                ExpCSVAverager(main_config, avg_opts, path)()
                q.task_done()
            except queue.Empty:
                break


class ExpCSVAverager:
    """
    Averages a set of .csv output files from a set of simulation runs for a single experiment.

    Attributes:
        main_config: Parsed dictionary of main YAML configuration.
        template_input_leaf: Leaf(i.e. no preceding path to the template XML configuration file
                                  for the experiment.
        no_verify: Should result verification be skipped?
        gen_stddev: Should standard deviation be generated(and therefore errorbars
                    plotted)?
        exp_output_root: Directory for averaged .csv output(relative to current dir or
                         absolute).
    """

    def __init__(self, main_config: dict, avg_opts: tp.Dict[str, str], exp_output_root: str) -> None:
        self.avg_opts = avg_opts

        # will get the main name and extension of the config file (without the full absolute path)
        self.template_input_fname, _ = os.path.splitext(
            os.path.basename(self.avg_opts['template_input_leaf']))

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.main_config = main_config

        self.avgd_output_leaf = main_config['sierra']['avg_output_leaf']
        self.avgd_output_root = os.path.join(self.exp_output_root,
                                             self.avgd_output_leaf)
        self.sim_metrics_leaf = main_config['sim']['sim_metrics_leaf']
        self.project_frames_leaf = main_config['sierra']['project_frames_leaf']
        self.argos_frames_leaf = main_config['sim']['argos_frames_leaf']
        self.videos_leaf = 'videos'
        self.project_imagize = avg_opts['project_imagizing']

        # To support inverted performance measures where smaller is better
        self.invert_perf = main_config['perf']['inverted']
        self.intra_perf_csv = main_config['perf']['intra_perf_csv']
        self.intra_perf_col = main_config['perf']['intra_perf_col']

        core.utils.dir_create_checked(self.avgd_output_root, exist_ok=True)

        # to be formatted like: self.input_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.output_name_format = format_base + "_output"

    def __call__(self):
        if not self.avg_opts['no_verify_results']:
            self.__verify_exp()
        self.__average_csvs()

    def __average_csvs(self):
        """Averages the CSV files found in the output save path"""

        logging.info('Averaging results in %s...', self.exp_output_root)

        # Maps (unique .csv stem, optional parent dir) to the averaged dataframe
        csvs = {}

        pattern = self.output_name_format.format(
            re.escape(self.avg_opts['template_input_leaf']), r'\d+')

        # Check to make sure all directories are simulation runs, skipping directories as needed.
        simulations = sim_dir_filter(os.listdir(self.exp_output_root),
                                     self.main_config, self.videos_leaf)

        assert(all(re.match(pattern, s) for s in simulations)),\
            "FATAL: Not all directories in {0} are simulation runs".format(self.exp_output_root)

        csvs = {}
        for sim in simulations:
            self.__gather_csvs_from_sim(sim, csvs)

        self.__average_csvs_within_exp(csvs)

    def __gather_csvs_from_sim(self, sim: str, csvs: dict):
        csv_root = os.path.join(self.exp_output_root, sim, self.sim_metrics_leaf)

        # The metrics folder should contain nothing but .csv files and directories. For all
        # directories it contains, they each should contain nothing but .csv files (these are
        # for video rendering later).
        for item in os.listdir(csv_root):
            item_path = os.path.join(csv_root, item)
            if os.path.isfile(item_path):
                df = core.utils.pd_csv_read(item_path, index_col=False)

                if (item, '') not in csvs:
                    csvs[(item, '')] = []

                csvs[(item, '')].append(df)
            else:
                # This takes FOREVER, so only do it if we absolutely need to
                if not self.project_imagize:
                    continue
                for csv_fname in os.listdir(item_path):
                    csv_path = os.path.join(item_path, csv_fname)
                    df = core.utils.pd_csv_read(csv_path, index_col=False)
                    if (csv_fname, item) not in csvs:
                        csvs[(csv_fname, item)] = []
                    csvs[(csv_fname, item)].append(df)

    def __average_csvs_within_exp(self, csvs: dict):
        # All CSV files with the same base name will be averaged together
        for csv_fname in csvs:
            csv_concat = pd.concat(csvs[csv_fname])
            if (self.invert_perf and csv_fname[0] in self.intra_perf_csv):
                csv_concat[self.intra_perf_col] = 1.0 / csv_concat[self.intra_perf_col]
                logging.debug("Inverted performance column: df stem=%s,col=%s",
                              csv_fname[0],
                              self.intra_perf_col)
            by_row_index = csv_concat.groupby(csv_concat.index)

            csv_averaged = by_row_index.mean()
            if csv_fname[1] != '':
                core.utils.dir_create_checked(os.path.join(self.avgd_output_root, csv_fname[1]),
                                              exist_ok=True)

            core.utils.pd_csv_write(csv_averaged, os.path.join(self.avgd_output_root, csv_fname[1], csv_fname[0]),

                                    index=False)

            # Also write out stddev in order to calculate confidence intervals later
            if self.avg_opts['gen_stddev']:
                csv_stddev = by_row_index.std().round(2)
                csv_stddev_fname = csv_fname.split('.')[0] + '.stddev'
                core.utils.pd_csv_write(csv_stddev, os.path.join(self.avgd_output_root, csv_stddev_fname),

                                        index=False)

    def __verify_exp(self):
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

        logging.info('Verifying results in %s...', self.exp_output_root)

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
                        logging.debug("Not verifying %s: contains rendering data",
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
                        assert(all(len(df1[c1]) == len(df1[c2])) for c2 in df1.columns),\
                            "FATAL: Not all columns from {0} have same length".format(path1)
                        assert(all(len(df1[c1]) == len(df2[c2])) for c2 in df1.columns),\
                            "FATAL: Not all columns from {0} and {1} have same length".format(path1,
                                                                                              path2)


def sim_dir_filter(exp_dirs: str, main_config: dict, videos_leaf: str):
    avgd_output_leaf = main_config['sierra']['avg_output_leaf']
    project_frames_leaf = main_config['sierra']['project_frames_leaf']
    argos_frames_leaf = main_config['sim']['argos_frames_leaf']
    return [e for e in exp_dirs if e not in [avgd_output_leaf,
                                             project_frames_leaf,
                                             argos_frames_leaf,
                                             videos_leaf]]
