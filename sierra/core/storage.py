# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Trampoline bindings for the various storage plugins that come with SIERRA.

See :ref:`tutorials/plugin/storage` for more details.
"""

# Core packages
import pathlib

# 3rd party packages
import pandas as pd

# Project packages
import sierra.core.plugin as pm
from sierra.core.trampoline import cmdline_parser


def df_read(path: pathlib.Path, medium: str, **kwargs) -> pd.DataFrame:
    """
    Dispatch "read from storage" request to active ``--storage`` plugin.
    """
    storage = pm.pipeline.get_plugin_module(medium)
    return storage.df_read(path, **kwargs)


def df_write(df: pd.DataFrame, path: pathlib.Path, medium: str, **kwargs) -> None:
    """
    Dispatch "write to storage" request to active ``--storage`` plugin.
    """
    storage = pm.pipeline.get_plugin_module(medium)
    return storage.df_write(df, path, **kwargs)


__all__ = ["df_read", "df_write"]
