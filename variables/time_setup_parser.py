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


class TimeSetupParser():
    """
    Parses the command line definition of time setup. The string must be
    formatted as:

    T<duration in seconds>[N<Number of datapoints per simulation on all metrics (i.e. the granularity)>]

    For example:

    T1000 -> Simulation will be 1000 seconds long, default (50) # datapoints.
    T2000N100 -> Simulation will be 2000 seconds long, 100 datapoints (1 every 20 seconds).
    """

    def parse(self, time_str):
        ret = {}

        ret.update(self.duration_parse(time_str))
        ret.update(self.n_datapoints_parse(time_str))
        return ret

    def duration_parse(self, time_str):
        """
        Parse the simulation duration.
        """
        ret = {}

        if "N" in time_str:
            ret["sim_duration"] = int(time_str.split("N")[0][1:])
        else:
            ret["sim_duration"] = int(time_str[1:])
        return ret

    def n_datapoints_parse(self, time_str):
        """
        Parse the max size from the batch time string.
        """
        ret = {}
        if "N" in time_str:
            ret["n_datapoints"] = int(time_str.split("N")[1])
        else:
            ret["n_datapoints"] = 50
        return ret
