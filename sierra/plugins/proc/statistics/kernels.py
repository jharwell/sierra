# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Kernels for the different types of statistics generated from experiments."""

# Core packages
import typing as tp

# 3rd party packages
import polars as pl
import numpy as np

# Project packages
from sierra.core import config


def conf95(
    groupby,
    ungrouped: pl.DataFrame,
) -> dict[str, pl.DataFrame]:
    """Generate stddev statistics plotting for 95% confidence intervals.

    Does not support non-numeric data.  Applicable to:

        - :func:`~sierra.core.graphs.stacked_line`

        - :func:`~sierra.core.graphs.summary_line`
    """
    # Get the grouping column names
    group_cols = groupby.by if hasattr(groupby, "by") else []

    # Build aggregation expressions for non-grouping columns only
    agg_exprs = []
    for col in ungrouped.columns:
        if col not in group_cols:
            agg_exprs.extend(
                [
                    pl.col(col).mean().alias(f"{col}_mean"),
                    pl.col(col).std().alias(f"{col}_std"),
                ]
            )

    # Aggregate by group
    df_like = groupby.agg(agg_exprs)
    if isinstance(df_like, pl.LazyFrame):
        df_like = df_like.collect()

    # Sort by grouping column to maintain order
    if group_cols:
        df_like = df_like.sort(group_cols[0])
        # Then drop the grouping column
        df_like = df_like.drop(group_cols)

    # Split into separate dataframes for mean and stddev
    mean_cols = [col for col in df_like.columns if col.endswith("_mean")]
    std_cols = [col for col in df_like.columns if col.endswith("_std")]

    df_mean = df_like.select(mean_cols).rename(lambda col: col.replace("_mean", ""))
    df_std = df_like.select(std_cols).rename(lambda col: col.replace("_std", ""))

    return {
        config.STATS["mean"].exts["mean"]: _fillna(_df_round(df_mean)),
        config.STATS["conf95"].exts["stddev"]: _fillna(_df_round(df_std)),
    }


