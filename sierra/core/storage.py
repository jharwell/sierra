# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
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
