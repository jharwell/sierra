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


class SwarmDensityParser():
    """
    Parses the command line definition of batch criteria. The string must be
    formatted as:

    CD<density><block_dist_type>

    density = <integer>p<integer> (i.e. 5p0 for 5.0)
    block_dist_type = {SS}

    For example:

    CD1p0SS -> Constant density of 1.0, single source block distribution.
    """

    def parse(self, criteria_str):
        ret = {}

        ret.update(self.density_type_parse(criteria_str))
        ret.update(self.target_density_parse(criteria_str))
        ret.update(self.block_dist_type_parse(criteria_str))
        return ret

    def density_type_parse(self, criteria_str):
        """
        Parse the density type out of the batch criteria string. Valid values are:

        CD - Constant Density
        """
        ret = {}
        ret["density_type"] = "CD"
        return ret

    def target_density_parse(self, criteria_str):
        """
        Parse the target density out of the batch criteria string.
        """
        ret = {}
        t_i1 = 2
        while criteria_str[t_i1].isdigit():
            t_i1 += 1
        d1 = int(criteria_str[2:t_i1])
        t_i2 = t_i1 + 1  # For the 'p'
        while criteria_str[t_i2].isdigit():
            t_i2 += 1
        d2 = int(criteria_str[t_i1 + 1:t_i2])
        ret["target_density"] = float(int(d1) + d2 / ((t_i2 - (t_i1 + 1)) * 10))
        return ret

    def block_dist_type_parse(self, criteria_str):
        """
        Parse the block distribution type from the batch criteria string.
        """
        ret = {}
        print(criteria_str[-2:])
        if "SS" == criteria_str[-2:]:
            ret["block_dist_type"] = "TypeSingleSource"
        return ret
