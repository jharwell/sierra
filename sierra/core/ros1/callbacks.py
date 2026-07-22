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
    exp_def: definition.ExpDefPickle,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
) -> int:
    """Extract population size from unpickled experiment definition."""
    for add in exp_def.element_adds:
        if "name" in add.attr and "n_agents" in add.attr["name"]:
            return int(add.attr["value"])

    return 0


def population_size_from_def(
    exp_def: definition.BaseExpDef, main_config: types.YAMLDict, cmdopts: types.Cmdopts
) -> int:
    """Extract population size from experiment definition."""
    bundle = definition.ExpDefPickle(
        attr_chgs=exp_def.attr_chgs, element_adds=exp_def.element_adds
    )
    return population_size_from_pickle(bundle, main_config, cmdopts)


def robot_prefix_extract(main_config: types.YAMLDict, cmdopts: types.Cmdopts) -> str:
    """Extract the common robot prefix based on cmdline opts + YAML config."""
    ros_section = main_config["ros"]
    assert isinstance(ros_section, dict), "'ros' section must be a mapping"
    ros = types.MainROSConfig.from_yaml(ros_section)
    return ros.robots[str(cmdopts["robot"])].prefix


__all__ = [
    "population_size_from_def",
    "population_size_from_pickle",
    "robot_prefix_extract",
]
