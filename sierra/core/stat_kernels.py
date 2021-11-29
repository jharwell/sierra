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

# Core packages
import typing as tp
import math

# 3rd party packages
import pandas as pd
import numpy as np

# Project packages
import sierra.core.config as config


class conf95:
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
        config.kStatsExtensions['mean']: _fillna(df_like.mean().round(8)),
        config.kStatsExtensions['stddev']: _fillna(df_like.std().round(8))
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
        config.kStatsExtensions['mean']: _fillna(df_like.mean().round(8))
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
        config.kStatsExtensions['mean']: csv_mean,
        config.kStatsExtensions['median']: csv_median,
        config.kStatsExtensions['q1']: csv_q1,
        config.kStatsExtensions['q3']: csv_q3,
        config.kStatsExtensions['cilo']: csv_cilo,
        config.kStatsExtensions['cihi']: csv_cihi,
        config.kStatsExtensions['whislo']: csv_whislo,
        config.kStatsExtensions['whishi']: csv_whishi
    }


def _fillna(df_like: tp.Union[pd.DataFrame, np.float64]) -> tp.Union[pd.DataFrame,
                                                                     np.float64]:
    # This is the general case for generating stats from a set of dataframes.
    if isinstance(df_like, pd.DataFrame):
        return df_like.fillna(0)
    # This case is for performance measure stats which operate on pd.Series,
    # which returns a single scalar.
    elif isinstance(df_like, np.float64):
        return np.nan_to_num(df_like, nan=0)

    assert False, "Unknown type"
