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


# Core packages
import os
import multiprocessing as mp
import queue
import typing as tp
import logging  # type: tp.Any

# 3rd party packages
import pandas as pd
import json

# Project packages
from sierra.core import utils, config, types, storage
import sierra.core.variables.batch_criteria as bc


class UnivarGraphCollationInfo():
    """
    Data class containing the collated ``.csv`` files for a particular graph.
    """

    def __init__(self,
                 df_ext: str,
                 ylabels: tp.List[str]) -> None:
        self.df_ext = df_ext
        self.df = pd.DataFrame(columns=ylabels)
        self.all_srcs_exist = True
        self.some_srcs_exist = False


class BivarGraphCollationInfo():
    """
    Data class containing the collated ``.csv`` files for a particular graph.
    """

    def __init__(self,
                 df_ext: str,
                 xlabels: tp.List[str],
                 ylabels: tp.List[str]) -> None:
        self.df_ext = df_ext
        self.df = pd.DataFrame(columns=ylabels, index=xlabels)
        self.all_srcs_exist = True
        self.some_srcs_exist = False


class UnivarGraphCollator:
    """For a single graph gather needed data from experiments in a batch.

    Results are put into a single :term:`Collated .csv` file which will have one
    column per experiment, named after the experiment directory, containing a
    column drawn from an :term:`Averaged .csv` file for the experiment.

    """

    def __init__(self, main_config: dict, cmdopts: types.Cmdopts) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria, target: dict, stat_collate_root: str) -> None:
        self.logger.info("Stage4: Collating univariate files from batch in %s for graph '%s'...",
                         self.cmdopts['batch_output_root'],
                         target['src_stem'])
        self.logger.trace(json.dumps(target, indent=4))

        exp_dirs = utils.exp_range_calc(self.cmdopts,
                                        self.cmdopts['batch_output_root'],
                                        criteria)

        # Always do the mean, even if stats are disabled
        exts = [config.kStatsExtensions['mean']]

        if self.cmdopts['dist_stats'] in ['conf95', 'all']:
            exts.extend([config.kStatsExtensions['stddev']])
        if self.cmdopts['dist_stats'] in ['bw', 'all']:
            exts.extend([config.kStatsExtensions['min'],
                         config.kStatsExtensions['max'],
                         config.kStatsExtensions['whislo'],
                         config.kStatsExtensions['whishi'],
                         config.kStatsExtensions['cilo'],
                         config.kStatsExtensions['cihi'],
                         config.kStatsExtensions['median']])

        stats = [UnivarGraphCollationInfo(df_ext=ext,
                                          ylabels=[os.path.split(e)[1] for e in exp_dirs]) for ext in exts]

        for i, diri in enumerate(exp_dirs):
            # We get full paths back from the exp dirs calculation, and we need to work with path
            # leaves
            diri = os.path.split(diri)[1]
            self._collate_exp(target, diri, stats)

        for stat in stats:
            if stat.all_srcs_exist:
                storage.DataFrameWriter('csv')(stat.df, os.path.join(stat_collate_root,
                                                                     target['dest_stem'] + stat.df_ext),
                                               index=False)

            elif not stat.all_srcs_exist and stat.some_srcs_exist:
                self.logger.warning("Not all experiments in '%s' produced '%s%s'",
                                    self.cmdopts['batch_output_root'],
                                    target['src_stem'],
                                    stat.df_ext)

    def _collate_exp(self, target: dict, exp_dir: str, stats: tp.List[UnivarGraphCollationInfo]) -> None:
        exp_stat_root = os.path.join(self.cmdopts['batch_stat_root'], exp_dir)

        for stat in stats:
            csv_ipath = os.path.join(
                exp_stat_root, target['src_stem'] + stat.df_ext)
            if not utils.path_exists(csv_ipath):
                stat.all_srcs_exist = False
                continue

            stat.some_srcs_exist = True

            data_df = storage.DataFrameReader('csv')(csv_ipath)

            assert target['col'] in data_df.columns.values,\
                "{0} not in columns of {1}".format(target['col'],
                                                   target['src_stem'] + stat.df_ext)

            if target.get('summary', False):
                stat.df.loc[0, exp_dir] = data_df.loc[data_df.index[-1],
                                                      target['col']]
            else:
                stat.df[exp_dir] = data_df[target['col']]


