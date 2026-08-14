# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Collation functionality for stage3 outputs according to configuration.

Two data shapes are produced here, and which one a graph uses is a property of
the *kind of data*, not an inconsistency to be smoothed over:

- **Wide / columnar** (``stacked_line``, ``summary_line``, ``histogram``): one
  column per experiment. This is the natural shape for aligned time-series data
  that research code already emits (each run writes columns of a time series),
  so keeping it wide means projects "just work" without reshaping their output.
  Wide format requires all columns share a height; shorter series are padded
  with nulls (never zeros -- see below).

- **Long / rowwise** (``heatmap``, ``scatterplot``): one row per datapoint,
  carrying the experiment identity as a column. This is the natural shape for
  point sets, where each experiment contributes an independent number of points
  with no shared index. Long format sidesteps padding entirely: experiments
  just contribute different numbers of rows.

Missing data is *always* recorded as null/absent, never as a synthesized 0 or
-1 sentinel. A null propagates to the collated CSV as an empty field, which is
distinguishable downstream from a genuine measurement of zero. Fabricating a
zero would silently corrupt any statistic (mean, quartile, etc.) computed over
the collated data.

.. IMPORTANT:: The wide (time-series) path assumes all experiments in a batch
   share the same starting index/timepoint, so that padding a shorter series
   with trailing nulls aligns it correctly against the others. Series that
   start at *different* x-values would be silently misaligned by bottom-padding.
   If it is ever
   violated, the wide collators must switch to an explicit index-keyed join
   rather than positional padding.
