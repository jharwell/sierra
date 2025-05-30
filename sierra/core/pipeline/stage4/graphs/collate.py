# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Collation functionality for stage3 outputs according to configuration."""

# Core packages
import multiprocessing as mp
import queue
import typing as tp
import logging
import pathlib
import json

# 3rd party packages
import pandas as pd
import psutil

# Project packages
from sierra.core import utils, config, types, storage, batchroot
import sierra.core.variables.batch_criteria as bc


class UnivarGraphCollationInfo:
    """Data class of the :term:`Collated Output Data` files for a particular graph."""

    def __init__(
        self, df_ext: str, exp_names: tp.List[str], summary: bool, summary_col: str
    ) -> None:
        self.df_ext = df_ext

        # When collating for summary line graphs, the dataframe is indexed by
        # the name of the experiment, and the datapoint per experiment is in a
        # column.
        #
        # When collating for stacked line graphs, the columns are the names of
        # the experiments, and the columns are the time series data.
        if summary:
            self.df = pd.DataFrame(index=exp_names, columns=[summary_col])
            self.df.index.name = "Experiment ID"
        else:
            self.df = pd.DataFrame(columns=exp_names)

        self.summary = summary
        self.summary_col = summary_col
        self.all_srcs_exist = True
        self.some_srcs_exist = False


class BivarGraphCollationInfo:
    """Data class of the :term:`Collated Output Data` files for a particular graph."""

    def __init__(
        self, df_ext: str, xlabels: tp.List[str], ylabels: tp.List[str]
    ) -> None:
        self.df_ext = df_ext
        self.ylabels = ylabels
        self.xlabels = xlabels
        self.df_seq = {}  # type: tp.Dict[int, pd.DataFrame]
        self.df_all = pd.DataFrame(columns=ylabels, index=xlabels)
        self.all_srcs_exist = True
        self.some_srcs_exist = False


