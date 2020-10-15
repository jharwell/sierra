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
import multiprocessing as mp
import queue
import typing as tp

import pandas as pd

import core.utils


class UnivarGraphCollator:
    """
    For a single graph (target) in a univariate batched experiment, go through all experiment
    directories in a batched experiment and collate file averaged results into a single ``.csv``
    file.
    """

    def __init__(self, main_config: dict, cmdopts: dict) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, batch_criteria, target: dict, collate_root: str) -> None:
        logging.info("Stage4: Collating univariate files from batch in %s for graph '%s'...",
                     self.cmdopts['batch_output_root'],
                     target['src_stem'])

        data_df_new = pd.DataFrame(columns=batch_criteria.gen_exp_dirnames(self.cmdopts))
        stddev_df_new = pd.DataFrame(columns=batch_criteria.gen_exp_dirnames(self.cmdopts))

        exp_dirs = core.utils.exp_range_calc(
            self.cmdopts, self.cmdopts['batch_output_root'], batch_criteria)
        csv_src_exists = [False for d in exp_dirs]
        stddev_src_exists = [False for d in exp_dirs]

        for i, diri in enumerate(exp_dirs):
            # We get full paths back from the exp dirs calculation, and we need to work with path
            # leaves
            diri = os.path.split(diri)[1]
            csv_src_exists[i] = self.__collate_exp_csv_data(diri,
                                                            target,
                                                            data_df_new)

            stddev_src_exists[i] = self.__collate_exp_csv_stddev(diri,
                                                                 target,
                                                                 stddev_df_new)

        if all([v for v in csv_src_exists]):
            core.utils.pd_csv_write(data_df_new, os.path.join(collate_root,
                                                              target['dest_stem'] + '.csv'),
                                    index=False)
        elif any([v for v in csv_src_exists]):
            logging.warning("Not all experiments in %s produced '%s.csv'",
                            self.cmdopts['batch_output_root'],
                            target['src_stem'])

        if all([v for v in csv_src_exists]) and not stddev_df_new.empty:
            core.utils.pd_csv_write(stddev_df_new, os.path.join(collate_root,
                                                                target['dest_stem'] + '.stddev'),
                                    index=False)

    def __collate_exp_csv_data(self, exp_dir: str, target: dict, collated_df: pd.DataFrame) -> bool:
        exp_output_root = os.path.join(self.cmdopts['batch_output_root'], exp_dir)
        csv_ipath = os.path.join(exp_output_root,
                                 self.main_config['sierra']['avg_output_leaf'],
                                 target['src_stem'] + '.csv')

        if not core.utils.path_exists(csv_ipath):
            return False

        data_df = core.utils.pd_csv_read(csv_ipath)

        assert target['col'] in data_df.columns.values,\
            "FATAL: {0} not in columns of {1}".format(target['col'],
                                                      target['src_stem'] + '.csv')
        collated_df[exp_dir] = data_df[target['col']]
        return True

    def __collate_exp_csv_stddev(self, exp_dir: str, target: dict, collated_df: pd.DataFrame) -> bool:
        exp_output_root = os.path.join(self.cmdopts['batch_output_root'], exp_dir)
        stddev_ipath = os.path.join(exp_output_root,
                                    self.main_config['sierra']['avg_output_leaf'],
                                    target['src_stem'] + '.stddev')

        # Will not exist if the cmdline option to generate these files was not passed during
        # stage 3.
        if not core.utils.path_exists(stddev_ipath):
            return False

        stddev_df = core.utils.pd_csv_read(stddev_ipath)

        assert target['col'] in stddev_df.columns.values,\
            "FATAL: {0} not in columns of {1}".format(target['col'],
                                                      target['src_stem'] + '.stddev')

        collated_df[exp_dir] = stddev_df[target['col']]
        return True


