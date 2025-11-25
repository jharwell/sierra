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


def supports_input(fmt: str) -> bool:
    return fmt == ".arrow"


def supports_output(fmt: type) -> bool:
    return fmt is pd.DataFrame


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)
def df_read(
    path: pathlib.Path, run_output_root: tp.Optional[pathlib.Path] = None, **kwargs
) -> pd.DataFrame:
    """
    Read a pandas dataframe from an apache .arrow file.
    """
    return pd.read_feather(path)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)
def df_write(df: pd.DataFrame, path: pathlib.Path, **kwargs) -> None:
    """
    Write a pandas dataframe to a apache .arrow file.
    """
    df.to_feather(path, **kwargs)