class BivarGraphCollator:
    """For a single graph gather needed data from experiments in a batch.

    Results are put into a single :term:`Collated .csv` file which will have one
    column per experiment, named after the experiment directory, containing a
    column drawn from an :term:`Averaged .csv` file for the experiment.

    """

    def __init__(self, main_config: dict, cmdopts: types.Cmdopts) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria, target: dict, stat_collate_root: str) -> None:
        self.logger.info("Stage4: Collating bivariate files from batch in %s for graph '%s'...",
                         self.cmdopts['batch_output_root'],
                         target['src_stem'])
        self.logger.trace(json.dumps(target, indent=4))

        exp_dirs = utils.exp_range_calc(self.cmdopts,
                                        self.cmdopts['batch_output_root'],
                                        criteria)

        xlabels, ylabels = utils.bivar_exp_labels_calc(exp_dirs)

        if self.cmdopts['dist_stats'] in ['conf95', 'all']:
            exts = [config.kStatsExtensions['mean'],
                    config.kStatsExtensions['stddev']]
        elif self.cmdopts['dist_stats'] in ['bw', 'all']:
            exts = [config.kStatsExtensions['min'],
                    config.kStatsExtensions['max'],
                    config.kStatsExtensions['mean'],
                    config.kStatsExtensions['whislo'],
                    config.kStatsExtensions['whishi'],
                    config.kStatsExtensions['cilo'],
                    config.kStatsExtensions['cihi'],
                    config.kStatsExtensions['median']]

        stats = [BivarGraphCollationInfo(df_ext=ext,
                                         xlabels=xlabels,
                                         ylabels=ylabels) for ext in exts]

        for i, diri in enumerate(exp_dirs):
            # We get full paths back from the exp dirs calculation, and we need to work with path
            # leaves
            diri = os.path.split(diri)[1]
            self._collate_exp(target, diri, stats)

        for stat in stats:
            if stat.all_srcs_exist:
                storage.DataFrameWriter('csv')(stat.df,
                                               os.path.join(stat_collate_root,
                                                            target['dest_stem'] + stat.df_ext),
                                               index=False)

            elif stat.some_srcs_exist:
                self.logger.warning("Not all experiments in '%s' produced '%s%s'",
                                    self.cmdopts['batch_output_root'],
                                    target['src_stem'],
                                    stat.df_ext)

    def _collate_exp(self,
                     target: dict,
                     exp_dir: str,
                     stats: tp.List[BivarGraphCollationInfo]) -> None:
        exp_stat_root = os.path.join(self.cmdopts['batch_stat_root'], exp_dir)

        for stat in stats:
            csv_ipath = os.path.join(
                exp_stat_root, target['src_stem'] + stat.df_ext)
            if not utils.path_exists(csv_ipath):
                stat.all_srcs_exist = False
                continue

            stat.some_srcs_exist = True

            data_df = storage.DataFrameReader('csv')(csv_ipath)

            assert target['col'] in data_df.columns.values,\
                "{0} not in columns of {1}, which has {2}".format(target['col'],
                                                                  csv_ipath,
                                                                  data_df.columns)
            xlabel, ylabel = exp_dir.split('+')
            stat.df.loc[xlabel, ylabel] = data_df[target['col']].to_numpy()


class GraphParallelCollator():
    """
    Generates :term:`Collated .csv` files from the :term:`Summary .csv` files.

    For all experiments in the batch.

    """

    def __init__(self,
                 main_config: tp.Dict[str, types.Cmdopts],
                 cmdopts: types.Cmdopts) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts

        self.batch_stat_collate_root = self.cmdopts['batch_stat_collate_root']
        utils.dir_create_checked(self.batch_stat_collate_root, exist_ok=True)

    def __call__(self,
                 criteria: bc.IConcreteBatchCriteria,
                 targets: tp.List[types.YAMLDict]) -> None:
        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        # For each category of graphs we are generating
        for category in targets:
            # For each graph in each category
            for graph in category['graphs']:
                q.put(graph)

        if self.cmdopts['serial_processing']:
            parallelism = 1
        else:
            parallelism = mp.cpu_count()

        for i in range(0, parallelism):
            p = mp.Process(target=GraphParallelCollator._thread_worker,
                           args=(q,
                                 self.main_config,
                                 self.cmdopts,
                                 self.batch_stat_collate_root,
                                 criteria))
            p.start()

        q.join()

    @staticmethod
    def _thread_worker(q: mp.Queue,
                       main_config: dict,
                       cmdopts: types.Cmdopts,
                       stat_collate_root: str,
                       criteria) -> None:

        collator = None  # type: ignore

        if criteria.is_univar():
            collator = UnivarGraphCollator(main_config, cmdopts)
        else:
            collator = BivarGraphCollator(main_config, cmdopts)

        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                graph = q.get(True, 3)
                collator(criteria, graph, stat_collate_root)
                q.task_done()
            except queue.Empty:
                break


__api__ = [
    'UnivarGraphCollator',
    'BivarGraphCollator',
    'UnivarGraphCollationInfo',
    'BivarGraphCollationInfo'
]
