"""
 Copyright 2018 John Harwell, All rights reserved.

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
import pandas as pd


class CSVCollator:

    """
    Generates collated .csv files from the averaged .csv files present in a batch of experiments.

    Attributes:
    batch_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
    targets(tuple list): List of (.csv file name, column name, collated .csv name) tuples specifying
                         what columns from what .csvs should be combined to formed a new .csv that
                         can then be used to generated batched/collated graphs.

    """

    def __init__(self, batch_output_root, targets):
        self.batch_output_root = os.path.abspath(batch_output_root)
        self.collate_root = os.path.join(self.batch_output_root, "collated-csvs")
        os.makedirs(self.collate_root, exist_ok=True)
        self.targets = targets

    def __call__(self):
        print("- Stage4: Collating inter-experiment .csv files from batch in {0} to {1}...".format(self.batch_output_root,
                                                                                                   self.collate_root))
        # For each category of graphs we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                self._collate_target_files(graph)

    def _collate_target_files(self, target):
        """
        Collate the files for a specific graph within a graph set. This may include:

        - .csv files with simulation data
        - .stddev files with the std deviation for said simulation data
        """
        src_exists = True

        csv_df_new = pd.DataFrame()
        stddev_df_new = pd.DataFrame()
        for item in os.listdir(self.batch_output_root):
            exp_output_root = os.path.join(self.batch_output_root, item)

            # So we can re-run graph generation multiple times on the same data
            if "collated-csvs" == item or "averaged-output" == item:
                continue

            if os.path.isdir(exp_output_root):
                csv_ipath = os.path.join(exp_output_root, "averaged-output",
                                         target['src_stem'] + '.csv')
                stddev_ipath = os.path.join(exp_output_root, "averaged-output",
                                            target['src_stem'] + '.stddev')
                if not os.path.exists(csv_ipath):
                    src_exists = False
                    continue

                csv_df = pd.read_csv(csv_ipath, sep=';')

                assert target['col'] in csv_df.columns.values, "FATAL: {0} not in columns of {1}".format(
                    target['col'], target['src_stem'] + '.csv')
                csv_df_new['clock'] = csv_df['clock']
                csv_df_new[item] = csv_df[target['col']]

                # Will not exist if the cmdline option to generate these files is not passed during
                # stage 3.
                if os.path.exists(stddev_ipath):
                    stddev_df = pd.read_csv(stddev_ipath, sep=';')

                    assert target['col'] in stddev_df.columns.values, "FATAL: {0} not in columns of {1}".format(
                        target['col'], target['src_stem'] + '.stddev')
                    stddev_df_new['clock'] = stddev_df['clock']
                    stddev_df_new[item] = stddev_df[target['col']]

        # Sort columns except clock. They all start with 'exp' so only sort on the numerals
        # after that part.
        if src_exists:
            new_cols = sorted([c for c in csv_df_new.columns if c not in ['clock']],
                              key=lambda t: (int(t[3:])))
            csv_df_new = csv_df_new.reindex(new_cols, axis=1)

            csv_df_new.to_csv(os.path.join(self.collate_root,
                                           target['dest_stem'] + '.csv'), sep=';',
                              index=False)
        if src_exists and not stddev_df_new.empty:
            new_cols = sorted([c for c in stddev_df_new.columns if c not in ['clock']],
                              key=lambda t: (int(t[3:])))
            stddev_df_new = stddev_df_new.reindex(new_cols, axis=1)

            stddev_df_new.to_csv(os.path.join(self.collate_root,
                                              target['dest_stem'] + '.stddev'), sep=';', index=False)
