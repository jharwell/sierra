#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Preprocess inter-experiment outputs for stage 5.

Basically, gather statistics generated from controllers for graph generation in
previous stages into the correct files(s) for comparison.
"""

# Core packages
import pathlib
import typing as tp

# 3rd party packages
import polars as pl

# Project packages
from sierra.core import utils, config, storage
from sierra.core.variables import batch_criteria as bc


class IntraExpPreparer:
    """
    Collate generated stats from previous stages into files(s) for comparison.
    """

    def __init__(
        self,
        ipath_stem: pathlib.Path,
        ipath_leaf: str,
        opath_stem: pathlib.Path,
        criteria: bc.XVarBatchCriteria,
    ):
        self.ipath_stem = ipath_stem
        self.ipath_leaf = ipath_leaf
        self.opath_stem = opath_stem
        self.criteria = criteria

    def for_cc(
        self,
        controller: str,
        opath_leaf: str,
        index: int,
        inc_exps: tp.Optional[str],
    ) -> None:
        """
        Take batch-level dataframes and creates a new dataframe.

        Has:

        - Experiment names for the index.

        - Controller names as column names (guaranteed to be unique, since
          that's what we are comparing).

        - df[controller] columns as timeslices *across* columns (i.e., across
          experiments in the batch) in the source dataframe.
        """
        exts = config.STATS["mean"].exts
        exts.update(config.STATS["conf95"].exts)
        exts.update(config.STATS["bw"].exts)

        for k in exts:
            stat_ipath = pathlib.Path(self.ipath_stem, self.ipath_leaf + exts[k])
            stat_opath = pathlib.Path(self.opath_stem, opath_leaf + exts[k])
            df = self._cc_for_stat(stat_ipath, stat_opath, index, inc_exps, controller)

            if df is not None:
                storage.df_write(
                    df,
                    self.opath_stem / (opath_leaf + exts[k]),
                    "storage.csv",
                )

    def for_sc(
        self,
        scenario: str,
        opath_leaf: str,
        index: int,
        inc_exps: tp.Optional[str],
    ) -> None:
        """
        Take batch-level dataframes and creates a new dataframe.

        Has:

        - Experiment names for the index.

        - Scenario names as column names (guaranteed to be unique, since
          that's what we are comparing).

        - df[scenario] columns as timeslices *across* columns (i.e., across
          experiments in the batch) in the source dataframe.
        """
        exts = config.STATS["mean"].exts
        exts.update(config.STATS["conf95"].exts)
        exts.update(config.STATS["bw"].exts)

        for k in exts:
            stat_ipath = pathlib.Path(self.ipath_stem, self.ipath_leaf + exts[k])
            stat_opath = pathlib.Path(self.opath_stem, opath_leaf + exts[k])
            df = self._sc_for_stat(stat_ipath, stat_opath, index, inc_exps, scenario)

            if df is not None:
                storage.df_write(
                    df,
                    self.opath_stem / (opath_leaf + exts[k]),
                    "storage.csv",
                )

    def _cc_for_stat(
        self,
        ipath: pathlib.Path,
        opath: pathlib.Path,
        index: int,
        inc_exps: tp.Optional[str],
        controller: str,
    ) -> tp.Optional[pl.DataFrame]:

        if utils.path_exists(opath):
            cum_df = storage.df_read(opath, "storage.csv")
        else:
            cum_df = pl.DataFrame({"Experiment ID": self.criteria.gen_exp_names()})

        if utils.path_exists(ipath):
            df = storage.df_read(ipath, "storage.csv")

            # Get the row at the specified index
            row_data = df.row(index if index >= 0 else len(df) + index)

            # Add as a new column to cum_df
            return cum_df.with_columns(pl.Series(controller, row_data))

        return None

    def _sc_for_stat(
        self,
        ipath: pathlib.Path,
        opath: pathlib.Path,
        index: int,
        inc_exps: tp.Optional[str],
        scenario: str,
    ) -> tp.Optional[pl.DataFrame]:
        if utils.path_exists(opath):
            cum_df = storage.df_read(opath, "storage.csv")
        else:
            cum_df = pl.DataFrame({"Experiment ID": self.criteria.gen_exp_names()})

        if utils.path_exists(ipath):
            df = storage.df_read(ipath, "storage.csv")

            # Get the row at the specified index
            row_data = df.row(index if index >= 0 else len(df) + index)

            # Add as a new column to cum_df
            return cum_df.with_columns(pl.Series(scenario, row_data))

        return None


__all__ = ["IntraExpPreparer"]