"""

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


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

#: Univariate experiment directory name, e.g. ``c1-exp3``.
_EXP_RE_UNIVAR = re.compile(r"c1-exp(\d+)")

#: Bivariate experiment directory name, e.g. ``c1-exp2+c2-exp5``.
_EXP_RE_BIVAR = re.compile(r"c1-exp(\d+)\+c2-exp(\d+)")


def _parse_univar_exp(exp_dir: str) -> int:
    """Parse the single experiment index out of a univariate exp dir name."""
    res = _EXP_RE_UNIVAR.match(exp_dir)
    assert res and len(res.groups()) == 1, (
        f"Unexpected directory name '{exp_dir}': "
        f"does not match {_EXP_RE_UNIVAR.pattern}"
    )
    return int(res.group(1))


def _parse_bivar_exp(exp_dir: str) -> tp.Optional[tuple[int, int]]:
    """Parse the (x, y) experiment indices from a bivariate exp dir name.

    Returns None (rather than asserting) so callers can record a missing
    datapoint for a malformed/unexpected name instead of crashing the batch.
    """
    res = _EXP_RE_BIVAR.match(exp_dir)
    if not res or len(res.groups()) != 2:
        return None
    return int(res.group(1)), int(res.group(2))


def _resolve_index(idx: int, height: int) -> tp.Optional[int]:
    """Resolve a possibly-negative row index against a frame height.

    Returns the positive index if in range, else None (out of range).
    """
    resolved = idx if idx >= 0 else height + idx
    if not 0 <= resolved < height:
        return None
    return resolved


def _cell_at(data_df: pl.DataFrame, col: str, resolved: int) -> tp.Any:
    """Positional single-cell access. `resolved` must already be in range."""
    # Polars supports positional access directly; no need to build an indexed
    # copy and filter (which the previous code did in a per-experiment loop).
    return data_df[col][resolved]


# ---------------------------------------------------------------------------
# Collation state
# ---------------------------------------------------------------------------


class GraphCollationInfo:
    """Container for :term:`Collated Output Data` files for a particular graph.

    This is one of the focal points for the magic of SIERRA: here is where data
    is transformed into the dataframe shape that makes generation of a given
    graph type seamless when you want to look at data *across* the batch. The
    shape by graph type is as follows:

        - :func:`~sierra.core.graphs.stacked_line`: wide. Columns are the raw
          time-series data; column names are the experiment names.

        - :func:`~sierra.core.graphs.summary_line`: wide. One row per
          experiment; a single time-slice value per experiment in
          ``summary_col``.

        - :func:`~sierra.core.graphs.histogram`: wide. One column per
          experiment, each holding that experiment's raw values.

        - :func:`~sierra.core.graphs.heatmap`: long. ``(x, y, z)`` rows; x/y are
          the experiment-space indices parsed from the exp dir name, z is a
          single time-slice value.

        - :func:`~sierra.core.graphs.scatterplot`: long. ``(exp, x, y)`` rows;
          each experiment contributes its full set of (x, y) points.
    """

    #: Graph types whose collated frame is wide (one column per experiment).
    _WIDE_TYPES: tp.ClassVar[set[str]] = {
        "summary_line",
        "stacked_line",
        "histogram",
    }

    #: Graph types whose collated frame is long (one row per datapoint).
    _LONG_TYPES: tp.ClassVar[set[str]] = {
        "heatmap",
        "scatterplot",
    }

    def __init__(
        self, df_ext: str, exp_names: list[str], graph_type: str, summary_col: str
    ) -> None:
        self.df_ext = df_ext
        self.graph_type = graph_type
        self.summary_col = summary_col
        self.all_srcs_exist = True
        self.some_srcs_exist = False

        if graph_type == "summary_line":
            # Polars has no index; use an explicit "Experiment ID" column. Seed
            # summary_col with nulls so an experiment we never fill in already
            # reads as missing.
            self.df = pl.DataFrame(
                {"Experiment ID": exp_names, summary_col: [None] * len(exp_names)}
            )
        elif graph_type in ("stacked_line", "histogram"):
            # Wide: experiment names become column names, filled in as each
            # experiment is collated.
            self.df = pl.DataFrame(schema=dict.fromkeys(exp_names))
        elif graph_type == "heatmap":
            # Create empty DataFrame with x, y, z columns
            self.df = pl.DataFrame(
                schema={"x": pl.Int64, "y": pl.Int64, "z": pl.Float64}
            )
        elif graph_type == "scatterplot":
            self.df = pl.DataFrame(
                schema={"exp": pl.Int64, "x": pl.Float64, "y": pl.Float64}
            )
        else:
            # Fail loudly rather than leaving self.df unset (which would surface
            # as an opaque AttributeError deep in a collator later).
            raise ValueError(
                f"Unknown graph_type '{graph_type}': cannot build collation frame"
            )


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
            target["src"],
        )
        self.logger.trace(json.dumps(target, indent=4))

        exp_dirs = utils.exp_range_calc(
            self.cmdopts["exp_range"],
            self.pathset.output_root,
            criteria.gen_exp_names(),
        )

        # Always do the base, even if distribution stats are disabled.
        #
        # NOTE: copy the exts dict rather than aliasing it.
        center = self.cmdopts["center"]
        # We have to test for membership, because it is perfectly valid to run
        # this plugin with deterministic data which has fake/pseudo stats; i.e.,
        # the proc.statistics plugin is not active.
        if center == "mean":
            stat_config = dict(config.STATS["mean"].spreads["none"].exts)
            if self.cmdopts.get("spread", "none") == "conf95":
                stat_config.update(config.STATS["mean"].spreads["conf95"].exts)

            if self.cmdopts.get("spread", "none") == "bw":
                stat_config.update(config.STATS["mean"].spreads["bw"].exts)

        elif center == "median":
            stat_config = dict(config.STATS["median"].spreads["none"].exts)
            if self.cmdopts.get("spread", "none") == "iqr":
                stat_config.update(config.STATS["median"].spreads["iqr"].exts)

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
                    / (str(target["dest"]) + stat.df_ext),
                    "storage.csv",
                )

            elif stat.some_srcs_exist:
                self.logger.warning(
                    "Not all experiments in '%s' produced '%s%s'",
                    self.pathset.output_root,
                    target["src"],
                    stat.df_ext,
                )
            else:
                self.logger.warning(
                    "No experiments in <batchroot>/%s produced %s%s",
                    self.pathset.output_root.relative_to(self.pathset.root),
                    target["src"],
                    stat.df_ext,
                )

    def _collate_exp(
        self, target: dict, exp_dir: str, stats: list[GraphCollationInfo]
    ) -> None:
        exp_stat_root = self.pathset.stat_root / exp_dir

        for stat in stats:
            csv_ipath = pathlib.Path(exp_stat_root, target["src"] + stat.df_ext)
            if not utils.path_exists(csv_ipath):
                stat.all_srcs_exist = False
                continue

            stat.some_srcs_exist = True

            data_df = storage.df_read(csv_ipath, "storage.csv")

            # An empty source file is a real outcome: the experiment ran but
            # produced no data for this source. Record it as a missing/null
            # datapoint rather than fabricating a value or reading a row out of
            # an empty frame (which would raise).
            if data_df.is_empty():
                self.logger.warning(
                    "%s is empty; recording missing datapoint for '%s'",
                    csv_ipath,
                    exp_dir,
                )
                self._record_empty(exp_dir, stat)
                continue

            # Graph types with no inter-exp collation step (e.g. network,
            # confusion_matrix) simply have no entry here and are skipped.
            collator = self._COLLATORS.get(target["type"])

            if collator is not None:
                collator(self, target, exp_dir, stat, data_df)

    # -- empty/missing datapoint handling ----------------------------------

    def _record_empty(self, exp_dir: str, stat: GraphCollationInfo) -> None:
        """Record a missing datapoint for ``exp_dir``.

        Each graph type represents "no data for this experiment" differently.
        In all cases the gap is recorded as null/absent -- never a synthesized
        0 or -1 -- so downstream consumers can distinguish "no data" from a real
        measurement. Dispatches to a per-type handler so each type's full
        behavior (both the "have data" and "no data" paths) is discoverable
        from its two methods rather than a scattered if/elif.
        """
        handler = self._EMPTY_HANDLERS.get(stat.graph_type)
        if handler is not None:
            handler(self, exp_dir, stat)

    def _empty_summary_line(self, exp_dir: str, stat: GraphCollationInfo) -> None:
        # __init__ seeds summary_col with None for every experiment, so an
        # experiment we never fill in already reads as null. Nothing to do.
        pass

    def _empty_stacked_line(self, exp_dir: str, stat: GraphCollationInfo) -> None:
        # A stacked_line column *is* an experiment's time series. We cannot
        # contribute a correctly-sized column of nulls (its length is defined by
        # the other experiments' series, which we may not have seen yet). Mark
        # the source set incomplete so this routes into the "not all experiments
        # produced ..." warning rather than being silently null-filled.
        stat.all_srcs_exist = False

    def _empty_histogram(self, exp_dir: str, stat: GraphCollationInfo) -> None:
        # Same reasoning as stacked_line: a histogram column is the experiment's
        # raw values, whose length we cannot synthesize meaningfully.
        stat.all_srcs_exist = False

    def _empty_heatmap(self, exp_dir: str, stat: GraphCollationInfo) -> None:
        # Keep the (x, y) cell present with a null z, so the experiment space
        # stays complete and the gap is visible rather than dropped.
        xy = _parse_bivar_exp(exp_dir)
        if xy is None:
            return
        x, y = xy
        row = pl.DataFrame(
            {"x": [x], "y": [y], "z": [None]},
            schema={"x": pl.Int64, "y": pl.Int64, "z": pl.Float64},
        )
        stat.df = pl.concat([stat.df, row], how="vertical")

    def _empty_scatterplot(self, exp_dir: str, stat: GraphCollationInfo) -> None:
        # A scatterplot experiment contributes a variable number of points; an
        # empty source simply contributes none. Nothing to record -- the
        # experiment is absent from the long frame, which is the correct
        # representation of "no points."
        pass

    # -- per-type collators -------------------------------------------------

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
            self._record_empty(exp_dir, stat)
            return

        resolved = _resolve_index(idx, data_df.height)
        if resolved is None:
            self.logger.warning(
                "Index %d out of range (height %d) for '%s'; recording missing "
                "datapoint",
                idx,
                data_df.height,
                exp_dir,
            )
            self._record_empty(exp_dir, stat)
            return

        datapoint = _cell_at(data_df, col, resolved)

        # Update the row where Experiment ID matches exp_dir.
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
        # schema.stacked_line marks 'cols' Optional because it genuinely is for
        # intra-exp. For inter-exp it is required and must name exactly one
        # column: that column is extracted from every experiment and becomes one
        # column *per experiment* in the collated frame. strictyaml cannot
        # express "required in this section only", so the rule is enforced here.
        col = self._require_single_col(target, "stacked_line")
        col_data = data_df[col]
        self._append_wide_column(stat, exp_dir, col_data, warn=True, target=target)

    def _collate_exp_histogram(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        # 'cols' is required by schema.histogram, but the "exactly one" rule is
        # specific to inter-exp collation and cannot be expressed there (the
        # same schema serves intra-exp, where any number of columns is valid).
        # The named column is extracted from every experiment, giving one column
        # *per experiment* in the collated frame; all are then plotted.
        col = self._require_single_col(target, "histogram")
        col_data = data_df[col]
        # Columns of different lengths are expected for histograms (each is an
        # independent distribution), so no warning on length mismatch.
        self._append_wide_column(stat, exp_dir, col_data, warn=False, target=target)

    def _collate_exp_heatmap(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        xy = _parse_bivar_exp(exp_dir)
        assert xy is not None, (
            f"Unexpected directory name '{exp_dir}': "
            f"does not match {_EXP_RE_BIVAR.pattern}"
        )
        x, y = xy
        col = target["z"]

        # Non-empty source may still lack the column or the requested index.
        # Record the (x, y) cell with a null z rather than raising.
        resolved = (
            _resolve_index(target["index"], data_df.height)
            if col in data_df.columns
            else None
        )
        if resolved is None:
            self.logger.warning(
                "Column '%s' or index %d unavailable for '%s'; recording null z",
                col,
                target["index"],
                exp_dir,
            )
            self._record_empty(exp_dir, stat)
            return

        z_value = _cell_at(data_df, col, resolved)
        row = pl.DataFrame(
            {"x": [x], "y": [y], "z": [z_value]},
            schema={"x": pl.Int64, "y": pl.Int64, "z": pl.Float64},
        )

        # Concatenate vertically
        stat.df = pl.concat([stat.df, row], how="vertical")

    def _collate_exp_scatterplot(
        self,
        target: dict,
        exp_dir: str,
        stat: GraphCollationInfo,
        data_df: pl.DataFrame,
    ) -> None:
        exp = _parse_univar_exp(exp_dir)

        xcol = target["xcol"]
        ycol = target["ycol"]

        # A non-empty source may still lack one of the requested columns. Record
        # no points for this experiment rather than raising.
        if xcol not in data_df.columns or ycol not in data_df.columns:
            self.logger.warning(
                "Column '%s' or '%s' absent for '%s'; recording no points",
                xcol,
                ycol,
                exp_dir,
            )
            self._record_empty(exp_dir, stat)
            return

        # Build one long-format frame of this experiment's (x, y) points and
        # append it. Long format means differing per-experiment point counts
        # need no padding: each experiment simply contributes its own rows.
        new_rows = data_df.select(
            pl.col(xcol).cast(pl.Float64).alias("x"),
            pl.col(ycol).cast(pl.Float64).alias("y"),
        ).with_columns(pl.lit(exp, dtype=pl.Int64).alias("exp"))
        # Reorder to match the seeded schema (exp, x, y).
        new_rows = new_rows.select(["exp", "x", "y"])

        stat.df = pl.concat([stat.df, new_rows], how="vertical")

    # -- wide-append helper -------------------------------------------------

    @staticmethod
    def _require_single_col(target: dict, graph_type: str) -> str:
        """Enforce the inter-exp "exactly one column" rule; return that column."""
        if "cols" not in target:
            raise ValueError(f"'cols' is required for inter-exp {graph_type} graphs")
        if len(target["cols"]) != 1:
            raise ValueError(
                f"Exactly 1 column is required for inter-exp {graph_type} "
                f"graphs, got {target['cols']}"
            )
        return target["cols"][0]

    def _append_wide_column(
        self,
        stat: GraphCollationInfo,
        exp_dir: str,
        col_data: pl.Series,
        warn: bool,
        target: dict,
    ) -> None:
        """Append one experiment's series as a column in a wide frame.

        Reconciles length against the existing frame by padding the shorter side
        with trailing nulls. This assumes all experiments share a starting index
        (see module docstring): padding is only ever filling *trailing* missing
        positions. Padding uses nulls, never zeros -- any stats have already
        been computed per-experiment upstream, so these nulls represent absent
        tail positions and must stay distinguishable from real zeros.
        """
        # First column: seed the frame directly.
        if stat.df.height == 0:
            stat.df = pl.DataFrame({exp_dir: col_data})
            return

        n = stat.df.height
        if col_data.len() < n:
            if warn:
                self.logger.warning(
                    "Not all columns for %s have the same length--extending "
                    "shorter col from %s",
                    target["dest"],
                    exp_dir,
                )
            col_data = col_data.extend_constant(None, n - col_data.len())
        elif col_data.len() > n:
            if warn:
                self.logger.warning(
                    "Not all columns for %s have the same length--extending "
                    "existing cols",
                    target["dest"],
                )
            pad = col_data.len() - n
            padding = pl.DataFrame(
                {c: [None] * pad for c in stat.df.columns},
                schema=stat.df.schema,
            )
            stat.df = pl.concat([stat.df, padding])

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
        "scatterplot": _collate_exp_scatterplot,
    }

    #: Maps graph type onto the method which records a missing datapoint for an
    #: experiment whose source was empty/unusable. Kept parallel to _COLLATORS
    #: so each type's full behavior is co-located.
    _EMPTY_HANDLERS: tp.ClassVar[dict[str, tp.Callable[..., None]]] = {
        "summary_line": _empty_summary_line,
        "stacked_line": _empty_stacked_line,
        "heatmap": _empty_heatmap,
        "histogram": _empty_histogram,
        "scatterplot": _empty_scatterplot,
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
    # processing intra-experiment graphs which causes hangs when generating
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
