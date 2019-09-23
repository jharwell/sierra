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

import re


class SwarmDensityParser():
    """
    Parses the command line definition of batch criteria. The string must be
    formatted as:

    {density}{block_dist_type}{AxB}.I{Arena Size Increment}

    density              = <integer>p<integer> (i.e. 5p0 for 5.0)
    block_dist_type      = {SS,DS,QS,PL}
    AxB                  = X by Y arena dimensions of the starting arena size; the starting swarm
                           size will be computed from this and the desired density.
    arena size increment = Size in meters that the X and Y dimensions should increase by in between
                           experiments. Larger values here will result in larger arenas and more
                           robots being simulated at a given density. Must be an integer

    For example:

    1p0.SS12x8.I16 -> Constant density of 1.0, single source block distribution, starting with a
                      12x8 arena. Each experiment's arena will increase by 16 in both X and Y.

    Return: Dictionary with the following keys:

      target_density   -> Floating point value of parsed target density
      block_dist_class -> String representing the name of a block distribution class.
      arena_size_inc   -> Integer increment for arena size.
      arena_x          -> Initial arena X size.
      arena_y          -> Initial arena Y size.

    """

    def parse(self, criteria_str):
        ret = {}
        block_dist_dict = {
            'SS': 'TypeSingleSource',
            'DS': 'TypeDualSource',
            'QS': 'TypeQuadSource',
            'PL': 'TypePowerLaw'
        }
        # Need to have 3 dots/4 parts
        assert 4 == len(criteria_str.split('.')),\
            "Bad criteria formatting in criteria '{0}': must have 4 sections, separated by '.'".format(
                criteria_str)

        # Parse density
        density = criteria_str.split('.')[1]
        res = re.search('[0-9]+', density)
        assert res is not None, \
            "FATAL: Bad density characteristic specification in criteria '{0}'".format(criteria_str)

        characteristic = float(res.group(0))

        res = re.search('p[0-9]+', density)
        assert res is not None, \
            "FATAL: Bad density mantissa specification in criteria '{0}'".format(criteria_str)
        mantissa = float("0." + res.group(0)[1:])

        ret['target_density'] = characteristic + mantissa

        # Parse block distribution type
        res = None
        dist_and_dims = (criteria_str.split('.')[2])
        for key in block_dist_dict.keys():
            res = re.search(key, dist_and_dims)
            if res is not None:
                ret['block_dist_class'] = block_dist_dict[res.group(0)]
                break

        assert res is not None, \
            "FATAL: Bad block distribution type in criteria '{0}'".format(criteria_str)

        # Parse arena dimensions
        res = re.search('[0-9]+', dist_and_dims)
        assert res is not None, \
            "FATAL: Bad arena X specification in criteria '{0}'".format(criteria_str)
        ret['arena_x'] = int(res.group(0)[:-1])

        res = re.search('x[0-9]+', criteria_str)
        assert res is not None,\
            "FATAL: Bad arena Y specification in criteria '{0}'".format(criteria_str)
        ret['arena_y'] = int(res.group(0)[1:])

        # Parse arena size increment
        increment = criteria_str.split('.')[3]
        res = re.search('I[0-9]+', increment)
        assert res is not None, \
            "FATAL: Bad arena increment specification in criteria '{0}'".format(criteria_str)

        ret['arena_size_inc'] = int(res.group(0)[1:])

        return ret
