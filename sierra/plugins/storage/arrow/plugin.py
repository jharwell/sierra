# Copyright 2025 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Plugin for reading/writing apache .arrow files using polars.
"""

# Core packages
import pathlib
import typing as tp

# 3rd party packages
from retry import retry
import polars as pl

# Project packages


def supports_input(fmt: str) -> bool:
    return fmt == ".arrow"


def supports_output(fmt: type) -> bool:
    return fmt is pl.DataFrame


@retry(Exception, tries=10, delay=0.100, backoff=1.1)
def df_read(
    path: pathlib.Path, run_output_root: tp.Optional[pathlib.Path] = None, **kwargs
) -> pl.DataFrame:
    """
    Read a polars dataframe from an apache .arrow file.
    """
    return pl.read_ipc(path, **kwargs)


@retry(Exception, tries=10, delay=0.100, backoff=1.1)
def df_write(df: pl.DataFrame, path: pathlib.Path, **kwargs) -> None:
    """
    Write a polars dataframe to a apache .arrow file.
    """
    df.write_ipc(path, **kwargs)
