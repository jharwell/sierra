#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Preprocess intra-experiment outputs for stage 5.

Basically, gather statistics generated from controllers for graph generation in
previous stages into the correct files(s) for comparison.

If the batch criteria is univariate, then only :func:`across_rows` is valid;
for bivariate batch criteria, either :func:`across_rows` or
:func:`across_cols` is valid, depending on what the primary axis is.

    """

# Core packages
import pathlib
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
from sierra.core import utils, config, storage


class Preprocessor():
    """
    Basically, gather statistics generated from controllers for graph generation
    in previous stages into the correct files(s) for comparison.

    If the batch criteria is univariate, then only :func:`across_rows` is valid;
    for bivariate batch criteria, either :func:`across_rows` or
    :func:`across_cols` is valid, depending on what the primary axis is.
    """

    def __init__(self,
                 ipath_stem: pathlib.Path,
                 ipath_leaf: str,
                 opath_stem: pathlib.Path,
                 n_exp: int):
        self.ipath_stem = ipath_stem
        self.ipath_leaf = ipath_leaf
        self.opath_stem = opath_stem
        self.n_exp = n_exp

    def across_cols(self,
                    opath_leaf: str,
                    all_cols: tp.List[str],
                    col_index: int,
                    inc_exps: tp.Optional[str]) -> None:
        """Prepare statistics in column-major batch criteria.

        The criteria of interest varies across the rows of controller CSVs.  We
        take row `index` from a given dataframe and take the rows specified by
        the `inc_exps` and append them to a results dataframe column-wise, which
        we then write the file system.

        """
        exts = config.kStats['mean'].exts
        exts.update(config.kStats['conf95'].exts)
        exts.update(config.kStats['bw'].exts)

        for k in exts:
            stat_ipath = pathlib.Path(self.ipath_stem,
                                      self.ipath_leaf + exts[k])
            stat_opath = pathlib.Path(self.opath_stem,
                                      opath_leaf + exts[k])
            df = self._accum_df_by_col(stat_ipath,
                                       stat_opath,
                                       all_cols,
                                       col_index,
                                       inc_exps)

            if df is not None:
                writer = storage.DataFrameWriter('storage.csv')
                opath = self.opath_stem / (opath_leaf + exts[k])
                writer(df, opath, index=False)

    def across_rows(self,
                    opath_leaf: str,
                    index: int,
                    inc_exps: tp.Optional[str]) -> None:
        """Prepare statistics in row-major batch criteria.

        The criteria of interest varies across the columns of controller
        CSVs. We take row `index` from a given dataframe and take the columns
        specified by the `inc_exps` and append them to a results dataframe
        row-wise, which we then write the file system.

        """
        exts = config.kStats['mean'].exts
        exts.update(config.kStats['conf95'].exts)
        exts.update(config.kStats['bw'].exts)

        for k in exts:
            stat_ipath = pathlib.Path(self.ipath_stem,
                                      self.ipath_leaf + exts[k])
            stat_opath = pathlib.Path(self.opath_stem,
                                      opath_leaf + exts[k])
            df = self._accum_df_by_row(stat_ipath, stat_opath, index, inc_exps)

            if df is not None:
                writer = storage.DataFrameWriter('storage.csv')
                writer(df,
                       self.opath_stem / (opath_leaf + exts[k]),
                       index=False)

    def _accum_df_by_col(self,
                         ipath: pathlib.Path,
                         opath: pathlib.Path,
                         all_cols: tp.List[str],
                         col_index: int,
                         inc_exps: tp.Optional[str]) -> pd.DataFrame:
        reader = storage.DataFrameReader('storage.csv')

        if utils.path_exists(opath):
            cum_df = reader(opath)
        else:
            cum_df = None

        if utils.path_exists(ipath):
            t = reader(ipath)

            if inc_exps is not None:
                cols_from_index = utils.exp_include_filter(inc_exps,
                                                           list(t.index),
                                                           self.n_exp)
            else:
                cols_from_index = slice(None, None, None)

            if cum_df is None:
                cum_df = pd.DataFrame(columns=all_cols)

            # We need to turn each column of the .csv on the filesystem into a
            # row in the .csv which we want to write out, so we transpose, fix
            # the index, and then set the columns of the new transposed
            # dataframe.
            tp_df = t.transpose()
            tp_df = tp_df.reset_index(drop=True)
            tp_df = tp_df[cols_from_index]
            tp_df.columns = all_cols

            # Series are columns, so we have to transpose before concatenating
            cum_df = pd.concat([cum_df,
                                tp_df.loc[col_index, :].to_frame().T])

            # cum_df = pd.concat([cum_df, tp_df.loc[col_index, :]])
            return cum_df

        return None

    def _accum_df_by_row(self,
                         ipath: pathlib.Path,
                         opath: pathlib.Path,
                         index: int,
                         inc_exps: tp.Optional[str]) -> pd.DataFrame:
        reader = storage.DataFrameReader('storage.csv')
        if utils.path_exists(opath):
            cum_df = reader(opath)
        else:
            cum_df = None

        if utils.path_exists(ipath):
            t = reader(ipath)

            if inc_exps is not None:
                cols = utils.exp_include_filter(inc_exps,
                                                list(t.columns),
                                                self.n_exp)
            else:
                cols = t.columns

            if cum_df is None:
                cum_df = pd.DataFrame(columns=cols)

            # Series are columns, so we have to transpose before concatenating
            cum_df = pd.concat([cum_df,
                                t.loc[index, cols].to_frame().T])
            return cum_df

        return None
