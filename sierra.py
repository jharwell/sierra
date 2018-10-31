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

import os
from cmdline import Cmdline
from pipeline.exp_pipeline import ExpPipeline
from generator_pair_parser import GeneratorPairParser
from generator_creator import GeneratorCreator

if __name__ == "__main__":
    # check python version
    import sys
    if sys.version_info < (3, 0):
        # restriction: cannot use Python 2.x to run this code
        raise RuntimeError("Python 3.x should must be used to run this code.")

    args = Cmdline().init().parse_args()

    pair = GeneratorPairParser()(args)
    template, ext = os.path.splitext(os.path.basename(args.template_config_file))

    # If the user specified a controller + scenario combination for the generator (including
    # dimensions), use it to determine directory names.
    #
    # Otherwise, they *MUST* be using batch criteria, and so use the batch criteria to uniquely
    # specify directory names.
    #
    # Also, add the template file leaf to the root directory path to help track what experiment was
    # run.
    if pair is not None:
        if "Generator" not in pair[1]:  # They specified scenario dimensions explicitly
            controller = pair[0]
            scenario = pair[1].split('.')[1]
        else:  # They did not specify scenario dimensions explicitly
            controller = pair[0]
            scenario = args.batch_criteria.split('.')[1]

        template, ext = os.path.splitext(os.path.basename(args.template_config_file))

        print("- Controller={0}, Scenario={1}".format(controller, scenario))
        if args.generation_root is None:
            args.generation_root = os.path.join(args.sierra_root,
                                                controller,
                                                template + '-' + scenario,
                                                "exp-inputs")

        if args.output_root is None:
            args.output_root = os.path.join(args.sierra_root,
                                            controller,
                                            template + '-' + scenario,
                                            "exp-outputs")

        if args.graph_root is None:
            args.graph_root = os.path.join(args.sierra_root,
                                           controller,
                                           template + '-' + scenario,
                                           "graphs")

    generator = GeneratorCreator()(args, pair)

    pipeline = ExpPipeline(args, generator)
    pipeline.run()
