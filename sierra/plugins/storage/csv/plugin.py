# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Plugin for reading/writing CSV files.
"""

# Core packages
import pathlib
import typing as tp

# 3rd party packages
from retry import retry
import pandas as pd

# Project packages


def supports_input(fmt: str) -> bool:
    return fmt == ".csv"


def supports_output(fmt: type) -> bool:
    return fmt is pd.DataFrame


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)
def df_read(
    path: pathlib.Path, run_output_root: tp.Optional[pathlib.Path] = None, **kwargs
) -> pd.DataFrame:
    """
    Read a dataframe from a CSV file using pandas.
    """
    # Always specify the datatype so pandas does not have to infer it--much
    # faster.
    return pd.read_csv(path, sep=",", **kwargs)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)
def df_write(df: pd.DataFrame, path: pathlib.Path, **kwargs) -> None:
    """
    Write a dataframe to a CSV file using pandas.
    """
    df.to_csv(path, sep=",", float_format="%.8f", **kwargs)
