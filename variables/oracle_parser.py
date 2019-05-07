"""
 Copyright 2019 John Harwell, All rights reserved.

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

import re


class OracleParser():
    """
    Parses the command line definition of batch criteria. The string must be formatted as:

    {oracle_name}.Z{swarm_size}

    oracle_name = {entities, tasks}

    For example:

    entities.Z16 -> All permutations of oracular information about entities in the arena, run with
    swarms of size 16.
    tasks.Z8 -> All permutations of oracular information about tasks in the arena, run with swarms
    of size 8.
    """

    def parse(self, criteria_str):
        ret = {}

        # Parse oracle name
        if 'entities' in criteria_str:
            ret['oracle_name'] = 'entities_oracle'
        elif 'tasking' in criteria_str:
            ret['oracle_name'] = 'tasking_oracle'
        # Parse swarm size
        res = re.search("\.Z[0-9]+", criteria_str)
        assert res is not None, "FATAL: Bad swarm size in criteria '{0}'".format(criteria_str)
        ret['swarm_size'] = int(res.group(0)[2:])
        return ret
