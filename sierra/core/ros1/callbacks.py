# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""Common classes and callbacks :term:`Platforms <Platform>` using :term:`ROS1`.

"""

# Core packages
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core.experiment import xml, definition


def population_size_from_pickle(adds_def: tp.Union[xml.AttrChangeSet,
                                                   xml.TagAddList],
                                main_config: types.YAMLDict,
                                cmdopts: types.Cmdopts) -> int:
    for add in adds_def:
        if 'name' in add.attr and 'n_robots' in add.attr['name']:
            return int(add.attr['value'])

    return 0


def population_size_from_def(exp_def: definition.XMLExpDef,
                             main_config: types.YAMLDict,
                             cmdopts: types.Cmdopts) -> int:
    return population_size_from_pickle(exp_def.tag_adds, main_config, cmdopts)


def robot_prefix_extract(main_config: types.YAMLDict,
                         cmdopts: types.Cmdopts) -> str:
    return main_config['ros']['robots'][cmdopts['robot']]['prefix']


__api__ = [
    'population_size_from_pickle',
    'population_size_from_def',
    'robot_prefix_extract'
]
