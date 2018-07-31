"""
 Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

import os
import re
import statistics
from pipeline.csv_class import CSV
import pandas as pd


class ExpCSVAverager:
    """
    Averages a set of .csv output files from a set of simulation runs for a single experiment.

    Attributes:
      exp_config_leaf(str): Leaf (i.e. no preceding path to the template XML configuration file for
                                the experiment.
      exp_output_root(str): Directory for averaged .csv output (relative to current dir or absolute).
    """

    def __init__(self, exp_config_leaf, exp_output_root):
        # will get the main name and extension of the config file (without the full absolute path)
        self.template_config_fname, self.template_config_ext = os.path.splitext(
            os.path.basename(exp_config_leaf))

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_config_leaf = exp_config_leaf

        # to be formatted like: self.config_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.output_name_format = format_base + "_output"

    def average_csvs(self):
        """Averages the CSV files found in the output save path"""
        csvs = {}
        # create a regex that searches for output CSVs regardless of which number experiment they are
        pattern = self.output_name_format.format(
            re.escape(self.exp_config_leaf), "\d+")

        for entry in os.scandir(self.exp_output_root):
            # check to make sure the file name matches the regex
            if re.fullmatch(pattern, entry.name):
                # restriction: csv files must be in the "metrics" folder inside the output folder
                for inner_entry in os.scandir(os.path.join(entry.path, "metrics")):
                    # get every csv file
                    if inner_entry.name.endswith(".csv"):
                        # create a CSV object out of the file
                        csv = CSV(inner_entry.path, delimiter=";")
                        if inner_entry.name not in csvs:
                            csvs[inner_entry.name] = []
                        csvs[inner_entry.name].append(csv)

        # average the CSVs based on their name; all the CSV files with the same base name will be
        # averaged together
        averaged_csvs = {key: self._average_csvs(csvs[key]) for key in csvs}

        stats = {key: self._gen_statistics(csvs[key]) for key in csvs}
        csvs_path = os.path.join(self.exp_output_root, "averaged-output")
        os.makedirs(csvs_path, exist_ok=True)

        # save the averaged CSV files
        for name, value in averaged_csvs.items():
            value.write(os.path.join(csvs_path, name))

        # Save statistics with the same stem as the averaged .csv file, but with the .stats
        # extension.
        for key, value in stats.items():
            value.to_csv(os.path.join(csvs_path, key.split('.')
                                      [0] + ".stats"), sep=';', index=False)

    def _average_csvs(self, csvs):
        '''
        Takes a list of CSV objects and averages them.
        Returns None if the list is empty
        '''
        if not csvs:
            return None
        csv_sum = csvs[0]
        for index in range(1, len(csvs)):
            csv_sum += csvs[index]
        return csv_sum / len(csvs)

    def _gen_statistics(self, csvs):
        """Generate statistics across all columns in all .csv files perclock interval."""
        n_cols = csvs[0].width
        n_rows = csvs[0].height

        # Last column is always ';', which is read as empty, hence the -1
        df = pd.DataFrame(columns=csvs[0].csv[0][:-1])
        df['clock'] = [i[0] for i in csvs[0].csv[1:]]

        # First column is clock, which doesn't need to be averaged.
        # Last column is always ';', which is read as empty, hence the -1
        for col in range(1, n_cols - 1):
            # First row is column headers so skip it
            for row in range(1, n_rows):
                vals = []
                for i in range(0, len(csvs)):
                    vals.append(float(csvs[i].csv[row][col]))
                df.loc[row - 1, df.columns[col]] = round(statistics.stdev(vals), 4)
        return df
