# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Plugin for reading/writing CSV files using polars.
"""

# Core packages
import pathlib
import typing as tp

# 3rd party packages
from retry import retry
import polars as pl

# Project packages


def supports_input(fmt: str) -> bool:
    return fmt == ".csv"


def supports_output(fmt: type) -> bool:
    return fmt is pl.DataFrame


@retry(Exception, tries=10, delay=0.100, backoff=1.1)
def df_read(
    path: pathlib.Path, run_output_root: tp.Optional[pathlib.Path] = None, **kwargs
) -> pl.DataFrame:
    """
    Read a dataframe from a CSV file using polars.
    """
    return pl.read_csv(path, separator=",", **kwargs)


@retry(Exception, tries=10, delay=0.100, backoff=1.1)
def df_write(df: pl.DataFrame, path: pathlib.Path, **kwargs) -> None:
    """
    Write a dataframe to a CSV file using polars.
    """
    df.write_csv(path, separator=",", float_precision=8, **kwargs)
