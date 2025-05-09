# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Functionality for loading stage 4 configuration from YAML.
"""
# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core import types, utils

_logger = logging.getLogger(__name__)


def load_config(cmdopts: types.Cmdopts) -> tp.Optional[types.YAMLDict]:
    """Load YAML configuration for :term:`Project` graphs to be generated.

     Load YAML configuratoin for graphs.

     This includes:

     - intra-experiment linegraphs

     - inter-experiment linegraphs

     - intra-experiment heatmaps

     - inter-experiment heatmaps (bivariate batch criteria only)

     Returns:
         Dictionary of loaded configuration.

    This function can be extended/overriden using a :term:`Project` hook. See
    :ref:`tutorials/project/hooks` for details.

    """
    root = pathlib.Path(cmdopts["project_config_root"])
    path = root / "graphs.yaml"

    if utils.path_exists(path):
        _logger.info(
            "Graph config for project '%s' from %s",
            cmdopts["project"],
            path,
        )
        with utils.utf8open(path) as f:
            return yaml.load(f, yaml.FullLoader)

    return None


__all__ = ["load_config"]
