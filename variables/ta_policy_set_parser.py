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


class TAPolicySetParser():
    """
    Parses the command line definition of batch criteria. The string must be formatted as:

    All.Z{swarm_size}

    For example:

    TAPolicy.Z16 -> All possible task allocation policies with swarms of size 16.
    """

    def parse(self, criteria_str):
        ret = {}

        # Parse task allocation policy set
        assert 'All' in criteria_str, "FATAL: Bad TAPolicy set in criteria '{0}'. Must be 'All'".format(
            criteria_str)
        # Parse swarm size
        res = re.search("\.Z[0-9]+", criteria_str)
        assert res is not None, "FATAL: Bad swarm size in criteria '{0}'".format(criteria_str)
        ret['swarm_size'] = int(res.group(0)[2:])
        return ret
