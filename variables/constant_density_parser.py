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


class ConstantDensityParser():
    """
    Parses the command line definition of batch criteria. The string must be
    formatted as:

    {density}.I{Arena Size Increment}

    density              = <integer>p<integer> (i.e. 5p0 for 5.0)
    arena size increment = Size in meters that the X and Y dimensions should increase by in between
                           experiments. Larger values here will result in larger arenas and more
                           robots being simulated at a given density. Must be an integer.

    For example:

    1p0.I16 -> Constant density of 1.0. Each experiment's arena will increase by 16 in both X and Y.

    Return: Dictionary with the following keys:

      target_density   -> Floating point value of parsed target density
      arena_size_inc   -> Integer increment for arena size.

    """

    def parse(self, cmdline_str):
        ret = {}
        # Need to have 1 dot/2 parts
        assert 3 == len(cmdline_str.split('.')),\
            "Bad criteria formatting in criteria '{0}': must have 2 sections, separated by '.'".format(
                cmdline_str)

        # Parse density
        density = cmdline_str.split('.')[1]
        res = re.search('[0-9]+', density)
        assert res is not None, \
            "FATAL: Bad density characteristic specification in criteria '{0}'".format(cmdline_str)

        characteristic = float(res.group(0))

        res = re.search('p[0-9]+', density)
        assert res is not None, \
            "FATAL: Bad density mantissa specification in criteria '{0}'".format(cmdline_str)
        mantissa = float("0." + res.group(0)[1:])

        ret['target_density'] = characteristic + mantissa

        # Parse arena size increment
        increment = cmdline_str.split('.')[2]
        res = re.search('I[0-9]+', increment)
        assert res is not None, \
            "FATAL: Bad arena increment specification in criteria '{0}'".format(cmdline_str)

        ret['arena_size_inc'] = int(res.group(0)[1:])

        return ret
