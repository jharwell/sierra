#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Preprocess inter-experiment outputs for stage 5.

Basically, gather statistics generated from controllers for graph generation in
previous stages into the correct files(s) for comparison.
"""

# Core packages
import pathlib
import typing as tp
import logging

# 3rd party packages
import polars as pl

# Project packages
from sierra.core import utils, config, storage
from sierra.core.variables import batch_criteria as bc


_logger = logging.getLogger(__name__)


def _collate_row(
    cum_df: tp.Optional[pl.DataFrame],
    src_df: pl.DataFrame,
    index: int,
    include_exp: tp.Optional[str],
    column_key: str,
    exp_names: list,
) -> pl.DataFrame:
    """Collate a single row from ``src_df`` into ``cum_df``.

    Append one ``column_key`` column to ``cum_df`` from the ``index`` row of
    ``src_df``, filtering the included experiments by ``include_exp``. Requires
    that ``src_df`` corresponds to a time series dataframe.

    Shared by the statistic collation (:class:`IntraExpPreparer`) and the model
    collation in the comparators so that ``include_exp`` filters data
    identically in both, keeping the collated CSV, the model CSV, and the graph
    ticks aligned.

    """
    if cum_df is None:
        cum_df = pl.DataFrame({"Experiment ID": exp_names})

    if "Experiment ID" in src_df.columns:
        _logger.warning(
            "Source dataframe has 'Experiment ID' as a column; if this "
            "corresponds to a SIERRA summary_line graph dataframe, stage 5 "
            "will crash. If this is from project outputs this warning can "
            "safely be ignored."
        )
    row_data = list(src_df.row(index if index >= 0 else len(src_df) + index))

    if include_exp is not None:
        n_exps = len(exp_names)
        row_data = utils.exp_include_filter(include_exp, row_data, n_exps)

        if cum_df.height != len(row_data):
            filtered_names = utils.exp_include_filter(include_exp, exp_names, n_exps)
            cum_df = pl.DataFrame({"Experiment ID": filtered_names})

    return cum_df.with_columns(pl.Series(column_key, row_data))


def _collate_model_column(
    cum_df: tp.Optional[pl.DataFrame],
    model_df: pl.DataFrame,
    include_exp: tp.Optional[str],
    column_key: str,
    exp_names: list,
) -> pl.DataFrame:
    """Collate  a single model column (duh).

    Append one ``column_key`` column to ``cum_df`` from a model's per-
    experiment prediction column, filtering by ``include_exp``.

    Unlike :func:`collate_row` (which slices a single time-index *row* out of a
    1-row-per-datapoint statistics file), an inter-experiment model produces one
    prediction *per experiment*: an ``Experiment ID`` column plus a single value
    column, one row per experiment. So here we take the value *column* as the
    per-experiment series rather than a row. include_exp is applied identically
    to the statistics path so the model overlay stays aligned with the data and
    the graph ticks.

    """
    if cum_df is None:
        cum_df = pl.DataFrame({"Experiment ID": exp_names})

    # The model's value column is the last one (col 0 is "Experiment ID").
    value_col = model_df.columns[-1]
    col_data = model_df[value_col].to_list()

    if include_exp is not None:
        n_exps = len(exp_names)
        col_data = utils.exp_include_filter(include_exp, col_data, n_exps)

        if cum_df.height != len(col_data):
            filtered_names = utils.exp_include_filter(include_exp, exp_names, n_exps)
            cum_df = pl.DataFrame({"Experiment ID": filtered_names})

    return cum_df.with_columns(pl.Series(column_key, col_data))


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
        stat_center: str,
        stat_spread: str,
    ):
        self.ipath_stem = ipath_stem
        self.ipath_leaf = ipath_leaf
        self.opath_stem = opath_stem
        self.criteria = criteria
        self.stat_center = stat_center
        self.stat_spread = stat_spread

    def for_cc(
        self,
        controller: str,
        opath_leaf: str,
        index: int,
        include_exp: tp.Optional[str],
    ) -> None:
        """
        Take batch-level dataframes and create a new dataframe.

        Has:

        - Experiment names for the index.

        - Controller names as column names (guaranteed to be unique, since
          that's what we are comparing).

        - df[controller] columns as timeslices *across* columns (i.e., across
          experiments in the batch) in the source dataframe.
        """
        self._collate(controller, opath_leaf, index, include_exp)

    def for_sc(
        self,
        scenario: str,
        opath_leaf: str,
        index: int,
        include_exp: tp.Optional[str],
    ) -> None:
        """
        Take batch-level dataframes and create a new dataframe.

        Has:

        - Experiment names for the index.

        - Scenario names as column names (guaranteed to be unique, since
          that's what we are comparing).

        - df[scenario] columns as timeslices *across* columns (i.e., across
          experiments in the batch) in the source dataframe.
        """
        self._collate(scenario, opath_leaf, index, include_exp)

    def _collate(
        self,
        column_key: str,
        opath_leaf: str,
        index: int,
        include_exp: tp.Optional[str],
    ) -> None:
        """Collate one *thing* across all stats into comparison dataframes."""
        exts = {
            **config.STATS[self.stat_center].spreads["none"].exts,
            **config.STATS[self.stat_center].spreads[self.stat_spread].exts,
        }

        for v in exts.values():
            stat_ipath = pathlib.Path(self.ipath_stem, self.ipath_leaf + v)
            stat_opath = pathlib.Path(self.opath_stem, opath_leaf + v)
            df = self._for_stat(stat_ipath, stat_opath, index, include_exp, column_key)

            if df is not None:
                storage.df_write(
                    df,
                    self.opath_stem / (opath_leaf + v),
                    "storage.csv",
                )

    def _for_stat(
        self,
        ipath: pathlib.Path,
        opath: pathlib.Path,
        index: int,
        include_exp: tp.Optional[str],
        column_key: str,
    ) -> tp.Optional[pl.DataFrame]:
        if not utils.path_exists(ipath):
            return None

        cum_df = (
            storage.df_read(opath, "storage.csv") if utils.path_exists(opath) else None
        )
        src_df = storage.df_read(ipath, "storage.csv")

        return _collate_row(
            cum_df,
            src_df,
            index,
            include_exp,
            column_key,
            self.criteria.gen_exp_names(),
        )


__all__ = ["IntraExpPreparer"]
