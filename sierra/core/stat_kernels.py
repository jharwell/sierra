# Copyright 2021 John Harwell, All rights reserved.
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
"""Kernels for the different types of statistics generated from experiments.

"""
# Core packages
import typing as tp
import math

# 3rd party packages
import pandas as pd
import numpy as np

# Project packages
from sierra.core import config


class conf95:
    """Generate stddev statistics plotting for 95% confidence intervals.

    Applicable to:

    - :class:`~sierra.core.graphs.stacked_line_graph.StackedLineGraph`
    - :class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`

    """
    @staticmethod
    def from_groupby(groupby: pd.core.groupby.generic.DataFrameGroupBy) -> tp.Dict[str,
                                                                                   pd.DataFrame]:
        return _conf95_kernel(groupby, groupby=True)

    @staticmethod
    def from_pm(dfs: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        ret = {}

        for exp in dfs.keys():
            ret[exp] = _conf95_kernel(dfs[exp], groupby=False)

        return ret


class mean:
    """
    Generate mean statistics only. Applicable to line graphs and heatmaps.
    """
    @staticmethod
    def from_groupby(groupby: pd.core.groupby.generic.DataFrameGroupBy) -> tp.Dict[str,
                                                                                   pd.DataFrame]:
        return _mean_kernel(groupby, groupby=True)

    @staticmethod
    def from_pm(dfs: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        ret = {}

        for exp in dfs.keys():
            ret[exp] = _mean_kernel(dfs[exp], groupby=False)

        return ret


class bw:
    """
    Generate statistics for plotting box and whisker plots around data points.

    Applicable to:

    - :class:`~sierra.core.graphs.stacked_line_graph.StackedLineGraph`
    - :class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`
    """
    @staticmethod
    def from_groupby(groupby: pd.core.groupby.generic.DataFrameGroupBy) -> tp.Dict[str, pd.DataFrame]:
        return _bw_kernel(groupby, groupby=True, n_runs=groupby.size().values[0])

    @staticmethod
    def from_pm(dfs: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.core.groupby.generic.DataFrameGroupBy]:
        ret = {}
        for exp in dfs.keys():
            ret[exp] = _bw_kernel(dfs[exp],
                                  groupby=False,
                                  n_runs=len(dfs[exp].columns))

        return ret


def _conf95_kernel(df_like, groupby: bool) -> tp.Dict[str, pd.DataFrame]:
    # This is (apparently?) a bug in pandas: if the dataframe only has a single
    # row, then passing axis=1 when calculating mean, median, etc., does not
    # work, as the functions do NOT do their calculating across the single row,
    # but instead just take the value of the last colum in the row. Converting
    # the dataframe to a series fixes this.
    if not groupby:
        df_like = df_like.iloc[0, :]

    return {
        config.kStats['mean'].exts['mean']: _fillna(df_like.mean().round(8)),
        config.kStats['conf95'].exts['stddev']: _fillna(df_like.std().round(8))
    }


def _mean_kernel(df_like, groupby: bool) -> tp.Dict[str, pd.DataFrame]:
    # This is (apparently?) a bug in pandas: if the dataframe only has a single
    # row, then passing axis=1 when calculating mean, median, etc., does not
    # work, as the functions do NOT do their calculating across the single row,
    # but instead just take the value of the last colum in the row. Converting
    # the dataframe to a series fixes this.
    if not groupby:
        df_like = df_like.iloc[0, :]

    return {
        config.kStats['mean'].exts['mean']: _fillna(df_like.mean().round(8))
    }


def _bw_kernel(df_like, groupby: bool, n_runs: int) -> tp.Dict[str, pd.DataFrame]:
    # This is (apparently?) a bug in pandas: if the dataframe only has a single
    # row, then passing axis=1 when calculating mean, median, etc., does not
    # work, as the functions do NOT do their calculating across the single row,
    # but instead just take the value of the last colum in the row. Converting
    # the dataframe to a series fixes this.
    if not groupby:
        df_like = df_like.iloc[0, :]

    csv_mean = _fillna(round(df_like.mean(), 8))
    csv_median = _fillna(round(df_like.median(), 8))
    csv_q1 = _fillna(round(df_like.quantile(0.25), 8))
    csv_q3 = _fillna(round(df_like.quantile(0.75), 8))

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
        config.kStats['mean'].exts['mean']: csv_mean,
        config.kStats['bw'].exts['median']: csv_median,
        config.kStats['bw'].exts['q1']: csv_q1,
        config.kStats['bw'].exts['q3']: csv_q3,
        config.kStats['bw'].exts['cilo']: csv_cilo,
        config.kStats['bw'].exts['cihi']: csv_cihi,
        config.kStats['bw'].exts['whislo']: csv_whislo,
        config.kStats['bw'].exts['whishi']: csv_whishi
    }


def _fillna(df_like: tp.Union[pd.DataFrame, np.float64, float]) -> tp.Union[pd.DataFrame,
                                                                            np.float64]:
    # This is the general case for generating stats from a set of dataframes.
    if isinstance(df_like, pd.DataFrame):
        return df_like.fillna(0)
    # This case is for performance measure stats which operate on pd.Series,
    # which returns a single scalar.
    elif isinstance(df_like, (np.float64, float)):
        return np.nan_to_num(df_like, nan=0)

    raise TypeError(f"Unknown type={type(df_like)}, value={df_like}")


__api__ = [
    'conf95',
    'mean',
    'bw'
]
