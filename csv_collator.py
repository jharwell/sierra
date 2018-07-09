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
        print("- Collating inter-experiment .csv files to {0}...".format(self.collate_root))
        for csv_ifname, csv_col, csv_ofname in self.targets:
            df_new = pd.DataFrame()
            for item in os.listdir(self.batch_output_root):
                exp_output_root = os.path.join(self.batch_output_root, item)
                if os.path.isdir(exp_output_root):
                    csv_ipath = os.path.join(exp_output_root, "averaged-output", csv_ifname)
                    if not os.path.exists(csv_ipath):
                        continue
                    df = pd.read_csv(csv_ipath, sep=';')

                    assert csv_col in df.columns.values, "FATAL: {0} not in columns of {1}".format(
                        csv_col, csv_ifname)
                    df_new['clock'] = df['clock']
                    df_new[item] = df[csv_col]
            # Sort columns except clock. They all start with 'exp' so only sort on the numerals
            # after that part.
            new_cols = ['clock'] + sorted([c for c in df_new.columns if c not in ['clock']],
                                          key=lambda t: (int(t[3:])))
            df_new = df_new.reindex(new_cols, axis=1)
            df_new.to_csv(os.path.join(self.collate_root, csv_ofname), sep=';', index=False)
