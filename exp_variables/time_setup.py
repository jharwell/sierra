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

from exp_variables.base_variable import BaseVariable

kMinPriority = 1
kMaxPriority = 10


class TimeSetup(BaseVariable):

    """
    Defines the simulation duration, metric collection interval.

    Attributes:
      sim_duration(int): The simulation duration.
      metric_interval(int): Interval for metric collection.
    """

    def __init__(self, sim_duration, metric_interval):
        self.sim_duration = sim_duration
        self.metric_interval = metric_interval

    def gen_attr_changelist(self):
        return [set([
            ("experiment.length", "{0}".format(self.sim_duration)),
            ("metrics.collect_interval", "{0}".format(self.metric_interval))])]


class Default(TimeSetup):
    def __init__(self):
        super().__init__(100000, 5000)


class Short(TimeSetup):
    def __init__(self):
        super().__init__(10000, 1000)


class Long(TimeSetup):
    def __init__(self):
        super().__init__(1000000, 50000)
