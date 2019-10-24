# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the terms of the GNU
#  General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#


import re


class ScenarioGeneratorParser:
    """
    Parse the scenario specification from cmdline arguments; used later to
    create generator classes to make modifications to template input files.

    Format for pair is <scenario>.AxB

    <scenario> can be one of [SS,DS,QS,PL,RN]. A and B are the scenario dimensions.

    The scenario is optional: if it is omitted then the batch criteria is used to obtain the
    scenario specification.

    Return:
      Parsed scenario specification, unless missing from the command line altogether; this can occur
      if the user is only running stage [4,5], and is not an error. In
      that case, None is returned.
    """

    def __init__(self, args):
        self.args = args
        self.scenario = None

    def parse_cmdline(self):
        """
        Parse the scenario generator from cmdline arguments into a string.
        """
        # Stage 5
        if self.args.scenario is None:
            return None

        else:  # Scenario specified on cmdline
            print(
                "- Parse scenario generator from cmdline specification '{0}'".format(self.args.scenario))

            res1 = re.search('[a-zA-Z]+', self.args.scenario)
            assert res1 is not None,\
                "FATAL: Bad block dist specification in '{0}'".format(self.args.scenario)
            res2 = re.search('[0-9]+x[0-9]+', self.args.scenario)
            assert res2 is not None,\
                "FATAL: Bad arena_dim specification in '{0}'".format(self.args.scenario)

            self.scenario = res1.group(0) + "." + res2.group(0)
        return self.scenario

    def reparse_str(scenario):
        """
        Given a string (presumably a result of an earlier cmdline parse), parse it into a dictionary
        of components: arena_x, arena_y, dist_type
        """
        x, y = scenario.split('.')[1].split('x')
        dist_type = scenario.split('.')[0]

        return {
            'arena_x': int(x),
            'arena_y': int(y),
            'dist_type': dist_type
        }
