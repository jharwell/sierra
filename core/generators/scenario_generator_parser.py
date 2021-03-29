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

    Format for pair is <scenario>.AxBxC

    <scenario> can be one of [SS,DS,QS,PL,RN]. A,B,C are the scenario dimensions.

    The Z dimension (C) is not optional (even for 2D simulations), due to how ARGoS handles LEDs
    internally.

    Return:
        Parsed scenario specification, unless missing from the command line altogether; this can
        occur if the user is only running stage [4,5], and is not an error. In that case, None is
        returned.
    """

    def __init__(self) -> None:
        self.scenario = None
        self.logger = logging.getLogger(__name__)

    def to_scenario_name(self, args):
        """
        Parse the scenario generator from cmdline arguments into a string.
        """
        # Stage 5
        if args.scenario is None:
            return None

        # Scenario specified on cmdline
        self.logger.info("Parse scenario generator from cmdline specification '%s'",
                         args.scenario)

        res1 = re.search('[SDQPR][SSSLN]', args.scenario)
        assert res1 is not None,\
            "FATAL: Bad block distribution specification in '{0}'".format(args.scenario)
        res2 = re.search('[0-9]+x[0-9]+x[0-9]+', args.scenario)

        assert res2 is not None,\
            "FATAL: Bad arena_dim specification in '{0}'".format(args.scenario)

        self.scenario = res1.group(0) + "." + res2.group(0)
        return self.scenario

    def to_dict(self, scenario: str):
        """
        Given a string (presumably a result of an earlier cmdline parse), parse it into a dictionary
        of components: arena_x, arena_y, arena_z, dist_type
        """
        x, y, z = scenario.split('+')[0].split('.')[1].split('x')
        dist_type = scenario.split('.')[0]

        return {
            'arena_x': int(x),
            'arena_y': int(y),
            'arena_z': int(z),
            'dist_type': dist_type
        }
