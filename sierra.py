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
"""
Main module/entry point for SIERRA, the helpful command line swarm-robotic automation tool.
"""

import cmdline as cmd
from pipeline.pipeline import Pipeline
from generators.controller_generator_parser import ControllerGeneratorParser
from generators.scenario_generator_parser import ScenarioGeneratorParser
from generators.generator_creator import GeneratorCreator
import variables.batch_criteria as bc
import collections
import pipeline.root_dirpath_generator as rdg
import coloredlogs
import logging


def __sierra_run_default(args):
    controller = ControllerGeneratorParser()(args)
    scenario = ScenarioGeneratorParser(args).parse_cmdline()

    # Add the template file leaf to the root directory path to help track what experiment was run.
    logging.info("Controller={0}, Scenario={1}".format(controller, scenario))
    cmdopts = rdg.from_cmdline(args)

    criteria = bc.Factory(args, cmdopts)
    joint_generator = GeneratorCreator()(args, controller, scenario, criteria, cmdopts)
    pipeline = Pipeline(args, joint_generator, criteria, cmdopts)
    pipeline.run()


def __sierra_run():
    # check python version
    import sys
    if sys.version_info < (3, 0):
        raise RuntimeError("Python 3.x should must be used to run this code.")

    # Get nice colored logging output!
    coloredlogs.install(fmt='%(asctime)s %(levelname)s - %(message)s')

    args = cmd.Cmdline().parser.parse_args()
    args = cmd.HPCEnvInheritor(args.hpc_env)(args)
    cmd.CmdlineValidator()(args)

    # If only 1 pipeline stage is passed, then the list of stages to run is parsed as a non-iterable
    # integer, which can causes the generator to fail to be created. So make it iterable in that
    # case as well.
    if not isinstance(args.pipeline, collections.Iterable):
        args.pipeline = [args.pipeline]

    if 5 not in args.pipeline:
        __sierra_run_default(args)
    else:
        pipeline = Pipeline(args, None, None, None)
        pipeline.run()


if __name__ == "__main__":
    __sierra_run()
