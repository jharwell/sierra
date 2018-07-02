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
import random
import argparse
import subprocess
import re
from csv_class import CSV
class CSVAverager:

    """
    Averages a set of .csv output files from a set of simulation runs.

    Attributes:
      config_path(str): Path(relative to current dir or absolute) to the
                        template XML configuration file.
      output_save_path(str): Directory for averaged .csv output. Can be relative or absolute.
    """

    def __init__(self, config_path, output_save_path):

        assert os.path.isfile(
            config_path), "The path '{}' (which should point to the main config file) did not point to a file".format(config_path)
        self.config_path = os.path.abspath(config_path)

        # will get the main name and extension of the config file (without the full absolute path)
        self.main_config_name, self.main_config_extension = os.path.splitext(
            os.path.basename(self.config_path))

        # where the output data should be stored
        if output_save_path is None:
            output_save_path = os.path.join(os.path.dirname(
                self.config_save_path), "Generated_Output")
        self.output_save_path = os.path.abspath(output_save_path)

        # to be formatted like: self.config_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.output_name_format = format_base + "_output"

    def average_csvs(self):
        '''Averages the CSV files found in the output save path'''
        csvs = {}
        # create a regex that searches for output CSVs regardless of which number experiment they are
        pattern = self.output_name_format.format(
            re.escape(self.main_config_name), "\d+")
        for entry in os.scandir(self.output_save_path):
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
        # average the CSVs based on their name; all the CSV files with the same base name will be averaged together
        averaged_csvs = {key: self._average_csvs(csvs[key]) for key in csvs}
        csvs_path = os.path.join(self.output_save_path, "Averaged_Output")
        os.makedirs(csvs_path, exist_ok=True)
        # save the averaged CSV files
        for name, value in averaged_csvs.items():
            value.write(os.path.join(csvs_path, name))
        print(
            "The CSVs have been averaged. (Output can be found in '{}')".format(csvs_path))

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
