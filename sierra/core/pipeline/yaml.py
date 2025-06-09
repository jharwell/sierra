# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Functionality for loading configuration from YAML.
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


def load_config(cmdopts: types.Cmdopts, name: str) -> tp.Optional[types.YAMLDict]:
    """Load YAML configuration for :term:`Project`.

     Load YAML configuration for projects.

     Returns:
         Dictionary of loaded configuration, or None if it doesn't exist.

    This function can be extended/overriden using a :term:`Project` hook. See
    :ref:`tutorials/project/hooks` for details.

    """
    root = pathlib.Path(cmdopts["project_config_root"])
    path = root / name

    if utils.path_exists(path):
        _logger.info(
            "Config for project %s from %s",
            cmdopts["project"],
            path,
        )
        with utils.utf8open(path) as f:
            return yaml.load(f, yaml.FullLoader)

    return None


__all__ = ["load_config"]