class UnivarGraphCollator:
    """For a single graph gather needed data from experiments in a batch.

    Results are put into a single :term:`Collated Output Data` file.
    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
    ) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.pathset = pathset
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria, target: types.YAMLDict) -> None:
        self.logger.info(
            "Files from univariate experiment  in <batch_root>/%s for graph '%s'",
            self.pathset.output_root.relative_to(self.pathset.root),
            target["src_stem"],
        )
        self.logger.trace(json.dumps(target, indent=4))  # type: ignore

        exp_dirs = utils.exp_range_calc(
            self.cmdopts["exp_range"], self.pathset.output_root, criteria
        )

        # Always do the mean, even if stats are disabled
        stat_config = config.kStats["mean"].exts

        if self.cmdopts["dist_stats"] in ["conf95", "all"]:
            stat_config.update(config.kStats["conf95"].exts)

        if self.cmdopts["dist_stats"] in ["bw", "all"]:
            stat_config.update(config.kStats["bw"].exts)

        is_summary = target["type"] == "summary_line"
        stats = [
            UnivarGraphCollationInfo(
                df_ext=suffix,
                exp_names=[e.name for e in exp_dirs],
                summary_col="{0}+{1}".format(
                    self.cmdopts["controller"], self.cmdopts["scenario"]
                ),
                summary=is_summary,
            )
            for suffix in stat_config.values()
        ]

        for diri in exp_dirs:
            self._collate_exp(target, diri.name, stats)

        for stat in stats:
            if stat.all_srcs_exist:
                storage.df_write(
                    stat.df,
                    self.pathset.stat_collate_root
                    / (target["dest_stem"] + stat.df_ext),
                    "storage.csv",
                    index=stat.summary,
                )

            elif not stat.all_srcs_exist and stat.some_srcs_exist:
                self.logger.warning(
                    "Not all experiments in '%s' produced '%s%s'",
                    self.pathset.output_root,
                    target["src_stem"],
                    stat.df_ext,
                )
            else:
                self.logger.warning(
                    "No experiments in <batchroot>/%s produced %s%s",
                    self.pathset.output_root.relative_to(self.pathset.root),
                    target["src_stem"],
                    stat.df_ext,
                )

    def _collate_exp(
        self, target: dict, exp_dir: str, stats: tp.List[UnivarGraphCollationInfo]
    ) -> None:
        exp_stat_root = self.pathset.stat_root / exp_dir

        for stat in stats:
            csv_ipath = pathlib.Path(exp_stat_root, target["src_stem"] + stat.df_ext)

            if not utils.path_exists(csv_ipath):
                stat.all_srcs_exist = False
                continue

            stat.some_srcs_exist = True

            data_df = storage.df_read(csv_ipath, "storage.csv")

            assert (
                target["col"] in data_df.columns.values
            ), "{0} not in columns of {1}".format(
                target["col"], target["src_stem"] + stat.df_ext
            )

            if target["type"] == "summary_line":
                idx = target.get("index", -1)
                datapoint = data_df.loc[data_df.index[idx], target["col"]]
                stat.df.loc[exp_dir, stat.summary_col] = datapoint
            else:
                stat.df[exp_dir] = data_df[target["col"]]


class BivarGraphCollator:
    """For a single graph gather needed data from experiments in a batch.

    Results are put into a single :term:`Collated Run Output Data` file.

    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
    ) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.pathset = pathset
        self.logger = logging.getLogger(__name__)

    def __call__(self, criteria: bc.IConcreteBatchCriteria, target: dict) -> None:
        self.logger.info(
            "Bivariate files from batch in %s for graph '%s'...",
            self.pathset.output_root,
            target["src_stem"],
        )
        self.logger.trace(json.dumps(target, indent=4))  # type: ignore

        exp_dirs = utils.exp_range_calc(
            self.cmdopts["exp_range"], self.pathset.output_root, criteria
        )

        xlabels, ylabels = utils.bivar_exp_labels_calc(exp_dirs)

        # Always do the mean, even if stats are disabled
        stat_config = config.kStats["mean"].exts

        if self.cmdopts["dist_stats"] in ["conf95", "all"]:
            stat_config.update(config.kStats["conf95"].exts)

        if self.cmdopts["dist_stats"] in ["bw", "all"]:
            stat_config.update(config.kStats["bw"].exts)

        stats = [
            BivarGraphCollationInfo(df_ext=suffix, xlabels=xlabels, ylabels=ylabels)
            for suffix in stat_config.values()
        ]

        for diri in exp_dirs:
            self._collate_exp(target, diri.name, stats)

        for stat in stats:
            if stat.all_srcs_exist:
                for row, df in stat.df_seq.items():
                    name = "{0}_{1}{2}".format(target["dest_stem"], row, stat.df_ext)
                    storage.df_write(
                        df,
                        self.pathset.stat_collate_root / name,
                        "storage.csv",
                        index=False,
                    )

                # TODO: Don't write this for now, until I find a better way of
                # doing 3D data in CSV files.
                # writer(stat.df_all,
                #        stat_collate_root / (target['dest_stem'] + stat.df_ext),
                #        index=False)

            elif stat.some_srcs_exist:
                self.logger.warning(
                    "Not all experiments in '%s' produced '%s%s'",
                    self.pathset.output_root,
                    target["src_stem"],
                    stat.df_ext,
                )

    def _collate_exp(
        self, target: dict, exp_dir: str, stats: tp.List[BivarGraphCollationInfo]
    ) -> None:
        exp_stat_root = self.pathset.stat_root / exp_dir
        for stat in stats:
            csv_ipath = pathlib.Path(exp_stat_root, target["src_stem"] + stat.df_ext)

            if not utils.path_exists(csv_ipath):
                stat.all_srcs_exist = False
                continue

            stat.some_srcs_exist = True

            data_df = storage.df_read(csv_ipath, "storage.csv")

            assert (
                target["col"] in data_df.columns.values
            ), "{0} not in columns of {1}, which has {2}".format(
                target["col"], csv_ipath, data_df.columns
            )
            xlabel, ylabel = exp_dir.split("+")

            # TODO: Don't capture this for now, until I figure out a better way
            # to do 3D data.
            # stat.df_all.loc[xlabel][ylabel] = data_df[target['col']].to_numpy()

            # We want a 2D dataframe after collation, with one iloc of SOMETHING
            # per experiment. If we just join the columns from each experiment
            # together into a dataframe like we did for univar criteria, we will
            # get a 3D dataframe. Instead, we take the ith row from each column
            # in sequence, to generate a SEQUENCE of 2D dataframes.
            for row in data_df[target["col"]].index:
                if row in stat.df_seq.keys():
                    stat.df_seq[row].loc[xlabel, ylabel] = data_df.loc[
                        row, target["col"]
                    ]
                else:
                    df = pd.DataFrame(columns=stat.ylabels, index=stat.xlabels)
                    df.loc[xlabel, ylabel] = data_df.loc[row, target["col"]]
                    stat.df_seq[row] = df


class ParallelCollator:
    """
    Generate :term:`Collated Run Output Data` files from :term:`Summary .csv`.

    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
    ) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.pathset = pathset

        utils.dir_create_checked(pathset.stat_collate_root, exist_ok=True)

    def __call__(
        self, criteria: bc.IConcreteBatchCriteria, targets: tp.List[types.YAMLDict]
    ) -> None:
        q = mp.JoinableQueue()  # type: mp.JoinableQueue

        # For each category of graphs we are generating
        for category in targets:
            # For each graph in each category
            for graph in category:
                q.put(graph)

        if self.cmdopts["processing_serial"]:
            parallelism = 1
        else:
            parallelism = psutil.cpu_count()

        for _ in range(0, parallelism):
            p = mp.Process(
                target=ParallelCollator._thread_worker,
                args=(q, self.main_config, self.cmdopts, self.pathset, criteria),
            )
            p.start()

        q.join()

    @staticmethod
    def _thread_worker(
        q: mp.Queue,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
        criteria,
    ) -> None:

        collator: tp.Union[UnivarGraphCollator, BivarGraphCollator]

        if criteria.is_univar():
            collator = UnivarGraphCollator(main_config, cmdopts, pathset)
        else:
            collator = BivarGraphCollator(main_config, cmdopts, pathset)

        while True:
            # Wait for 3 seconds after the queue is empty before bailing
            try:
                graph = q.get(True, 3)
                collator(criteria, graph)
                q.task_done()
            except queue.Empty:
                break


__all__ = [
    "UnivarGraphCollator",
    "BivarGraphCollator",
    "UnivarGraphCollationInfo",
    "BivarGraphCollationInfo",
    "ParallelCollator",
]