def mean(groupby, ungrouped: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """
    Generate mean statistics only.

    Applicable to:

        - :func:`~sierra.core.graphs.summary_line`

        - :func:`~sierra.core.graphs.stacked_line`

        - :func:`~sierra.core.graphs.heatmap`

        - :func:`~sierra.core.graphs.confusion_matrix`

    .. versionchanged:: 1.5.6

       Now supports non-numeric columns via ``mode()``.
    """
    # Get the grouping column names
    group_cols = groupby.by if hasattr(groupby, "by") else []

    # Build expressions based on actual column dtypes
    agg_exprs = []
    for col in ungrouped.columns:
        if col not in group_cols:  # Skip grouping columns
            if ungrouped[col].dtype.is_numeric():
                agg_exprs.append(pl.col(col).mean().alias(col))
            else:
                agg_exprs.append(pl.col(col).mode().first().alias(col))

    # Aggregate by group - this computes stats for each group
    df_like = groupby.agg(agg_exprs)
    if isinstance(df_like, pl.LazyFrame):
        df_like = df_like.collect()

    # Sort by row_idx to maintain original order, because group_by() does not
    # preserve order
    df_like = df_like.sort(group_cols[0])
    # Then drop the row_idx column
    df_like = df_like.drop(group_cols)

    return {config.STATS["mean"].exts["mean"]: _fillna(df_like)}


def bw(groupby, ungrouped: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """
    Generate statistics for plotting box and whisker plots around data points.

    Does not support non-numeric data.  Applicable to:

        - :func:`~sierra.core.graphs.summary_line`
    """
    # Get the grouping column names
    group_cols = groupby.by if hasattr(groupby, "by") else []

    agg_exprs = []
    for col in ungrouped.columns:
        if col not in group_cols:

            # Numeric only!
            if not ungrouped[col].dtype.is_numeric():
                continue
            agg_exprs.extend(
                [
                    pl.col(col).mean().alias(f"{col}_mean"),
                    pl.col(col).median().alias(f"{col}_median"),
                    pl.col(col).quantile(0.25).alias(f"{col}_q1"),
                    pl.col(col).quantile(0.75).alias(f"{col}_q3"),
                    # Per-group, per-column sample size for the notch CI. Using
                    # count() (not a group-level count) means (a) n is the
                    # number of observations behind THIS median, as the
                    # McGill/Tukey/Larsen notch formula requires, and (b) nulls
                    # are excluded per column, so a group that is null/empty for
                    # a series gets n=0 there rather than a misleading value.
                    pl.col(col).count().alias(f"{col}_n"),
                    pl.col(col)
                    .filter(
                        pl.col(col)
                        >= (
                            pl.col(col).quantile(0.25)
                            - 1.5
                            * (pl.col(col).quantile(0.75) - pl.col(col).quantile(0.25))
                        )
                    )
                    .min()
                    .alias(f"{col}_whislo"),
                    pl.col(col)
                    .filter(
                        pl.col(col)
                        <= (
                            pl.col(col).quantile(0.75)
                            + 1.5
                            * (pl.col(col).quantile(0.75) - pl.col(col).quantile(0.25))
                        )
                    )
                    .max()
                    .alias(f"{col}_whishi"),
                ]
            )
    # For grouped data, aggregate
    stats = groupby.agg(agg_exprs)
    if isinstance(stats, pl.LazyFrame):
        stats = stats.collect()

    # Sort by grouping column to maintain order - group_by() does not do this by
    # default.
    stats = stats.sort(group_cols[0])
    # Then drop the grouping column
    stats = stats.drop(group_cols)

    # Extract individual statistics
    mean_cols = [col for col in stats.columns if col.endswith("_mean")]
    median_cols = [col for col in stats.columns if col.endswith("_median")]
    q1_cols = [col for col in stats.columns if col.endswith("_q1")]
    q3_cols = [col for col in stats.columns if col.endswith("_q3")]
    n_cols = [col for col in stats.columns if col.endswith("_n")]
    whislo_cols = [c for c in stats.columns if c.endswith("_whislo")]
    whishi_cols = [c for c in stats.columns if c.endswith("_whishi")]

    csv_whislo = _fillna(
        _df_round(stats.select(whislo_cols).rename(lambda c: c.replace("_whislo", "")))
    )
    csv_whishi = _fillna(
        _df_round(stats.select(whishi_cols).rename(lambda c: c.replace("_whishi", "")))
    )

    csv_mean = _fillna(
        _df_round(stats.select(mean_cols).rename(lambda col: col.replace("_mean", "")))
    )
    csv_median = _fillna(
        _df_round(
            stats.select(median_cols).rename(lambda col: col.replace("_median", ""))
        )
    )
    csv_q1 = _fillna(
        _df_round(stats.select(q1_cols).rename(lambda col: col.replace("_q1", "")))
    )
    csv_q3 = _fillna(
        _df_round(stats.select(q3_cols).rename(lambda col: col.replace("_q3", "")))
    )
    # Per-group, per-column sample size. Renamed to bare column names so its
    # column order matches csv_median/csv_q1/csv_q3, and NOT run through
    # _fillna (a null/empty group should read n=0, not be coerced to some
    # rounded float). Counts are integers; keep them as-is.
    csv_n = stats.select(n_cols).rename(lambda col: col.replace("_n", ""))

    # Calculate IQR and whiskers
    # Convert to numpy for element-wise operations
    q1_vals = csv_q1.to_numpy()
    q3_vals = csv_q3.to_numpy()
    median_vals = csv_median.to_numpy()
    n_vals = csv_n.to_numpy().astype(float)  # per-group, per-column sample size
    iqr = np.abs(q3_vals - q1_vals)  # Inter-quartile range

    # Notched-box confidence interval on the MEDIAN. The 1.57 constant is from:
    #
    # (Robert McGill, John W. Tukey and Wayne A. Larsen. Variations of Box
    # Plots, The American Statistician, Vol. 32, No. 1 (Feb., 1978), pp. 12-16
    #
    # n here MUST be the number of observations behind each median (the
    # per-group sample size), not the number of groups. It is array-valued
    # (one n per group per column), so use np.sqrt, not math.sqrt. Groups with
    # n==0 (null/empty for that series) have no valid CI: emit NaN there rather
    # than dividing by zero and drawing a bogus notch.
    with np.errstate(divide="ignore", invalid="ignore"):
        half = 1.57 * iqr / np.sqrt(n_vals)
    half = np.where(n_vals > 0, half, np.nan)
    cilo_vals = median_vals - half
    cihi_vals = median_vals + half

    # Convert back to DataFrames with same column names
    csv_cilo = pl.DataFrame(cilo_vals, schema=csv_median.columns)
    csv_cihi = pl.DataFrame(cihi_vals, schema=csv_median.columns)

    return {
        config.STATS["mean"].exts["mean"]: csv_mean,
        config.STATS["bw"].exts["median"]: csv_median,
        config.STATS["bw"].exts["q1"]: csv_q1,
        config.STATS["bw"].exts["q3"]: csv_q3,
        config.STATS["bw"].exts["cilo"]: csv_cilo,
        config.STATS["bw"].exts["cihi"]: csv_cihi,
        config.STATS["bw"].exts["whislo"]: csv_whislo,
        config.STATS["bw"].exts["whishi"]: csv_whishi,
    }


def _df_round(df: pl.DataFrame) -> pl.DataFrame:
    """Round all float columns to 8 decimal places."""
    return df.with_columns(
        [
            (
                pl.col(col).round(8)
                if df[col].dtype in [pl.Float32, pl.Float64]
                else pl.col(col)
            )
            for col in df.columns
        ]
    )


@tp.overload
def _fillna(df_like: tp.Union[np.float64, float]) -> np.float64: ...


@tp.overload
def _fillna(df_like: pl.DataFrame) -> pl.DataFrame: ...


def _fillna(
    df_like: tp.Union[pl.DataFrame, np.float64, float],
) -> tp.Union[pl.DataFrame, np.float64]:
    """Fill null values with 0."""
    # This is the general case for generating stats from a set of dataframes.
    if isinstance(df_like, pl.DataFrame):
        return df_like.fill_null(0)

    # This case is for performance measure stats which operate on scalars
    if isinstance(df_like, (np.float64, float)):
        return np.nan_to_num(df_like, nan=0)

    raise TypeError(f"Unknown type={type(df_like)}, value={df_like}")


__all__ = ["bw", "conf95", "mean"]
