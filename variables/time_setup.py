"""
 Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

from variables.base_variable import BaseVariable
from variables.time_setup_parser import TimeSetupParser

kDataPoints = 50
kTicksPerSecond = 5


class TimeSetup(BaseVariable):

    """
    Defines the simulation duration, metric collection interval.

    Attributes:
      sim_duration(int): The simulation duration in seconds, NOT timesteps.
      metric_interval(int): Interval for metric collection.
    """

    def __init__(self, sim_duration, metric_interval):
        self.sim_duration = str(int(sim_duration))
        self.metric_interval = str(int(metric_interval))

    def gen_attr_changelist(self):
        return [set([
            (".//experiment", "length", "{0}".format(self.sim_duration)),
            (".//experiment", "ticks_per_second", "{0}".format(kTicksPerSecond)),
            (".//output/metrics", "collect_interval", "{0}".format(self.metric_interval))])]

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []


class TInterval(TimeSetup):
    def __init__(self):
        super().__init__(1000 / kTicksPerSecond, 1000 / kDataPoints)


def Factory(time_str):
    """
    Creates time setup classes from the command line definition of time setup.
    """
    attr = TimeSetupParser().parse(time_str.split(".")[1])

    def __init__(self):
        TimeSetup.__init__(self,
                           attr["sim_duration"],
                           attr["sim_duration"] * kTicksPerSecond / attr["n_datapoints"])

    return type(time_str,
                (TimeSetup,),
                {"__init__": __init__})
