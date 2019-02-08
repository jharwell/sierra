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
import collections

if __name__ == "__main__":
    # check python version
    import sys
    if sys.version_info < (3, 0):
        # restriction: cannot use Python 2.x to run this code
        raise RuntimeError("Python 3.x should must be used to run this code.")

    args = Cmdline().init().parse_args()

    pair = GeneratorPairParser()(args)

    # If batch criteria is used, prefer to use it to uniquely determine directory names. Otherwise,
    # if the user is not using batch criteria, but specified a controller + scenario combination for
    # the generator (including dimensions), use that to determine directory names.
    #
    # Also, add the template file leaf to the root directory path to help track what experiment was
    # run.
    if pair is not None:
        if "Generator" not in pair[1]:  # They specified scenario dimensions explicitly
            controller = pair[0]
            scenario = pair[1].split('.')[1]
        elif args.batch_criteria is not None:
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

    # If only 1 pipeline stage is passed, then the list of stages to run is parsed as a non-iterable
    # integer, which causes the generator to fail to be created sometimes, which is a problem. So
    # make it iterable in that case as well.
    if not isinstance(args.pipeline, collections.Iterable):
        args.pipeline = [args.pipeline]

    generator = GeneratorCreator()(args, pair)
    pipeline = ExpPipeline(args, generator)
    pipeline.run()
