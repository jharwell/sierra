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
import logging


class ScenarioGeneratorParser:
    """
    Parse the scenario specification from cmdline arguments; used later to
    create generator classes to make modifications to template input files.

    Format for pair is <scenario>.AxB[xC]

    <scenario> can be one of [SS,DS,QS,PL,RN]. A,B,C are the scenario dimensions.

    The Z dimension (C) is optional. If it is omitted, 1.0 is used.

    Return:
        Parsed scenario specification, unless missing from the command line altogether; this can occur
        if the user is only running stage [4,5], and is not an error. In that case, None is returned.
    """

    def __init__(self, args) -> None:
        self.args = args
        self.scenario = None

    def parse_cmdline(self):
        """
        Parse the scenario generator from cmdline arguments into a string.
        """
        # Stage 5
        if self.args.scenario is None:
            return None

        # Scenario specified on cmdline
        logging.info("Parse scenario generator from cmdline specification '%s'",
                     self.args.scenario)

        res1 = re.search('[SDQLR][SSSLN]', self.args.scenario)
        assert res1 is not None,\
            "FATAL: Bad block distribution specification in '{0}'".format(self.args.scenario)
        res2 = re.search('[0-9]+x[0-9]+x[0-9]+', self.args.scenario)

        if res2 is None:  # 2D simulation
            res2 = re.search('[0-9]+x[0-9]+', self.args.scenario)

        assert res2 is not None,\
            "FATAL: Bad arena_dim specification in '{0}'".format(self.args.scenario)

        self.scenario = res1.group(0) + "." + res2.group(0)
        return self.scenario

    @staticmethod
    def reparse_str(scenario):
        """
        Given a string (presumably a result of an earlier cmdline parse), parse it into a dictionary
        of components: arena_x, arena_y, dist_type
        """
        # Try parsing a 3D scenario dimension specification, and if that does not work, then it must
        # be a 2D scenario specification.
        try:
            x, y, z = scenario.split('.')[1].split('x')

        except ValueError:
            x, y = scenario.split('.')[1].split('x')
            z = 1.0

        dist_type = scenario.split('.')[0]

        return {
            'arena_x': int(x),
            'arena_y': int(y),
            'arena_z': int(z),
            'dist_type': dist_type
        }
