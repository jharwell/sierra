# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Plugin for reading from CSV files when processing experimental run results.

"""

# Core packages
import pathlib

# 3rd party packages
from retry import retry
import pandas as pd

# Project packages


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)  # type:ignore
def df_read(path: pathlib.Path, **kwargs) -> pd.DataFrame:
    """
    Read a dataframe from a CSV file using pandas.
    """
    # Always specify the datatype so pandas does not have to infer it--much
    # faster.
    return pd.read_csv(path, sep=';', float_precision='high', **kwargs)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)  # type:ignore
def df_write(df: pd.DataFrame, path: pathlib.Path, **kwargs) -> None:
    """
    Write a dataframe to a CSV file using pandas.
    """
    df.to_csv(path, sep=';', float_format='%.8f', **kwargs)
