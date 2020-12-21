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

import logging
import sys
from collections.abc import Iterable
import os

import coloredlogs

import core.cmdline as cmd
import core.hpc as hpc
from core.pipeline.pipeline import Pipeline
from core.generators.controller_generator_parser import ControllerGeneratorParser
from core.generators.scenario_generator_parser import ScenarioGeneratorParser
import core.root_dirpath_generator as rdg
import core.plugin_manager


def __sierra_run_default(args):
    controller = ControllerGeneratorParser()(args)
    scenario = ScenarioGeneratorParser(args).parse_cmdline()

    logging.info("Controller=%s, Scenario=%s", controller, scenario)
    cmdopts = rdg.from_cmdline(args)
    pipeline = Pipeline(args, controller, cmdopts)
    pipeline.run()


def __sierra_run():
    # check python version

    if sys.version_info < (3, 6):
        raise RuntimeError("Python >= 3.6 must be used to run SIERRA.")

    bootstrap_args, other_args = cmd.BootstrapCmdline().parser.parse_known_args()

    # Get nice colored logging output!
    coloredlogs.install(fmt='%(asctime)s %(name)s %(levelname)s - %(message)s',
                        level=eval("logging." + bootstrap_args.log_level))
    logger = logging.getLogger(__name__)

    # Load non-project directory plugins
    pm = core.plugin_manager.DirectoryPluginManager()
    pm.initialize(os.path.join(os.getcwd(), 'plugins'))
    for plugin in pm.available_plugins():
        pm.load_plugin(plugin)

    # Load HPC plugins
    logger.info("Loading HPC plugins")
    pm = hpc.HPCPluginManager()
    pm.initialize(os.path.join(os.getcwd(), 'plugins', 'hpc'))
    for plugin in pm.available_plugins():
        pm.load_plugin(plugin)

    logger.info("Loading cmdline extensions from project '%s'", bootstrap_args.project)
    try:
        module = __import__("projects.{0}.cmdline".format(bootstrap_args.project),
                            fromlist=["*"])
    except ModuleNotFoundError:
        logger.fatal("Project '%s' not found", bootstrap_args.project)
        raise

    args = module.Cmdline().parser.parse_args(other_args)
    module.CmdlineValidator()(args)

    args = hpc.EnvConfigurer()(bootstrap_args.hpc_env, args)
    args.__dict__['project'] = bootstrap_args.project

    # If only 1 pipeline stage is passed, then the list of stages to run is parsed as a non-iterable
    # integer, which can cause the generator to fail to be created. So make it iterable in that
    # case as well.
    if not isinstance(args.pipeline, Iterable):
        args.pipeline = [args.pipeline]

    if 5 not in args.pipeline:
        __sierra_run_default(args)
    else:
        pipeline = Pipeline(args, None, {})
        pipeline.run()


if __name__ == "__main__":
    __sierra_run()
