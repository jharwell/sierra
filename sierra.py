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

# Core packages
import logging
import sys
from collections.abc import Iterable
import os

# 3rd party packages
import coloredlogs

# Project packages
import core.cmdline as cmd
import core.hpc as hpc
from core.pipeline.pipeline import Pipeline
from core.generators.controller_generator_parser import ControllerGeneratorParser
from core.generators.scenario_generator_parser import ScenarioGeneratorParser
import core.root_dirpath_generator as rdg
import core.plugin_manager


class SIERRA():
    def __init__(self) -> None:

        # check python version
        if sys.version_info < (3, 6):
            raise RuntimeError("Python >= 3.6 must be used to run SIERRA.")

        bootstrap_args, other_args = cmd.BootstrapCmdline().parser.parse_known_args()

        # Get nice colored logging output!
        coloredlogs.install(fmt='%(asctime)s %(levelname)s %(name)s  - %(message)s',
                            level=eval("logging." + bootstrap_args.log_level))

        self.logger = logging.getLogger(__name__)

        # Load non-project directory plugins
        pm = core.plugin_manager.DirectoryPluginManager()
        pm.initialize(os.path.join(os.getcwd(), 'plugins'))
        for plugin in pm.available_plugins():
            pm.load_plugin(plugin)

        # Load HPC plugins
        self.logger.info("Loading HPC plugins")
        pm = hpc.HPCPluginManager()
        pm.initialize(os.path.join(os.getcwd(), 'plugins', 'hpc'))
        for plugin in pm.available_plugins():
            pm.load_plugin(plugin)

        # Load project cmdline extensions
        self.logger.info("Loading cmdline extensions from project '%s'", bootstrap_args.project)
        try:
            module = __import__("projects.{0}.cmdline".format(bootstrap_args.project),
                                fromlist=["*"])
        except ModuleNotFoundError:
            self.logger.fatal("Project '%s' not found", bootstrap_args.project)
            raise

        # Validate cmdline args
        self.args = module.Cmdline().parser.parse_args(other_args)
        module.CmdlineValidator()(self.args)

        self.args = hpc.EnvConfigurer()(bootstrap_args.hpc_env, self.args)
        self.args.__dict__['project'] = bootstrap_args.project

    def __call__(self) -> None:
        # If only 1 pipeline stage is passed, then the list of stages to run is parsed as a non-iterable
        # integer, which can cause the generator to fail to be created. So make it iterable in that
        # case as well.
        if not isinstance(self.args.pipeline, Iterable):
            self.args.pipeline = [self.args.pipeline]

        if 5 not in self.args.pipeline:
            controller = ControllerGeneratorParser()(self.args)
            scenario = ScenarioGeneratorParser(self.args).parse_cmdline()

            self.logger.info("Controller=%s, Scenario=%s", controller, scenario)
            cmdopts = rdg.from_cmdline(self.args)
            pipeline = Pipeline(self.args, controller, cmdopts)
            pipeline.run()
        else:
            pipeline = Pipeline(self.args, None, {})
            pipeline.run()


if __name__ == "__main__":
    SIERRA()()
