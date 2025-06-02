# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Terminal interface for the various storage plugins that come with SIERRA.

See :ref:`tutorials/plugin/storage` for more details.
"""

# Core packages
import pathlib

# 3rd party packages
import pandas as pd

# Project packages
import sierra.core.plugin_manager as pm


def df_read(path: pathlib.Path, medium: str, **kwargs) -> pd.DataFrame:
    storage = pm.pipeline.get_plugin_module(medium)
    return storage.df_read(path, **kwargs)  # type: ignore


def df_write(df: pd.DataFrame, path: pathlib.Path, medium: str, **kwargs) -> None:
    storage = pm.pipeline.get_plugin_module(medium)
    return storage.df_write(df, path, **kwargs)  # type: ignore


__all__ = ["df_read", "df_write"]
