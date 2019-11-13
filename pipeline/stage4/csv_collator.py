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
import logging
import typing as tp
import pandas as pd
from variables import batch_criteria as bc


class UnivarCSVCollator:
    """
    Generates collated ``.csv`` files from the averaged .csv files present in a batch of experiments
    for :class:`variables.batch_criteria.UnivarBatchCriteria` into the directory specified in the
    main configuration YAML file. Which ``.csv`` files will be collated is determined by
    inter-experiment graph configuration, as parsed from the corresponding YAML file.

    Each collated ``.csv`` file will be 1D, with each experiment a column within the collated
    ``.csv`` file, which will only have one row.

    Optionally, also generate ``.stddev`` files for each collated ``.csv`` file in the same fashion,
    as configured on the cmdline.

    Attributes:
        main_config: Dictionary of parsed main YAML configuration.
        cmdopts: Dictionary of parsed cmdline options.
        batch_output_root: Absolute path to the output directory for all experiments in the batch
                           (each experiment gets their own directory in here).
        collate_root: Absolute path to the folder within :attribute:`batch_output_root` to collate
                      ``.csv`` files into; name controlled via main YAML configuration.
    """

    def __init__(self, main_config: dict, cmdopts: tp.Dict[str, str]):
        self.main_config = main_config
        self.cmdopts = cmdopts

        self.batch_output_root = os.path.abspath(self.cmdopts['output_root'])
        self.collate_root = os.path.join(self.batch_output_root,
                                         self.main_config['sierra']['collate_csv_leaf'])
        os.makedirs(self.collate_root, exist_ok=True)

    def __call__(self, batch_criteria: bc.BatchCriteria, targets: dict):
        """
        Collate all ``.csv`` (and possibly all `.stddev` files) for all experiments in the batch
        into :attribute:`collate_root`.
        """
        logging.info("Stage4: Collating univar inter-experiment .csv files from batch in % s to %s...",
                     self.batch_output_root,
                     self.collate_root)
        # For each category of graphs we are generating
        for category in targets:
            # For each graph in each category
            for graph in category['graphs']:
                self.__collate_target_files(batch_criteria, graph)

    def __collate_target_files(self, batch_criteria: bc.BatchCriteria, target: dict):
        """
        For a specific graph to be generated, collate columns from a specific ``.csv`` in all
        experiments into a single inter-experiment ``.csv`` file, and save it into
        :attribute:`collate_root`. If all experiments did not produce the necessary source ``.csv``
        file, as specified in graph configuration, the partially collated dataframe is not written
        out.

        Optionally, collate the ``.stddev`` files from all experiments in the same fashion, if they
        exist.
        """

        data_df_new = pd.DataFrame(columns=batch_criteria.gen_exp_dirnames(self.cmdopts))
        stddev_df_new = pd.DataFrame(columns=batch_criteria.gen_exp_dirnames(self.cmdopts))

        exp_dirs = batch_criteria.gen_exp_dirnames(self.cmdopts)
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
                                            target['dest_stem'] + '.csv'), sep=';',
                               index=False)
        elif any([v for v in csv_src_exists]):
            logging.warning("Not all experiments in %s produced '%s.csv'--skipping collation",
                            self.batch_output_root,
                            target['src_stem'])

        if all([v for v in csv_src_exists]) and not stddev_df_new.empty:
            stddev_df_new.to_csv(os.path.join(self.collate_root,
                                              target['dest_stem'] + '.stddev'), sep=';',
                                 index=False)

    def __collate_exp_csv_data(self, exp_dir, target, collated_df):
        """
        Collate data from a specific column in a specific ``.csv`` in each experiment in the
        batch into the column for the experiment in  the dataframe for the collated ``.csv`` file
        in :attribute:`collate_root`.

        Returns:
            True if the source ``.csv`` specified by the target graph exists and was added to the
            collated ``.csv`` dataframe, False otherwise.
        """
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
        collated_df[exp_dir] = data_df[target['col']]
        return True

    def __collate_exp_csv_stddev(self, exp_dir, target, collated_df):
        """
        Collate data from a specific column in a specific ``.stddev`` in each experiment in the
        batch into the column for the experiment in  the dataframe for the collated ``.stddev`` file
        in :attribute:`collate_root`.

        Returns:
            True if the source ``.stddev`` specified by the target graph exists and was added to the
            collated ``.stddev`` dataframe, False otherwise.
        """

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

        collated_df[exp_dir] = stddev_df[target['col']]
        return True


