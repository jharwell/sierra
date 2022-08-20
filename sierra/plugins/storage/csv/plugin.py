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
