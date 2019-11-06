# Copyright 2018 John Harwell, All rights reserved.
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


import os
import pandas as pd
import logging


class BivarCSVCollator:

    """Generates collated .csv files from the averaged .csv files present in a batch of experiments for
    bivar batch criteria. Each collated .csv file will one criteria as the column values, and one
    criteria as the row index, with each (x,y) pair containing a vector of temporal experiment
    values drawn from a .csv in the experiment's output's, per graph configuration.

    - .csv files with simulation data
    - .stddev files with the std deviation for said simulation data (if cmdline option for it
       was passed)
    """

    def __init__(self, main_config, cmdopts, targets, batch_criteria):
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.batch_criteria = batch_criteria

        self.batch_output_root = os.path.abspath(self.cmdopts['output_root'])
        self.collate_root = os.path.join(self.batch_output_root,
                                         self.main_config['sierra']['collate_csv_leaf'])
        os.makedirs(self.collate_root, exist_ok=True)
        self.targets = targets

    def __call__(self):
        logging.info("Stage4: Collating bivar inter-experiment .csv files from batch in {0} to {1}...".format(self.batch_output_root,
                                                                                                              self.collate_root))
        # For each category of graphs we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                self.__collate_target_files(graph)

    def __collate_target_files(self, target):

        xlabels = self.batch_criteria.gen_exp_dirnames(self.cmdopts, 'x')
        ylabels = self.batch_criteria.gen_exp_dirnames(self.cmdopts, 'y')

        data_df_new = pd.DataFrame(columns=ylabels, index=xlabels)
        stddev_df_new = pd.DataFrame()
        exp_dirs = self.batch_criteria.gen_exp_dirnames(self.cmdopts)
        csv_src_exists = [False for d in exp_dirs]
        stddev_src_exists = [False for d in exp_dirs]

        for i in range(0, len(exp_dirs)):
            csv_src_exists[i] = self.__collate_exp_csv_data(exp_dirs[i],
                                                            target,
                                                            data_df_new)

            stddev_src_exists[i] = self.__collate_exp_csv_stddev(exp_dirs[i],
                                                                 target,
                                                                 stddev_df_new)

        if all([v for v in csv_src_exists]):
            data_df_new.to_csv(os.path.join(self.collate_root,
                                            target['dest_stem'] + '.csv'),
                               sep=';',
                               index=False)
        elif any([v for v in csv_src_exists]):
            logging.warning("Not all experiments in {0} produced '{1}.csv'".format(self.batch_output_root,
                                                                                   target['src_stem']))

        if all([v for v in csv_src_exists]) and not stddev_df_new.empty:
            stddev_df_new.to_csv(os.path.join(self.collate_root,
                                              target['dest_stem'] + '.stddev'),
                                 sep=';',
                                 index=False)

    def __collate_exp_csv_data(self, exp_dir, target, collated_df):
        exp_output_root = os.path.join(self.batch_output_root, exp_dir)
        csv_ipath = os.path.join(exp_output_root,
                                 self.main_config['sierra']['avg_output_leaf'],
                                 target['src_stem'] + '.csv')
        if not os.path.exists(csv_ipath):
            return False

        data_df = pd.read_csv(csv_ipath, sep=';')

        assert target['col'] in data_df.columns.values,\
            "FATAL: {0} not in columns of {1}".format(target['col'],
                                                      target['src_stem'] + '.csv')
        xlabel, ylabel = exp_dir.split('+')
        collated_df.loc[xlabel, ylabel] = data_df[target['col']].to_numpy()
        return True

    def __collate_exp_csv_stddev(self, exp_dir, target, collated_df):
        exp_output_root = os.path.join(self.batch_output_root, exp_dir)
        stddev_ipath = os.path.join(exp_output_root,
                                    self.main_config['sierra']['avg_output_leaf'],
                                    target['src_stem'] + '.stddev')

        # Will not exist if the cmdline option to generate these files was not passed during
        # stage 3.
        if not os.path.exists(stddev_ipath):
            return False

        stddev_df = pd.read_csv(stddev_ipath, sep=';')

        assert target['col'] in stddev_df.columns.values,\
            "FATAL: {0} not in columns of {1}".format(target['col'],
                                                      target['src_stem'] + '.stddev')

        xlabel, ylabel = exp_dir.split('+')
        collated_df.iloc[xlabel, ylabel] = stddev_df[target['col']]
        return True
