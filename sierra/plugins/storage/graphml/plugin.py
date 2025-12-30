# Copyright 2025 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Plugin for reading/writing GraphML files.
"""

# Core packages
import pathlib
import typing as tp

# 3rd party packages
from retry import retry
import networkx as nx

# Project packages


def supports_input(fmt: str) -> bool:
    return fmt == ".grapml"


def supports_output(fmt: type) -> bool:
    return fmt is nx.Graph


@retry(Exception, tries=10, delay=0.100, backoff=1.1)
def graph_read(
    path: pathlib.Path, run_output_root: tp.Optional[pathlib.Path] = None, **kwargs
) -> nx.Graph:
    """
    Read a dataframe from a .graphl file using networkx.
    """
    return nx.read_graphml(path)


@retry(Exception, tries=10, delay=0.100, backoff=1.1)
def graph_write(graph: nx.Graph, path: pathlib.Path, **kwargs) -> None:
    """
    Write a dataframe to a CSV file using pandas.
    """
    nx.write_graphml(graph, path)
