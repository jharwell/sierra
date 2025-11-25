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
import pandas as pd
import networkx as nx

# Project packages


def supports_input(fmt: str) -> bool:
    return fmt == ".grapml"


def supports_output(fmt: type) -> bool:
    return fmt is nx.Graph


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)
def graph_read(
    path: pathlib.Path, run_output_root: tp.Optional[pathlib.Path] = None, **kwargs
) -> pd.DataFrame:
    """
    Read a dataframe from a .graphl file using networkx.
    """
    nx.read_graphml(path)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)
def graph_write(df: pd.DataFrame, path: pathlib.Path, **kwargs) -> None:
    """
    Write a dataframe to a CSV file using pandas.
    """
    df.to_csv(path, sep=",", float_format="%.8f", **kwargs)
