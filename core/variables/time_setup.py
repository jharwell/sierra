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

# 3rd party packages
import implements

# Project packages
from core.variables.base_variable import IBaseVariable
from core.xml_luigi import XMLAttrChangeSet, XMLAttrChange, XMLTagRmList, XMLTagAddList, XMLLuigi


kTICKS_PER_SECOND = 10
"""
Default # times each controller will be run per second in simulation.
"""


k1D_DATA_POINTS = 50
"""
Default # datapoints in each .csv of one-dimensional data.
"""

kND_DATA_DIVISOR = 10
"""
Default divisor for the output interval for  each .csv of two- or three-dimensional data, as
compared to the output interval for 1D data.
"""


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

    def __init__(self, duration: int) -> None:
        self.duration = duration
        self.attr_changes = []  # type: tp.List[XMLAttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        if not self.attr_changes:
            self.attr_changes = [XMLAttrChangeSet(XMLAttrChange(".//experiment",
                                                                "length",
                                                                "{0}".format(self.duration)),
                                                  XMLAttrChange(".//experiment",
                                                                "ticks_per_second",
                                                                "{0}".format(kTICKS_PER_SECOND)),
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

    def __call__(self, time_str: str) -> tp.Dict[str, int]:
        ret = {}

        ret.update(Parser.duration_parse(time_str))
        ret.update(Parser.n_datapoints_parse(time_str))
        return ret

    @staticmethod
    def duration_parse(time_str: str) -> tp.Dict[str, int]:
        """
        Parse the simulation duration.
        """
        ret = {}

        if "N" in time_str:
            ret["duration"] = int(time_str.split("N")[0][1:])
        else:
            ret["duration"] = int(time_str[1:])
        return ret

    @staticmethod
    def n_datapoints_parse(time_str: str) -> tp.Dict[str, int]:
        """
        Parse the  # datapoints that will be present in each .csv.
        """
        ret = {}
        if "N" in time_str:
            ret["n_datapoints"] = int(time_str.split("N")[1])
        else:
            ret["n_datapoints"] = k1D_DATA_POINTS
        return ret


def factory(cmdline: str) -> ARGoSTimeSetup:
    """
    Factory to create :class:`ARGoSTimeSetup` derived classes from the command line definition.

    Parameters:
       cmdline: The value of ``--time-setup``
    """
    name = cmdline.split(".")[1]
    attr = Parser()(name)

    def __init__(self: ARGoSTimeSetup) -> None:
        ARGoSTimeSetup.__init__(self, attr["duration"])

    return type(name,
                (ARGoSTimeSetup,),
                {"__init__": __init__})  # type: ignore


__api__ = [
    'k1D_DATA_POINTS',
    'kND_DATA_DIVISOR',
    'kTICKS_PER_SECOND',
    'ARGoSTimeSetup',
]
