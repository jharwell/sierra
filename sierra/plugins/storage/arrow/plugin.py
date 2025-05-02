# Copyright 2025 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Plugin for reading/writing apache .arrow files.
"""

# Core packages
import pathlib
import typing as tp

# 3rd party packages
from retry import retry
import pandas as pd

# Project packages


def suffixes() -> tp.Set[str]:
    return {'.arrow'}


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)  # type:ignore
def df_read(path: pathlib.Path, **kwargs) -> pd.DataFrame:
    """
    Read a pandas dataframe from an apache .arrow file.
    """
    return pd.read_feather(path)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)  # type:ignore
def df_write(df: pd.DataFrame, path: pathlib.Path, **kwargs) -> None:
    """
    Write a pandas dataframe to a apache .arrow file.
    """
    df.to_feather(path)
