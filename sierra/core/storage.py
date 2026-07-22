# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Trampoline bindings for the various storage plugins that come with SIERRA.

See :ref:`tutorials/plugins/storage` for more details.
"""

# Core packages
import typing as tp
import pathlib

# 3rd party packages
import polars as pl
import networkx as nx

# Project packages
import sierra.core.plugin as pm
from sierra.core.trampoline import cmdline_parser


def df_read(path: pathlib.Path, medium: str, **kwargs) -> pl.DataFrame:
    """
    Dispatch "read DataFrame" request to active ``--storage`` plugin.
    """
    storage = pm.pipeline.get_plugin_module(medium)
    return storage.df_read(path, **kwargs)


def df_write(df: pl.DataFrame, path: pathlib.Path, medium: str, **kwargs) -> None:
    """
    Dispatch "write DataFrame" request to active ``--storage`` plugin.
    """
    storage = pm.pipeline.get_plugin_module(medium)
    return storage.df_write(df, path, **kwargs)


def graph_read(
    path: pathlib.Path,
    medium: str,
    run_output_root: tp.Optional[pathlib.Path] = None,
    **kwargs,
) -> nx.Graph:
    """
    Dispatch "read graph" request to active ``--storage`` plugin.
    """
    storage = pm.pipeline.get_plugin_module(medium)
    return storage.graph_read(path, **kwargs)


def graph_write(
    graph: nx.Graph,
    medium: str,
    path: pathlib.Path,
    **kwargs,
) -> nx.Graph:
    """
    Dispatch "write graph" request to active ``--storage`` plugin.
    """
    storage = pm.pipeline.get_plugin_module(medium)
    return storage.graph_write(graph, path, **kwargs)


__all__ = ["df_read", "df_write"]
