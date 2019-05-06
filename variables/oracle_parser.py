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


class OracleParser():
    """
    Parses the command line definition of batch criteria. The string must be formatted as:

    {oracle_name}

    oracle_name = {entities, tasks}

    For example:

    entities -> All permutations of oracular information about entities in the arena.
    tasks -> All permutations of oracular information about tasks in the arena.
    """

    def parse(self, criteria_str):
        ret = {}

        ret.update(self.type_parse(criteria_str))
        return ret

    def type_parse(self, criteria_str):
        """
        Parse the oracular information dissemination type.
        """
        ret = {}
        if 'entities' in criteria_str:
            ret['oracle_name'] = 'entities_oracle'
        elif 'tasking' in criteria_str:
            ret['oracle_name'] = 'tasking_oracle'
        return ret
