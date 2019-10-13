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


import re


class SwarmSizeParser():
    """
    Parses the command line definition of batch criteria. The string must be
    formatted as:

    {increment_type}{max_size}

    - increment_type = {Log,Linear}
    - max_size = Integer

    For example:

    Log1024 -> Swarm sizes 1..1024 by powers of 2
    Linear1000 -> Swarm sizes 10...1000, step size of 100
    """

    def parse(self, criteria_str):
        ret = {}

        # Parse increment type
        res = re.search("^Log|Linear", criteria_str)
        assert res is not None, \
            "FATAL: Bad swarm size increment type in criteria '{0}'".format(criteria_str)
        ret['increment_type'] = res.group(0)

        # Parse max size
        res = re.search("[0-9]+", criteria_str)
        assert res is not None, \
            "FATAL: Bad swarm size max in criteria '{0}'".format(criteria_str)
        ret['max_size'] = int(res.group(0))

        # Set linear_increment if needed
        if ret['increment_type'] == 'Linear':
            ret['linear_increment'] = int(ret['max_size'] / 10.0)

        return ret
