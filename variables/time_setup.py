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
        self.sim_duration = sim_duration
        self.metric_interval = metric_interval

    def gen_attr_changelist(self):
        return [set([
            (".//experiment", "length", "{0}".format(self.sim_duration)),
            (".//experiment", "ticks_per_second", "{0}".format(kTicksPerSecond)),
            (".//output/metrics", "collect_interval", "{0}".format(self.metric_interval))])]

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []

# Just for testing


class TInterval(TimeSetup):
    def __init__(self):
        super().__init__(1000 / kTicksPerSecond, 1000 / kDataPoints)


class T1000(TimeSetup):
    def __init__(self):
        super().__init__(1000, 1000 * kTicksPerSecond / kDataPoints)


class T5000(TimeSetup):
    def __init__(self):
        super().__init__(5000, 5000 * kTicksPerSecond / kDataPoints)


class T10000(TimeSetup):
    def __init__(self):
        super().__init__(10000, 10000 * kTicksPerSecond / kDataPoints)


class T20000(TimeSetup):
    def __init__(self):
        super().__init__(20000, 20000 * kTicksPerSecond / kDataPoints)


class T50000(TimeSetup):
    def __init__(self):
        super().__init__(50000, 50000 * kTicksPerSecond / kDataPoints)


class T100000(TimeSetup):
    def __init__(self):
        super().__init__(100000, 100000 * kTicksPerSecond / kDataPoints)
