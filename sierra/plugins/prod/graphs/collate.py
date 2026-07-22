# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Collation functionality for stage3 outputs according to configuration."""

# Core packages
import logging
import pathlib
import json
import re
import typing as tp

# 3rd party packages
import polars as pl

# Project packages
from sierra.core import utils, config, types, storage, batchroot
import sierra.core.variables.batch_criteria as bc
from sierra.plugins.prod.graphs import targets
from sierra.core import plugin as pm
from sierra.core.graphs import gconfig

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
        elif graph_type == "histogram":
            # Create empty DataFrame with experiment names as column names
            self.df = pl.DataFrame(schema=dict.fromkeys(exp_names))

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
                graph_type=str(target["type"]),
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
                    / (str(target["dest_stem"]) + stat.df_ext),
                    "storage.csv",
                )

            elif stat.some_srcs_exist:
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

            # An empty source file is a real outcome: the experiment ran but
            # produced no data for this source. Record it as a missing/null
            # datapoint rather than fabricating a value or attempting to read a
            # row out of an empty frame (which would raise). We deliberately do
            # NOT synthesize a 0/-1 sentinel: a null propagates to the collated
            # CSV as an empty field, which is distinguishable downstream from a
            # genuine measurement of zero.
            if data_df.is_empty():
                self.logger.warning(
                    "%s is empty; recording missing datapoint for '%s'",
                    csv_ipath,
                    exp_dir,
                )
                self._collate_exp_empty(exp_dir, stat)
                continue

            # Graph types with no inter-exp collation step (e.g. network,
            # confusion_matrix) simply have no entry here and are skipped.
            collator = self._COLLATORS.get(target["type"])

            if collator is not None:
                collator(self, target, exp_dir, stat, data_df)

    def _collate_exp_empty(self, exp_dir: str, stat: GraphCollationInfo) -> None:
        """Record a missing datapoint for ``exp_dir`` when its source is empty.

        Each graph type represents "no data for this experiment" differently.
        In all cases the gap is recorded as null/absent -- never as a synthesized
        0 or -1 -- so downstream consumers can distinguish "no data" from a real
        measurement.
        """
        if stat.graph_type == "summary_line":
            # __init__ seeds summary_col with None for every experiment, so an
            # experiment we never fill in already reads as null. Nothing to do.
            pass
        elif stat.graph_type == "stacked_line":
            # A stacked_line column *is* an experiment's time series. We cannot
            # contribute a correctly-sized column of nulls (its length is
            # defined by the other experiments' series, which we may not have
            # seen yet). Mark the source set incomplete so this routes into the
            # "not all experiments produced ..." warning rather than being
            # silently zero/null filled.
            stat.all_srcs_exist = False
        elif stat.graph_type == "heatmap":
            # Keep the (x, y) cell present with a null z, so the experiment
            # space stays complete and the gap is visible rather than dropped.
            res = re.match(r"c1-exp(\d+)\+c2-exp(\d+)", exp_dir)
            if res:
                row = pl.DataFrame(
                    {
                        "x": [int(res.group(1))],
                        "y": [int(res.group(2))],
                        "z": [None],
                    },
                    schema={"x": pl.Int64, "y": pl.Int64, "z": pl.Float64},
                )
                stat.df = pl.concat([stat.df, row], how="vertical")

    def _collate_exp_summary_line(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        # 'index' and 'col' are guaranteed present and well-typed by
        # schema.summary_line, validated up-front in gconfig.
        idx = target["index"]
        col = target["col"]

        # The source is non-empty but may still lack the requested column or
        # have too few rows for the requested index. Treat either as a missing
        # datapoint (null) rather than raising an opaque index error.
        if col not in data_df.columns:
            self.logger.warning(
                "Column '%s' absent in source for '%s'; recording missing datapoint",
                col,
                exp_dir,
            )
            self._collate_exp_empty(exp_dir, stat)
            return

        n = data_df.height
        resolved = idx if idx >= 0 else n + idx
        if not 0 <= resolved < n:
            self.logger.warning(
                "Index %d out of range (height %d) for '%s'; recording missing "
                "datapoint",
                idx,
                n,
                exp_dir,
            )
            self._collate_exp_empty(exp_dir, stat)
            return

        # Get datapoint from data_df at the resolved (positive) row index. In
        # polars we add an explicit row index first to access by position.
        data_df_indexed = data_df.with_row_index("__row_idx")

        datapoint = data_df_indexed.filter(pl.col("__row_idx") == resolved)[col][0]

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
        # 2026-07-22 [JRH]: schema.stacked_line marks 'cols' Optional because
        # it genuinely is for intra-exp. For inter-exp it is required, and must
        # name exactly one column: that column is extracted from every
        # experiment and becomes one column *per experiment* in the collated
        # frame. strictyaml cannot express "required in this section only", so
        # the rule is enforced here.
        if "cols" not in target:
            raise ValueError("'cols' is required for inter-exp stacked_line graphs")
        if len(target["cols"]) != 1:
            raise ValueError(
                "Exactly 1 column is required for inter-exp stacked_line graphs, "
                "got {}".format(target["cols"])
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
            n = stat.df.height
            if col_data.len() < n:
                self.logger.warning(
                    "Not all columns for %s have the same length--extending shorter col from %s",
                    target,
                    exp_dir,
                )
                col_data = col_data.extend_constant(None, n - col_data.len())
            stat.df = stat.df.with_columns(col_data.alias(exp_dir))

    def _collate_exp_heatmap(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        idx = target["index"]

        regex = r"c1-exp(\d+)\+c2-exp(\d+)"
        res = re.match(regex, exp_dir)

        assert (
            res and len(res.groups()) == 2
        ), f"Unexpected directory name '{exp_dir}': does not match regex {regex}"

        col = target["z"]

        # Non-empty source may still lack the column or the requested index.
        # Record the (x, y) cell with a null z rather than raising.
        if (
            col not in data_df.columns
            or not 0 <= (idx if idx >= 0 else data_df.height + idx) < data_df.height
        ):
            self.logger.warning(
                "Column '%s' or index %d unavailable for '%s'; recording null z",
                col,
                idx,
                exp_dir,
            )
            self._collate_exp_empty(exp_dir, stat)
            return

        resolved = idx if idx >= 0 else data_df.height + idx

        # Get z value from data_df at the resolved (positive) row index.
        data_df_indexed = data_df.with_row_index("__row_idx")
        z_value = data_df_indexed.filter(pl.col("__row_idx") == resolved)[col][0]

        # Create new row as DataFrame
        row = pl.DataFrame(
            {
                "x": [int(res.group(1))],
                "y": [int(res.group(2))],
                "z": [z_value],
            },
            schema={"x": pl.Int64, "y": pl.Int64, "z": pl.Float64},
        )

        # Concatenate vertically
        stat.df = pl.concat([stat.df, row], how="vertical")

    def _collate_exp_histogram(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        # 2026-07-22 [JRH]: 'cols' is required by schema.histogram, but the
        # "exactly one" rule is specific to inter-exp collation and cannot be
        # expressed there (the same schema serves intra-exp, where any number
        # of columns is valid). The named column is extracted from every
        # experiment, giving one column *per experiment* in the collated frame;
        # all of those are then plotted.
        if len(target["cols"]) != 1:
            raise ValueError(
                "Exactly 1 column is required for inter-exp histograms, "
                "got {}".format(target["cols"])
            )

        # Get the column data - target["cols"] is a list with one element
        col_data = data_df[target["cols"][0]]

        # If this is the first column being added, we need to handle the
        # empty DataFrame.
        if stat.df.height == 0:
            # Create DataFrame from the first column
            stat.df = pl.DataFrame({exp_dir: col_data})
        else:
            # Add this as a new column to existing stat.df. Columns of different
            # lengths are not really a problem for histograms, so we don't warn.
            n = stat.df.height
            if col_data.len() < n:
                col_data = col_data.extend_constant(None, n - col_data.len())
            stat.df = stat.df.with_columns(col_data.alias(exp_dir))

    #: Maps graph type onto the method which extracts that type's contribution
    #: from a single experiment. Types absent from this table have no inter-exp
    #: collation step. Defined after the methods it references so the names
    #: resolve.
    _COLLATORS: tp.ClassVar[dict[str, tp.Callable[..., None]]] = {
        "summary_line": _collate_exp_summary_line,
        "stacked_line": _collate_exp_stacked_line,
        "heatmap": _collate_exp_heatmap,
        "histogram": _collate_exp_histogram,
    }


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

    graphs_config = gconfig.load(cmdopts)
    inter_config = gconfig.section(graphs_config, "inter-exp")

    if inter_config is None:
        return

    loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")
    controller_config = loader.load_config(cmdopts, config.PROJECT_YAML.controllers)

    # 2026-01-05 [JRH]: Collect all graphs to process. This USED to be done in a
    # multiprocessing pool, but that was having problems with holoviews causing
    # hangs because (presumably) some lock being held by the main thread from
    # processing intra-experiment graphs which causes hangs when generated
    # graphs in sub-processes here.
    for category in targets.inter_exp_calc(inter_config, controller_config, cmdopts):
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
