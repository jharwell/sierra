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

"""Classes for the ``--time-setup`` cmdline option for :term:`Platforms
<Platform>` which use :term:`ROS`. See :ref:`ln-vars-ts` for usage
documentation.

"""

# Core packages
import typing as tp
import re

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.xml import XMLAttrChangeSet, XMLAttrChange, XMLTagAdd, XMLTagRmList, XMLTagAddList, XMLLuigi
from sierra.core import config
from sierra.core.variables.time_setup import Parser


@implements.implements(IBaseVariable)
class TimeSetup():
    """
    Attributes:

        n_secs_per_run: The :term:`Experimental Run` duration in seconds, NOT
                        :term:`Ticks <Tick>` or timesteps.

        n_datapoints: How many datapoints to capture during the experimental
                      run.

        n_ticks_per_sec: How many times per second robot controllers will be
                         run.

        ros_param_server: Should be use the ROS parameter server or not?

    """

    def __init__(self,
                 n_secs_per_run: int,
                 n_datapoints: int,
                 n_ticks_per_sec: int,
                 ros_param_server: bool) -> None:
        self.n_secs_per_run = n_secs_per_run
        self.n_datapoints = n_datapoints
        self.n_ticks_per_sec = n_ticks_per_sec
        self.attr_changes = []  # type: tp.List[XMLAttrChangeSet]
        self.ros_param_server = ros_param_server

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        if not self.attr_changes:
            if self.ros_param_server:
                chg = XMLAttrChange("./launch/param/[@name='sierra/experiment/length']",
                                    "value",
                                    str(self.n_secs_per_run))
            else:
                chg = XMLAttrChange("./params/sierra/experiment",
                                    "length",
                                    str(self.n_secs_per_run))

            self.attr_changes = [XMLAttrChangeSet(chg)]

        return self.attr_changes

    def gen_tag_rmlist(self) -> tp.List[XMLTagRmList]:
        return []

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        return []

    def gen_files(self) -> None:
        pass


def factory(arg: str, ros_param_server: bool) -> TimeSetup:
    """
    Factory to create :class:`TimeSetup` derived classes from the command
    line definition.

    Arguments:
       arg: The value of ``--time-setup``.
    """
    parser = Parser({'n_secs_per_run': config.kROS['n_secs_per_run'],
                     'n_ticks_per_sec': config.kROS['n_ticks_per_sec'],
                     'n_datapoints': config.kExperimentalRunData['n_datapoints_1D']})
    attr = parser(arg)

    def __init__(self: TimeSetup) -> None:
        TimeSetup.__init__(self,
                           attr["n_secs_per_run"],
                           attr['n_datapoints'],
                           attr['n_ticks_per_sec'],
                           ros_param_server)

    return type(attr['pretty_name'],
                (TimeSetup,),
                {"__init__": __init__})  # type: ignore


__api__ = [
    'TimeSetup',
]
