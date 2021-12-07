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

"""Classes for the ``--time-setup`` cmdline option. See :ref:`ln-vars-ts` for
usage documentation.

"""

# Core packages
import typing as tp
import re

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.xml import XMLAttrChangeSet, XMLAttrChange, XMLTagAdd, XMLTagRmList, XMLTagAddList, XMLLuigi
import sierra.core.config as config


@implements.implements(IBaseVariable)
class TimeSetup():
    """
    Defines the simulation duration.

    Attributes:
        duration: The simulation duration in seconds, NOT timesteps.
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


class Parser():
    """
    Enforces the cmdline definition of time setup criteria.
    """

    def __call__(self, arg: str) -> tp.Dict[str, int]:
        ret = {
            'n_secs_per_run': int(),
            'n_datapoints': int(),
            'n_ticks_per_sec': int(),
        }
        # Parse duration, which must be present
        res = re.search(r"T\d+", arg)
        assert res is not None, \
            "Bad duration specification in time setup '{0}'".format(arg)
        ret['n_secs_per_run'] = int(res.group(0)[1:])

        # Parse # datapoints to capture, which can be absent
        res = re.search(r"N\d+", arg)
        if res is not None:
            ret['n_datapoints'] = int(res.group(0)[1:])
        else:
            ret['n_datapoints'] = config.kExperimentalRunData['n_datapoints_1D']

        # Parse # ticks per second for controllers, which can be absent
        res = re.search(r"K\d+", arg)
        if res is not None:
            ret['n_ticks_per_sec'] = int(res.group(0)[1:])
        else:
            ret['n_ticks_per_sec'] = config.kGazebo['n_ticks_per_sec']

        return ret


def factory(arg: str, ros_param_server: bool) -> TimeSetup:
    """
    Factory to create :class:`TimeSetup` derived classes from the command
    line definition.

    Arguments:
       arg: The value of ``--time-setup``.
    """
    name = '.'.join(arg.split(".")[1:])
    attr = Parser()(arg)

    def __init__(self: TimeSetup) -> None:
        TimeSetup.__init__(self,
                           attr["n_secs_per_run"],
                           attr['n_datapoints'],
                           attr['n_ticks_per_sec'],
                           ros_param_server)

    return type(name,
                (TimeSetup,),
                {"__init__": __init__})  # type: ignore


__api__ = [
    'TimeSetup',
]
