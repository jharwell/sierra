# Copyright 2020 John Harwell, All rights reserved.
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
"""
Terminal interfare for the various storage plugins that come with SIERRA.

See :ref:`ln-sierra-tutorials-plugin-storage` for more details.
"""

# Core packages
import pathlib
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
import sierra.core.plugin_manager as pm


class DataFrameWriter():
    """
    Dispatcher to write a dataframe to the filesystem.
    """

    def __init__(self, medium: str):
        self.medium = medium

    def __call__(self,
                 df: pd.DataFrame,
                 path: tp.Union[pathlib.Path, str],
                 **kwargs) -> None:
        storage = pm.pipeline.get_plugin_module(self.medium)
        return storage.df_write(df, path, **kwargs)  # type: ignore


class DataFrameReader():
    """
    Dispatcher to read a dataframe from the filesystem.

    """

    def __init__(self, medium: str):
        self.medium = medium

    def __call__(self,
                 path: tp.Union[pathlib.Path, str],
                 **kwargs) -> pd.DataFrame:
        storage = pm.pipeline.get_plugin_module(self.medium)
        return storage.df_read(path, **kwargs)  # type: ignore


__api__ = [
    'DataFrameWriter',
    'DataFrameReader'
]
