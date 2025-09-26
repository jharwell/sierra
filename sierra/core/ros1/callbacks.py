# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""Common classes and callbacks :term:`Engines <Engine>` using :term:`ROS1`."""

# Core packages
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core.experiment import definition


def population_size_from_pickle(
    adds_def: tp.Union[definition.AttrChangeSet, definition.ElementAddList],
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
) -> int:
    """Extracts population size from unpickled experiment definition."""
    for add in adds_def:
        if "name" in add.attr and "n_agents" in add.attr["name"]:
            return int(add.attr["value"])

    return 0


def population_size_from_def(
    exp_def: definition.BaseExpDef, main_config: types.YAMLDict, cmdopts: types.Cmdopts
) -> int:
    """Extracts population size from experiment definition."""
    return population_size_from_pickle(exp_def.element_adds, main_config, cmdopts)


def robot_prefix_extract(main_config: types.YAMLDict, cmdopts: types.Cmdopts) -> str:
    """Extracts the common robot prefix based on cmdline opts + YAML config."""
    return str(main_config["ros"]["robots"][cmdopts["robot"]]["prefix"])


__all__ = [
    "population_size_from_pickle",
    "population_size_from_def",
    "robot_prefix_extract",
]
