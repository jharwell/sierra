# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Collation functionality for stage3 outputs according to configuration."""

# Core packages
import logging
import pathlib
import json
import re

# 3rd party packages
import polars as pl

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
            # Polars doesn't have index, so create explicit "Experiment ID" column
            self.df = pl.DataFrame(
                {"Experiment ID": exp_names, summary_col: [None] * len(exp_names)}
            )
        elif graph_type == "stacked_line":
            # Create empty DataFrame with experiment names as column names
            self.df = pl.DataFrame(schema=dict.fromkeys(exp_names))
        elif graph_type == "heatmap":
            # Create empty DataFrame with x, y, z columns
            self.df = pl.DataFrame(
                schema={"x": pl.Int64, "y": pl.Int64, "z": pl.Float64}
            )

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
                self._collate_exp_summary_line(target, exp_dir, stat, data_df)
            elif target["type"] == "stacked_line":
                self._collate_exp_stacked_line(target, exp_dir, stat, data_df)
            elif target["type"] == "heatmap":
                self._collate_exp_heatmap(target, exp_dir, stat, data_df)

    def _collate_exp_summary_line(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        idx = target.get("index", -1)

        if "col" not in target:
            raise ValueError("'col' key is required")

        # Get datapoint from data_df at specified index and column In
        # polars, we need to add row index first if accessing by
        # positio.n
        data_df_indexed = data_df.with_row_index("__row_idx")
        datapoint = data_df_indexed.filter(
            pl.col("__row_idx") == (idx if idx >= 0 else len(data_df) + idx)
        )[target["col"]][0]

        if type(target["col"]) is list:
            raise RuntimeError(
                "Selected column {} must be a scalar, not list".format(target["col"])
            )

        # Update the row where Experiment ID matches exp_dir
        stat.df = stat.df.with_columns(
            pl.when(pl.col("Experiment ID") == exp_dir)
            .then(pl.lit(datapoint))
            .otherwise(pl.col(stat.summary_col))
            .alias(stat.summary_col)
        )

    def _collate_exp_stacked_line(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        if "cols" not in target:
            raise ValueError("'cols' key is required")
        if len(target["cols"]) > 1:
            raise ValueError(
                "Exactly 1 column is required for inter-exp" "stacked_line graphs"
            )

        # Get the column data - target["cols"] is a list with one element
        col_data = data_df[target["cols"][0]]

        # If this is the first column being added, we need to handle the
        # empty DataFrame.
        if stat.df.height == 0:
            # Create DataFrame from the first column
            stat.df = pl.DataFrame({exp_dir: col_data})
        else:
            # Add this as a new column to existing stat.df
            stat.df = stat.df.with_columns(col_data.alias(exp_dir))

    def _collate_exp_heatmap(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        idx = target.get("index", -1)

        regex = r"c1-exp(\d+)\+c2-exp(\d+)"
        res = re.match(regex, exp_dir)

        assert (
            res and len(res.groups()) == 2
        ), f"Unexpected directory name '{exp_dir}': does not match regex {regex}"

        # Get z value from data_df at specified index and column
        data_df_indexed = data_df.with_row_index("__row_idx")
        z_value = data_df_indexed.filter(
            pl.col("__row_idx") == (idx if idx >= 0 else len(data_df) + idx)
        )[target["col"]][0]

        # Create new row as DataFrame
        row = pl.DataFrame(
            {
                "x": [int(res.group(1))],
                "y": [int(res.group(2))],
                "z": [z_value],
            }
        )

        # Concatenate vertically
        stat.df = pl.concat([stat.df, row], how="vertical")


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

    loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")

    graphs_config = loader.load_config(cmdopts, config.PROJECT_YAML.graphs)

    if "inter-exp" not in graphs_config:
        _logger.warning(
            "Cannot collate data: 'inter-exp' key not found in graphs YAML config"
        )
        return

    controller_config = loader.load_config(cmdopts, config.PROJECT_YAML.controllers)

    # 2026-01-05 [JRH]: Collect all graphs to process. This USED to be done in a
    # multiprocessing pool, but that was having problems with holoviews causing
    # hangs because (presumably) some lock being held by the main thread from
    # processing intra-experiment graphs which causes hangs when generated
    # graphs in sub-processes here.
    for category in targets.inter_exp_calc(
        graphs_config["inter-exp"], controller_config, cmdopts
    ):
        for graph in category:
            _proc_single_graph(main_config, cmdopts, pathset, criteria, graph)

    _logger.info("All graphs processed successfully")


def _proc_single_graph(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria,
    graph: types.YAMLDict,
) -> None:
    """Process a single graph. Called by worker processes."""
    collator = GraphCollator(main_config, cmdopts, pathset)
    collator(criteria, graph)


__all__ = [
    "GraphCollationInfo",
    "GraphCollator",
    "proc_batch_exp",
]
