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
Class for averaging ``.csv`` files as part of stage 3 of the experimental pipeline.
"""

import os
import re
import logging
import pandas as pd


class BatchedExpCSVAverager:

    """
    Averages the .csv output files for each experiment in the specified batch directory.

    Attributes:
      ro_params(dict): Dictionary of read-only parameters for batch averaging
      batch_output_root(str): Directory for averaged .csv output (relative to current dir or absolu

    """

    def __init__(self, ro_params, batch_output_root):

        self.ro_params = ro_params
        self.batch_output_root = batch_output_root

    def run(self):
        """Average .csv output files for all experiments in the batch."""
        # Ignore the folder for .csv files collated across experiments within a batch
        experiments = [item for item in os.listdir(self.batch_output_root) if item not in [
            self.ro_params['config']['sierra']['collate_csv_leaf']]]
        for exp in experiments:
            path = os.path.join(self.batch_output_root, exp)

            if os.path.isdir(path):
                ExpCSVAverager(self.ro_params, path).run()


class ExpCSVAverager:
    """
    Averages a set of .csv output files from a set of simulation runs for a single experiment.

    Attributes:
        ro_params(dict): Dictionary of read-only configuration for CSV averaging:
        template_input_leaf(str): Leaf (i.e. no preceding path to the template XML configuration file
                                  for the experiment.
        no_verify(bool): Should result verification be skipped?
        gen_stddev(bool): Should standard deviation be generated (and therefore errorbars
                          plotted)?
        config(dict): Parsed main YAML configuration
         exp_output_root(str): Directory for averaged .csv output (relative to current dir or
                               absolute).
    """

    def __init__(self, ro_params, exp_output_root):
        # will get the main name and extension of the config file (without the full absolute path)
        self.template_input_leaf = ro_params['template_input_leaf']
        self.template_input_fname, self.template_input_ext = os.path.splitext(
            os.path.basename(self.template_input_leaf))

        self.exp_output_root = os.path.abspath(exp_output_root)

        self.avgd_output_leaf = ro_params['config']['sierra']['avg_output_leaf']
        self.avgd_output_root = os.path.join(self.exp_output_root,
                                             self.avgd_output_leaf)
        self.metrics_leaf = ro_params['config']['sim']['metrics_leaf']

        self.exp_no_verify = ro_params['exp_no_verify']
        self.gen_stddev = ro_params['gen_stddev']
        os.makedirs(self.avgd_output_root, exist_ok=True)

        # to be formatted like: self.input_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.output_name_format = format_base + "_output"

    def run(self):
        if not self.exp_no_verify:
            self._verify_exp_csvs()
        self._average_csvs()

    def _average_csvs(self):
        """Averages the CSV files found in the output save path"""

        logging.info('Averaging results in %s...', self.exp_output_root)

        # Maps unique .csv stem to the averaged dataframe
        csvs = {}

        pattern = self.output_name_format.format(
            re.escape(self.template_input_leaf), r'\d+')

        # check to make sure all directories are simulation runs, skipping the directory within each
        # experiment that the averaged data is placed in
        experiments = [e for e in os.listdir(self.exp_output_root) if e not in [
            self.avgd_output_leaf]]

        assert(all(re.match(pattern, exp) for exp in experiments)),\
            "FATAL: Not all directories in {0} are simulation runs".format(self.exp_output_root)

        for exp in experiments:
            csv_root = os.path.join(self.exp_output_root, exp, self.metrics_leaf)
            # Nothing but .csv files should be in the metrics folder
            for csv_fname in os.listdir(csv_root):
                df = pd.read_csv(os.path.join(csv_root, csv_fname), index_col=False, sep=';')
                if csv_fname not in csvs:
                    csvs[csv_fname] = []

                csvs[csv_fname].append(df)

            # All CSV files with the same base name will be averaged together
            for csv_fname in csvs:
                csv_concat = pd.concat(csvs[csv_fname])
                by_row_index = csv_concat.groupby(csv_concat.index)
                csv_averaged = by_row_index.mean()
                csv_averaged.to_csv(os.path.join(self.avgd_output_root, csv_fname),
                                    sep=';',
                                    index=False)
                # Also write out stddev in order to calculate confidence intervals later
                if self.gen_stddev:
                    csv_stddev = by_row_index.std().round(2)
                    csv_stddev_fname = csv_fname.split('.')[0] + '.stddev'
                    csv_stddev.to_csv(os.path.join(self.avgd_output_root, csv_stddev_fname),
                                      sep=';',
                                      index=False)

    def _verify_exp_csvs(self):
        """
        Verify that all experiments in the batch output root all have the same .csv files, and that
        those .csv files all have the same # of rows and columns
        """
        experiments = [exp for exp in os.listdir(self.exp_output_root) if exp not in [
            self.avgd_output_leaf]]

        logging.info('Verifying results in %s...', self.exp_output_root)

        for exp1 in experiments:
            csv_root1 = os.path.join(self.exp_output_root,
                                     exp1,
                                     self.metrics_leaf)

            for exp2 in experiments:
                csv_root2 = os.path.join(self.exp_output_root,
                                         exp2,
                                         self.metrics_leaf)

                if not os.path.isdir(csv_root2):
                    continue

                for csv in os.listdir(csv_root2):
                    path1 = os.path.join(csv_root1, csv)
                    path2 = os.path.join(csv_root2, csv)
                    assert (os.path.exists(path1) and os.path.exists(path2)),\
                        "FATAL: Either {0} or {1} does not exist".format(path1, path2)

                    # Verify both dataframes have same # columns, and that column sets are identical
                    df1 = pd.read_csv(path1, sep=';')
                    df2 = pd.read_csv(path2, sep=';')
                    assert (len(df1.columns) == len(df2.columns)), \
                        "FATAL: Dataframes from {0} and {1} do not have same # columns".format(
                            path1, path2)
                    assert(sorted(df1.columns) == sorted(df2.columns)),\
                        "FATAL: Columns from {0} and {1} not identical".format(path1, path2)
                    assert(len(df1.index) == len(df2.index)),\
                        "FATAL: Length of indexes in {0} and {1} not the same: {2} vs. {3}".format(path1,
                                                                                                   path2,
                                                                                                   len(df1.index),
                                                                                                   len(df2.index))
                    # Verify that there are no NaNs in the dataframe. NaNs will occur when .csv
                    # files do not have the same # rows in each column, which Pandas (un)helpfully
                    # fills in with NaNs. So we count them, and error out if there are ANY.
                    assert not df1.isnull().any().any(),\
                        "FATAL: Empty cells or NaNs found in {0}".format(path1)
                    assert not df2.isnull().any().any(),\
                        "FATAL: Empty cells or NaNs found in {0}".format(path2)
