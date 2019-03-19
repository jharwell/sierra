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


class GeneratorPairParser:
    """
    Parse the (controller, scenario) generator pair as a string tuple. These are then used later to
    create generator classes to make modifications to template input files.

    Format for pair is <decomposition depth>.<controller>.<scenario>

    <scenario> can be one of [SS,DS,QS,PL,RN].

    The scenario is optional; if it is omitted then the batch criteria are used to obtain the
    scenario (the last two letters of the batch criteria value specified on the command line) must
    match one of the scenarios specified above.

    Return:
      (controller, scenario) tuple, unless the generator is missing from the command line
      altogether; this can occur if the user is only running stage [4,5], and is not an error. In
      that case, None is returned for the pair.
    """

    def __call__(self, args):
        abbrev_dict = {"SS": "single_source",
                       "DS": "dual_source",
                       "QS": "quad_source",
                       "PL": "powerlaw",
                       "RN": "random"}

        if args.generator is None:
            return None
        else:
            components = args.generator.split('.')
            controller = components[0] + "." + components[1]

            # Scenario specified via batch criteria, and so the type of scenario is the last 2
            # letters of it.
            if 2 == len(components):
                print("- Parse (controller, scenario) generator specifications from cmdline "
                      "batch criteria '{0}'".format(args.batch_criteria))
                res = re.search('[a-zA-Z].[0-9]+x[0-9]+', args.batch_criteria)
                assert res is not None,\
                    "FATAL: Bad scenario+arena_dim specification in '{0}'".format(
                        args.batch_criteria)

                key = res.group(0)[:2]
                scenario = abbrev_dict[key] + "." + key + "Generator"
            else:  # Scenario specified as part of generator
                print("- Parse (controller,scenario) generator specifications from cmdline "
                      "generator '{0}'".format(args.generator))

                res = re.search('[a-zA-Z].[0-9]+x[0-9]+', components[2])
                assert res is not None,\
                    "FATAL: Bad scenario+arena_dim specification in '{0}'".format(
                        components[2])

                key = res.group(0)[:2]
                scenario = abbrev_dict[key] + "." + components[2]

            return (controller, scenario)