class BivarCSVCollator:
    """
    Generates collated ``.csv`` files from the averaged .csv files present in a batch of experiments
    for :class:`variables.batch_criteria.BivarBatchCriteria` into the directory specified in the
    main configuration YAML file. Which ``.csv`` files will be collated is determined by
    inter-experiment graph configuration, as parsed from the corresponding YAML file.

    Each collated ``.csv`` file will be 2D, with the first constituent batch criteria as the X
    values (rows), and the second one as the Y values (columns). Each (X,Y) cell within the ``.csv``
    will contain a vector of temporal experiment values drawn from a ``.csv`` in the corresponding
    experiment's output.

    Optionally, also generate ``.stddev`` files for each collated ``.csv`` file in the same
    faishion, as configured on the cmdline.

    Attributes:
        main_config: Dictionary of parsed main YAML configuration.
        cmdopts: Dictionary of parsed cmdline options.
        batch_output_root: Absolute path to the output directory for all experiments in the batch
                           (each experiment gets their own directory in here).
        collate_root: Absolute path to the folder within :attribute:`batch_output_root` to collate
                      ``.csv`` files into; name controlled via main YAML configuration.
    """

    def __init__(self,
                 main_config: dict,
                 cmdopts: tp.Dict[str, str]):
        self.main_config = main_config
        self.cmdopts = cmdopts

        self.batch_output_root = os.path.abspath(self.cmdopts['output_root'])
        self.collate_root = os.path.join(self.batch_output_root,
                                         self.main_config['sierra']['collate_csv_leaf'])
        os.makedirs(self.collate_root, exist_ok=True)

    def __call__(self, batch_criteria: bc.BatchCriteria, targets: dict):
        """
        Collate all ``.csv`` (and possibly all `.stddev` files) for all experiments in the batch
        into :attribute:`collate_root`.
        """
        logging.info("Stage4: Collating bivar inter-experiment .csv files from batch in %s to %s...",
                     self.batch_output_root,
                     self.collate_root)
        # For each category of graphs we are generating
        for category in targets:
            # For each graph in each category
            for graph in category['graphs']:
                self.__collate_target_files(batch_criteria, graph)

    def __collate_target_files(self, batch_criteria: bc.BatchCriteria, target: dict):
        """
        For a specific graph to be generated, collate columns from a specific ``.csv`` in all
        experiments into a single inter-experiment ``.csv`` file, and save it into
        :attribute:`collate_root`. If all experiments did not produce the necessary source ``.csv``
        file, as specified in graph configuration, the partially collated dataframe is not written
        out.

        Optionally, collate the ``.stddev`` files from all experiments in the same fashion, if they
        exist.
        """

        xlabels = batch_criteria.gen_exp_dirnames(self.cmdopts, 'x')
        ylabels = batch_criteria.gen_exp_dirnames(self.cmdopts, 'y')

        data_df_new = pd.DataFrame(columns=ylabels, index=xlabels)
        stddev_df_new = pd.DataFrame()
        exp_dirs = batch_criteria.gen_exp_dirnames(self.cmdopts)
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
            logging.warning("Not all experiments in %s produced '%s.csv'--skipping collation",
                            self.batch_output_root,
                            target['src_stem'])

        if all([v for v in csv_src_exists]) and not stddev_df_new.empty:
            stddev_df_new.to_csv(os.path.join(self.collate_root,
                                              target['dest_stem'] + '.stddev'),
                                 sep=';',
                                 index=False)

    def __collate_exp_csv_data(self,
                               exp_dir: str,
                               target: dict,
                               collated_df: pd.DataFrame) -> bool:
        """
        Collate data from a specific column in a specific ``.csv`` in each experiment in the batch
        into a (X,Y) cell into the dataframe for the collated ``.csv`` file in
        :attribute:`collate_root`.

        Returns:
            True if the source ``.csv`` specified by the target graph exists and was added to the
            collated ``.csv`` dataframe, False otherwise.
        """
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

    def __collate_exp_csv_stddev(self,
                                 exp_dir: str,
                                 target: dict,
                                 collated_df: pd.DataFrame) -> bool:
        """
        Collate data from a specific column in a specific ``.stddev`` in each experiment in the
        batch into a (X,Y) cell into the dataframe for the collated ``.stddev`` file in
        :attribute:`collate_root`.

        Returns:
            True if the source ``.stddev`` specified by the target graph exists and was added to the
            collated ``.stddev`` dataframe, False otherwise.
        """
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
