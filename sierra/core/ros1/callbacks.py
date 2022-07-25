# Copyright 2021 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
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
