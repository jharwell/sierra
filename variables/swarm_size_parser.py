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


class SwarmSizeParser():
    """
    Parses the command line definition of batch criteria. The string must be
    formatted as:

    <increment_type><max size>

    - increment_type = {Log,Linear}

    For example:

    Log1024 -> Swarm sizes 1..1024 by powers of 2
    Linear1000 -> Swarm sizes 10...1000, step size of 100
    """

    def parse(self, criteria_str):
        ret = {}

        ret.update(self.increment_type_parse(criteria_str))
        ret.update(self.max_size_parse(criteria_str))
        return ret

    def increment_type_parse(self, criteria_str):
        """
        Parse the temporal variance type out of the batch criteria string. Valid values are:

        Log - Logarithmic in powers of 2.
        Linear - 10 linearly spaced sizes from max_size / 10 to max_size
        """
        ret = {}

        for s in ["Log", "Linear"]:
            index = criteria_str.find(s)
            if -1 != index:
                ret["increment_type"] = criteria_str[0:len(s)]

        return ret

    def max_size_parse(self, criteria_str):
        """
        Parse the max size from the batch criteria string.
        """
        ret = {}
        ret["linear_increment"] = None
        ret["max_size"] = None

        t_i = 0
        while not criteria_str[t_i].isdigit():
            t_i += 1

        ret["linear_increment"] = int(criteria_str[t_i:]) / 10
        ret["max_size"] = int(criteria_str[t_i:])
        return ret
