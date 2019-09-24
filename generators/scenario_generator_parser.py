"""
Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the terms of the GNU
  General Public License as published by the Free Software Foundation, either version 3 of the
  License, or (at your option) any later version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""

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

    def __call__(self, args):
        if args.scenario is None and args.batch_criteria is None:
            return None

        # Scenario specified via batch criteria
        if args.scenario is None:
            print(
                "- Parse scenario generator from cmdline criteria '{0}'".format(args.batch_criteria))

            res1 = re.search('[a-zA-Z]+', args.batch_criteria)
            assert res1 is not None,\
                "FATAL: Bad block dist specification in '{0}'".format(args.batch_criteria)
            res2 = re.search('[0-9]+x[0-9]+', args.batch_criteria)
            assert res2 is not None,\
                "FATAL: Bad arena_dim specification in '{0}'".format(args.batch_criteria)

            scenario = res1.group(0) + "." + res2.group(0)
        else:  # Scenario specified on cmdline
            print(
                "- Parse scenario generator from cmdline specification '{0}'".format(args.scenario))

            res1 = re.search('[a-zA-Z]+', args.scenario)
            assert res1 is not None,\
                "FATAL: Bad block dist specification in '{0}'".format(args.scenario)
            res2 = re.search('[0-9]+x[0-9]+', args.scenario)
            assert res2 is not None,\
                "FATAL: Bad arena_dim specification in '{0}'".format(args.scenario)

            scenario = res1.group(0) + "." + res2.group(0)
        return scenario
