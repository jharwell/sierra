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
Time Setup Definition:

    T{duration}[N{# datapoints per simulation}

    duration = Duration of simulation in seconds
    # datapoints per simulation = # rows in each .csv for all metrics (i.e. the granularity)

Examples:

    ``T1000``: Simulation will be 1000 seconds long, default (50) # datapoints.
    ``T2000N100``: Simulation will be 2000 seconds long, 100 datapoints (1 every 20 seconds).
"""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from core.variables.base_variable import IBaseVariable
from core.xml_luigi import XMLAttrChangeSet, XMLAttrChange, XMLTagRmList, XMLTagAddList

k1D_DATA_POINTS = 50
"""
Default # datapoints in each .csv of one-dimensional data.
"""

kND_DATA_DIVISOR = 10
"""
Default divisor for the output interval for  each .csv of two- or three-dimensional data, as
compared to the output interval for 1D data.
"""

kTICKS_PER_SECOND = 5
"""
Default # times each controller will be run per second in simulation.
"""


@implements.implements(IBaseVariable)
class TimeSetup():
    """
    Defines the simulation duration, metric collection interval.

    Attributes:
        sim_duration: The simulation duration in seconds, NOT timesteps.
        metric_interval: Base interval for metric collection.
    """
    @staticmethod
    def extract_explen(exp_def):
        """
        Extract and return the (experiment length in seconds) for the specified
        experiment.
        """
        for path, attr, value in exp_def:
            if 'experiment' in path and 'length' in attr:
                return int(value)
        return None

    def __init__(self, sim_duration: int, metric_interval: int) -> None:
        self.sim_duration = sim_duration
        self.metric_interval = metric_interval
        self.attr_changes = []  # type: tp.List

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        if not self.attr_changes:
            self.attr_changes = [XMLAttrChangeSet(XMLAttrChange(".//experiment",
                                                                "length",
                                                                "{0}".format(self.sim_duration)),
                                                  XMLAttrChange(".//experiment",
                                                                "ticks_per_second",
                                                                "{0}".format(kTICKS_PER_SECOND)),
                                                  XMLAttrChange(".//output/metrics/append",
                                                                "output_interval",
                                                                "{0}".format(self.metric_interval)),
                                                  XMLAttrChange(".//output/metrics/truncate",
                                                                "output_interval",
                                                                "{0}".format(self.metric_interval)),
                                                  XMLAttrChange(".//output/metrics/create",
                                                                "output_interval",
                                                                "{0}".format(max(1, self.metric_interval / kND_DATA_DIVISOR)))
                                                  )]
        return self.attr_changes

    def gen_tag_rmlist(self) -> tp.List[XMLTagRmList]:
        return []

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        return []


class TInterval(TimeSetup):
    def __init__(self) -> None:
        super().__init__(int(1000 / kTICKS_PER_SECOND), int(1000 / k1D_DATA_POINTS))


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
    def duration_parse(time_str: str) -> dict:
        """
        Parse the simulation duration.
        """
        ret = {}

        if "N" in time_str:
            ret["sim_duration"] = int(time_str.split("N")[0][1:])
        else:
            ret["sim_duration"] = int(time_str[1:])
        return ret

    @staticmethod
    def n_datapoints_parse(time_str: str) -> dict:
        """
        Parse the  # datapoints that will be present in each .csv.
        """
        ret = {}
        if "N" in time_str:
            ret["n_datapoints"] = int(time_str.split("N")[1])
        else:
            ret["n_datapoints"] = k1D_DATA_POINTS
        return ret


def factory(time_str: str) -> TimeSetup:
    """
    Factory to create :class:`TimeSetup` derived classes from the command line definition.
    """
    attr = Parser()(time_str.split(".")[1])

    def __init__(self) -> None:
        TimeSetup.__init__(self,
                           attr["sim_duration"],
                           int(attr["sim_duration"] * kTICKS_PER_SECOND / attr["n_datapoints"]))

    return type(time_str,  # type: ignore
                (TimeSetup,),
                {"__init__": __init__})


__api__ = [
    'k1D_DATA_POINTS',
    'kND_DATA_DIVISOR',
    'kTICKS_PER_SECOND',
    'TimeSetup',
    'TInterval',
]