class BivarGraphCollator:
    """
    For a single graph (target) for a bivariate batched experiment, go through all experiment
    directories in a batched experiment and collate file averaged results into a single ``.csv``
    file.

    """

    def __init__(self, main_config: dict, cmdopts: dict) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

    def __call__(self, batch_criteria, target: dict, collate_root: str) -> None:
        logging.info("Stage4: Collating bivariate files from batch in %s for graph '%s'...",
                     self.cmdopts['batch_output_root'],
                     target['src_stem'])

        exp_dirs = core.utils.exp_range_calc(
            self.cmdopts, self.cmdopts['batch_output_root'], batch_criteria)

        # Because sets are used, if a sub-range of experiments are selected for collation, the
        # selected range has to be an even multiple of the # of experiments in the second batch
        # criteria, or inter-experiment graph generation won't work (the final .csv is always an MxN
        # grid).
        xlabels_set = set()
        ylabels_set = set()
        for e in exp_dirs:
            pair = os.path.split(e)[1].split('+')
            xlabels_set.add(pair[0])
            ylabels_set.add(pair[1])

        xlabels = sorted(list(xlabels_set))
        ylabels = sorted(list(ylabels_set))

        data_df_new = pd.DataFrame(columns=ylabels, index=xlabels)
        stddev_df_new = pd.DataFrame()
        csv_src_exists = [False for d in exp_dirs]
        stddev_src_exists = [False for d in exp_dirs]

        for i, diri in enumerate(exp_dirs):
            # We get full paths back from the exp dirs calculation, and we need to work with path
            # leaves
            diri = os.path.split(diri)[1]
            csv_src_exists[i] = self.__collate_exp_csv_data(diri,
                                                            target,
                                                            data_df_new)

            stddev_src_exists[i] = self.__collate_exp_csv_stddev(diri,
                                                                 target,
                                                                 stddev_df_new)
        if all([v for v in csv_src_exists]):
            core.utils.pd_csv_write(data_df_new, os.path.join(collate_root,
                                                              target['dest_stem'] + '.csv'),

                                    index=False)
        elif any([v for v in csv_src_exists]):
            logging.warning("Not all experiments in %s produced '%s.csv'",
                            self.cmdopts['batch_output_root'],
                            target['src_stem'])

        if all([v for v in csv_src_exists]) and not stddev_df_new.empty:
            core.utils.pd_csv_write(stddev_df_new, os.path.join(collate_root,
                                                                target['dest_stem'] + '.stddev'),

                                    index=False)

    def __collate_exp_csv_data(self, exp_dir: str, target: dict, collated_df: pd.DataFrame) -> bool:
        exp_output_root = os.path.join(self.cmdopts['batch_output_root'], exp_dir)
        csv_ipath = os.path.join(exp_output_root,
                                 self.main_config['sierra']['avg_output_leaf'],
                                 target['src_stem'] + '.csv')
        if not core.utils.path_exists(csv_ipath):
            return False

        data_df = core.utils.pd_csv_read(csv_ipath)

        assert target['col'] in data_df.columns.values,\
            "FATAL: {0} not in columns of {1}".format(target['col'],
                                                      target['src_stem'] + '.csv')
        xlabel, ylabel = exp_dir.split('+')
        collated_df.loc[xlabel, ylabel] = data_df[target['col']].to_numpy()
        return True

    def __collate_exp_csv_stddev(self, exp_dir: str, target: dict, collated_df: pd.DataFrame) -> bool:
        exp_output_root = os.path.join(self.cmdopts['batch_output_root'], exp_dir)
        stddev_ipath = os.path.join(exp_output_root,
                                    self.main_config['sierra']['avg_output_leaf'],
                                    target['src_stem'] + '.stddev')

        # Will not exist if the cmdline option to generate these files was not passed during
        # stage 3.
        if not core.utils.path_exists(stddev_ipath):
            return False

        stddev_df = core.utils.pd_csv_read(stddev_ipath)

        assert target['col'] in stddev_df.columns.values,\
            "FATAL: {0} not in columns of {1}".format(target['col'],
                                                      target['src_stem'] + '.stddev')

        xlabel, ylabel = exp_dir.split('+')
        collated_df.iloc[xlabel, ylabel] = stddev_df[target['col']]
        return True


class MultithreadCollator():
    """
    Generates collated ``.csv`` files from the averaged ``.csv`` files present in a batch of
    experiments for univariate or bivariate batch criteria. Each collated ``.csv`` file will have
    one column per experiment, named after the experiment directory, containing a column drawn from
    a ``.csv`` in the experiment's averaged output, per graph configuration.

    """

    def __init__(self, main_config: dict, cmdopts: dict) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

        self.collate_root = os.path.join(self.cmdopts['batch_output_root'],
                                         self.main_config['sierra']['collate_csv_leaf'])
        core.utils.dir_create_checked(self.collate_root, exist_ok=True)

    def __call__(self, batch_criteria, targets: dict) -> None:
        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        # For each category of graphs we are generating
        for category in targets:
            # For each graph in each category
            for graph in category['graphs']:
                q.put(graph)

        for i in range(0, mp.cpu_count()):
            p = mp.Process(target=MultithreadCollator.__thread_worker,
                           args=(q,
                                 self.main_config,
                                 self.cmdopts,
                                 self.collate_root,
                                 batch_criteria))
            p.start()

        q.join()

    @staticmethod
    def __thread_worker(q: mp.Queue,
                        main_config: dict,
                        cmdopts: dict,
                        collate_root: str,
                        batch_criteria) -> None:

        collator = None  # type: tp.Any

        if batch_criteria.is_univar():
            collator = UnivarGraphCollator(main_config, cmdopts)
        else:
            collator = BivarGraphCollator(main_config, cmdopts)

        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                graph = q.get(True, 3)
                collator(batch_criteria, graph, collate_root)
                q.task_done()
            except queue.Empty:
                break


__api__ = ['UnivarGraphCollator', 'BivarGraphCollator']
