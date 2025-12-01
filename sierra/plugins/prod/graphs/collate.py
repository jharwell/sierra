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
import re

# 3rd party packages
import pandas as pd

# Project packages
from sierra.core import utils, config, types, storage, batchroot
import sierra.core.variables.batch_criteria as bc
from sierra.plugins.prod.graphs import targets
from sierra.core import plugin as pm

_logger = logging.getLogger(__name__)


class GraphCollationInfo:
    """Container for :term:`Collated Output Data` files for a particular graph.

    This is one of the focal points for the magic of SIERRA: here is where time
    series data is transformed into different dataframe formats so as to make
    generation of different types of graphs seamless when you want to look at
    some data *across* the batch.  The for dataframes by graph type is as
    follows:

        - :func:`~sierra.core.graphs.stacked_line` : Columns are the raw time
          series data.  Column names are the names of the experiments.

        - :func:`~sierra.core.graphs.summary_line`: Columns are a single time
          slice of time series data.  Column names are the names of the
          experiments.  Indexed by (exp name, summary column).

        - :func:`~sierra.core.graphs.heatmap`: X,Y columns are the indices in
          the multidimensional array defining the experiment space, parsed out
          from the exp dirnames for the batch.  Z values are a single time slice
          of time series data for the specified column in each experiment in the
          batch.
    """

    def __init__(
        self, df_ext: str, exp_names: list[str], graph_type: str, summary_col: str
    ) -> None:
        self.df_ext = df_ext

        if graph_type == "summary_line":
            self.df = pd.DataFrame(index=exp_names, columns=[summary_col])
            self.df.index.name = "Experiment ID"
        elif graph_type == "stacked_line":
            self.df = pd.DataFrame(columns=exp_names)
        elif graph_type == "heatmap":
            self.df = pd.DataFrame(columns=["x", "y", "z"])

        self.graph_type = graph_type
        self.summary_col = summary_col
        self.all_srcs_exist = True
        self.some_srcs_exist = False


class GraphCollator:
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
            "Files from univariate experiment in <batch_root>/%s for graph '%s'",
            self.pathset.output_root.relative_to(self.pathset.root),
            target["src_stem"],
        )
        self.logger.trace(json.dumps(target, indent=4))

        exp_dirs = utils.exp_range_calc(
            self.cmdopts["exp_range"],
            self.pathset.output_root,
            criteria.gen_exp_names(),
        )

        # Always do the mean, even if stats are disabled
        stat_config = config.STATS["mean"].exts

        # We have to test for membership, because it is perfectly valid to run
        # this plugin with deterministic data which has fake/pseudo stats; i.e.,
        # the proc.statistics plugin is not active.
        if "dist_stats" in self.cmdopts and self.cmdopts["dist_stats"] in [
            "conf95",
            "all",
        ]:
            stat_config.update(config.STATS["conf95"].exts)

        if "dist_stats" in self.cmdopts and self.cmdopts["dist_stats"] in ["bw", "all"]:
            stat_config.update(config.STATS["bw"].exts)

        stats = [
            GraphCollationInfo(
                df_ext=suffix,
                exp_names=[e.name for e in exp_dirs],
                summary_col="{}+{}".format(
                    self.cmdopts["controller"], self.cmdopts["scenario"]
                ),
                graph_type=target["type"],
            )
            for suffix in stat_config.values()
        ]

        for diri in exp_dirs:
            self._collate_exp(target, diri.name, stats)

        for stat in stats:
            if stat.all_srcs_exist:
                storage.df_write(
                    stat.df,
                    self.pathset.stat_interexp_root
                    / (target["dest_stem"] + stat.df_ext),
                    "storage.csv",
                    index=stat.graph_type == "summary_line",
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
        self, target: dict, exp_dir: str, stats: list[GraphCollationInfo]
    ) -> None:
        exp_stat_root = self.pathset.stat_root / exp_dir

        for stat in stats:
            csv_ipath = pathlib.Path(exp_stat_root, target["src_stem"] + stat.df_ext)
            if not utils.path_exists(csv_ipath):
                stat.all_srcs_exist = False
                continue

            stat.some_srcs_exist = True

            data_df = storage.df_read(csv_ipath, "storage.csv")

            # 2025-07-08 [JRH]: This is the ONE place in all the graph
            # generation code which is a procedural switch on graph type.
            if target["type"] == "summary_line":
                idx = target.get("index", -1)

                if "col" not in target:
                    raise ValueError("'col' key is required")

                datapoint = data_df.loc[data_df.index[idx], target["col"]]
                if type(target["col"]) is list:
                    raise RuntimeError(
                        "Selected column {} must be a scalar, not list".format(
                            target["col"]
                        )
                    )
                stat.df.loc[exp_dir, stat.summary_col] = datapoint
            elif target["type"] == "stacked_line":
                if "cols" not in target:
                    raise ValueError("'cols' key is required")
                if len(target["cols"]) > 1:
                    raise ValueError(
                        "Exactly 1 column is required for inter-exp"
                        "stacked_line graphs"
                    )

                stat.df[exp_dir] = data_df[target["cols"]]
            elif target["type"] == "heatmap":
                idx = target.get("index", -1)

                regex = r"c1-exp(\d+)\+c2-exp(\d+)"
                res = re.match(regex, exp_dir)

                assert (
                    res and len(res.groups()) == 2
                ), f"Unexpected directory name '{exp_dir}': does not match regex {regex}"

                row = pd.DataFrame(
                    [
                        {
                            # group 0 is always the whole matched string
                            "x": int(res.group(1)),
                            "y": int(res.group(2)),
                            "z": data_df.loc[data_df.index[idx], target["col"]],
                        }
                    ]
                )

                stat.df = pd.concat([stat.df, row])


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Generate :term:`Collated Output Data` files from :term:`Batch Summary Data` files.

    """
    utils.dir_create_checked(pathset.stat_interexp_root, exist_ok=True)

    q = mp.JoinableQueue()  # type: mp.JoinableQueue

    loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")

    graphs_config = loader.load_config(cmdopts, config.PROJECT_YAML.graphs)

    if "inter-exp" not in graphs_config:
        _logger.warning(
            "Cannot collate data: 'inter-exp' key not found in graphs YAML config"
        )
        return

    controller_config = loader.load_config(cmdopts, config.PROJECT_YAML.controllers)

    # For each category of graphs we are generating
    for category in targets.inter_exp_calc(
        graphs_config["inter-exp"], controller_config, cmdopts
    ):
        # For each graph in each category
        for graph in category:
            q.put(graph)

    parallelism = cmdopts["processing_parallelism"]

    for _ in range(0, parallelism):
        p = mp.Process(
            target=_thread_worker,
            args=(q, main_config, cmdopts, pathset, criteria),
        )
        p.start()

    q.join()


def _thread_worker(
    q: mp.Queue,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria,
) -> None:

    collator = GraphCollator(main_config, cmdopts, pathset)
    while True:
        # Wait for 3 seconds after the queue is empty before bailing
        try:
            graph = q.get(True, 3)
            collator(criteria, graph)
            q.task_done()
        except queue.Empty:
            break


__all__ = [
    "GraphCollationInfo",
    "GraphCollator",
    "proc_batch_exp",
]
