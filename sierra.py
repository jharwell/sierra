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
from generators.controller_generator_parser import ControllerGeneratorParser
from generators.scenario_generator_parser import ScenarioGeneratorParser
from generators.generator_creator import GeneratorCreator
import variables.batch_criteria as bc
import collections


def __scenario_dir_name(batch_criteria, scenario):
    """
    Select the directory name for the root directory for batch input/output depending on what the
    batch criteria is. The default is to use the block distribution type + arena size to
    differentiate between batched experiments, for some batch criteria, those will be the same and
    so you need to use the batch criteria definition itself to uniquely identify.
    """

    if any(b in batch_criteria for b in ['swarm_density', 'temporal_variance']):
        # dash instead of dot to not confuse programs that rely on file extensions
        return scenario + '.' + '-'.join(batch_criteria.split('.')[1:])
    else:
        return scenario  # General case


def __sierra_run():
    # check python version
    import sys
    if sys.version_info < (3, 0):
        # restriction: cannot use Python 2.x to run this code
        raise RuntimeError("Python 3.x should must be used to run this code.")

    args = Cmdline().init().parse_args()

    controller = ControllerGeneratorParser()(args)
    scenario = ScenarioGeneratorParser()(args)

    # Add the template file leaf to the root directory path to help track what experiment was run.
    if controller is not None and scenario is not None:
        print("- Controller={0}, Scenario={1}".format(controller, scenario))

        template, ext = os.path.splitext(os.path.basename(args.template_config_file))

        scenario = __scenario_dir_name(args.batch_criteria, scenario)
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

    if args.batch_criteria is not None:
        criteria = bc.Factory(args)
        print("- Parse batch criteria into generator '{0}'".format(
            criteria.__class__.__name__))
    else:
        criteria = None

    joint_generator = GeneratorCreator()(args, controller, scenario, criteria)
    pipeline = ExpPipeline(args, joint_generator, criteria)
    pipeline.run()


if __name__ == "__main__":
    __sierra_run()
