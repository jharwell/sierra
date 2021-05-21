# Copyright 2018 John Harwell, All rights reserved.
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

"""
Classes for the ``--time-setup`` cmdline option. See :ref:`ln-vars-ts` for usage documentation.
"""

# Core packages
import typing as tp
import re

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.xml_luigi import XMLAttrChangeSet, XMLAttrChange, XMLTagRmList, XMLTagAddList, XMLLuigi
import sierra.core.config as config


@implements.implements(IBaseVariable)
class ARGoSTimeSetup():
    """
    Defines the simulation duration, metric collection interval.

    Attributes:
        duration: The simulation duration in seconds, NOT timesteps.
    """
    @staticmethod
    def extract_explen(exp_def: XMLAttrChangeSet) -> tp.Optional[int]:
        """
        Extract and return the (experiment length in seconds) for the specified
        experiment.
        """
        for path, attr, value in exp_def:
            if 'experiment' in path and 'length' in attr:
                return int(value)
        return None

    def __init__(self, duration: int, n_datapoints: int, n_ticks_per_sec: int) -> None:
        self.duration = duration
        self.n_datapoints: n_datapoints
        self.n_ticks_per_sec = n_ticks_per_sec
        self.attr_changes = []  # type: tp.List[XMLAttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        if not self.attr_changes:
            self.attr_changes = [XMLAttrChangeSet(XMLAttrChange(".//experiment",
                                                                "length",
                                                                "{0}".format(self.duration)),
                                                  XMLAttrChange(".//experiment",
                                                                "ticks_per_second",
                                                                "{0}".format(self.n_ticks_per_sec)),
                                                  )]
        return self.attr_changes

    def gen_tag_rmlist(self) -> tp.List[XMLTagRmList]:
        return []

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        return []


class Parser():
    """
    Enforces the cmdline definition of time setup criteria.
    """

    def __call__(self, arg: str) -> tp.Dict[str, int]:
        ret = {
            'duration': int(),
            'n_datapoints': int(),
            'n_ticks_per_sec': int(),
        }
        # Parse duration, which must be present
        res = re.search(r"T\d+", arg)
        assert res is not None, \
            "FATAL: Bad duration specification in time setup '{0}'".format(arg)
        ret['duration'] = int(res.group(0)[1:])

        # Parse # datapoints to capture, which can be absent
        res = re.search(r"N\d+", arg)
        if res is not None:
            ret['n_datapoints'] = int(res.group(0)[1:])
        else:
            ret['n_datapoints'] = config.k1D_DATA_POINTS_DEFAULT

        # Parse # ticks per second for controllers, which can be absent
        res = re.search(r"K\d+", arg)
        if res is not None:
            ret['n_ticks_per_sec'] = int(res.group(0)[1:])
        else:
            ret['n_ticks_per_sec'] = config.kTICKS_PER_SECOND_DEFAULT

        return ret


def factory(arg: str) -> ARGoSTimeSetup:
    """
    Factory to create :class:`ARGoSTimeSetup` derived classes from the command line definition.

    Parameters:
       arg: The value of ``--time-setup``
    """
    name = '.'.join(arg.split(".")[1:])
    attr = Parser()(arg)

    def __init__(self: ARGoSTimeSetup) -> None:
        ARGoSTimeSetup.__init__(self,
                                attr["duration"],
                                attr['n_datapoints'],
                                attr['n_ticks_per_sec'])

    return type(name,
                (ARGoSTimeSetup,),
                {"__init__": __init__})  # type: ignore


__api__ = [
    'ARGoSTimeSetup',
]
