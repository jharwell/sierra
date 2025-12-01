# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Kernels for the different types of statistics generated from experiments."""

# Core packages
import typing as tp
import math

# 3rd party packages
import pandas as pd
import numpy as np

# Project packages
from sierra.core import config


def conf95(
    groupby: pd.core.groupby.generic.DataFrameGroupBy,
) -> dict[str, pd.DataFrame]:
    """Generate stddev statistics plotting for 95% confidence intervals.

    Does not support non-numeric data.

    Applicable to:

    - :func:`~sierra.core.graphs.stacked_line`
    - :func:`~sierra.core.graphs.summary_line`

    """
    return _conf95_kernel(groupby, groupby=True)


def mean(
    groupby: pd.core.groupby.generic.DataFrameGroupBy,
) -> dict[str, pd.DataFrame]:
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
    return _mean_kernel(groupby, groupby=True)


def bw(groupby: pd.core.groupby.generic.DataFrameGroupBy) -> dict[str, pd.DataFrame]:
    """
    Generate statistics for plotting box and whisker plots around data points.

    Does not support non-numeric data.

    Applicable to:

    - :func:`~sierra.core.graphs.summary_line`
    """
    return _bw_kernel(groupby, groupby=True, n_runs=groupby.size().to_numpy()[0])


def _conf95_kernel(df_like, groupby: bool) -> dict[str, pd.DataFrame]:
    # This is (apparently?) a bug in pandas: if the dataframe only has a single
    # row, then passing axis=1 when calculating mean, median, etc., does not
    # work, as the functions do NOT do their calculating across the single row,
    # but instead just take the value of the last colum in the row. Converting
    # the dataframe to a series fixes this.
    if not groupby:
        df_like = df_like.iloc[0, :]

    return {
        config.STATS["mean"].exts["mean"]: _fillna(_df_round(df_like.mean())),
        config.STATS["conf95"].exts["stddev"]: _fillna(_df_round(df_like.std())),
    }


def _mean_kernel(df_like, groupby: bool) -> dict[str, pd.DataFrame]:
    # This is (apparently?) a bug in pandas: if the dataframe only has a single
    # row, then passing axis=1 when calculating mean, median, etc., does not
    # work, as the functions do NOT do their calculating across the single row,
    # but instead just take the value of the last colum in the row. Converting
    # the dataframe to a series fixes this.
    if not groupby:
        df_like = df_like.iloc[0, :]

    return {
        config.STATS["mean"].exts["mean"]: _fillna(df_like.apply(_smart_aggregate_mean))
    }


def _bw_kernel(df_like, groupby: bool, n_runs: int) -> dict[str, pd.DataFrame]:
    # This is (apparently?) a bug in pandas: if the dataframe only has a single
    # row, then passing axis=1 when calculating mean, median, etc., does not
    # work, as the functions do NOT do their calculating across the single row,
    # but instead just take the value of the last colum in the row. Converting
    # the dataframe to a series fixes this.
    if not groupby:
        df_like = df_like.iloc[0, :]

    csv_mean = _fillna(_df_round(df_like.mean()))
    csv_median = _fillna(_df_round(df_like.median()))
    csv_q1 = _fillna(_df_round(df_like.quantile(0.25)))
    csv_q3 = _fillna(_df_round(df_like.quantile(0.75)))

    iqr = abs(csv_q3 - csv_q1)  # Inter-quartile range
    csv_whislo = csv_q1 - 1.50 * iqr
    csv_whishi = csv_q3 + 1.50 * iqr

    # The magic 1.57 is from the original paper:
    #
    # (Robert McGill, John W. Tukey and Wayne A. Larsen. Variations of Box
    # Plots, The American Statistician, Vol. 32, No. 1 (Feb., 1978), pp. 12-16
    csv_cilo = csv_median - 1.57 * iqr / math.sqrt(n_runs)
    csv_cihi = csv_median + 1.57 * iqr / math.sqrt(n_runs)

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


def _df_round(df_like):
    df_like.map(lambda x: round(x, 8) if isinstance(x, float) else x)
    return df_like


def _series_round(series: pd.Series) -> pd.Series:
    series.apply(lambda x: round(x, 8) if isinstance(x, float) else x)
    return series


def _smart_aggregate_mean(group) -> pd.Series:
    """
    Handle numeric and non-numeric data when aggregating for ``mean()``.
    """
    result = {}
    for col in group.columns:
        if pd.api.types.is_numeric_dtype(group[col]):
            result[col] = group[col].mean()
        else:
            # Use mode for non-numeric, fallback to first value if mode is empty
            mode_result = group[col].mode()
            result[col] = mode_result[0] if len(mode_result) > 0 else group[col].iloc[0]
    return pd.Series(result)


def _fillna(
    df_like: tp.Union[pd.DataFrame, np.float64, float],
) -> tp.Union[pd.DataFrame, np.float64]:
    # This is the general case for generating stats from a set of dataframes.
    if isinstance(df_like, pd.DataFrame):
        return df_like.fillna(0)

    # This case is for performance measure stats which operate on pd.Series,
    # which returns a single scalar.
    if isinstance(df_like, (np.float64, float)):
        return np.nan_to_num(df_like, nan=0)

    raise TypeError(f"Unknown type={type(df_like)}, value={df_like}")


__all__ = ["bw", "conf95", "mean"]
