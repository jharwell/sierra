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
import sierra.core.cmdline as cmd
import sierra.core.hpc as hpc
from sierra.core.pipeline.pipeline import Pipeline
from sierra.core.generators.controller_generator_parser import ControllerGeneratorParser
import sierra.core.root_dirpath_generator as rdg
import sierra.core.plugin_manager as pm


class SIERRA():
    def __init__(self) -> None:

        # check python version
        if sys.version_info < (3, 6):
            raise RuntimeError("Python >= 3.6 must be used to run SIERRA.")

        bootstrap_args, other_args = cmd.BootstrapCmdline().parser.parse_known_args()

        # Get nice colored logging output!
        coloredlogs.install(fmt='%(asctime)s %(levelname)s %(name)s - %(message)s',
                            level=eval("logging." + bootstrap_args.log_level))

        self.logger = logging.getLogger(__name__)

        sierra_root = os.path.dirname(os.path.abspath(__file__))

        # Load non-project directory plugins
        dpm = pm.DirectoryPluginManager()
        dpm.initialize(os.path.join(sierra_root, 'plugins'))
        for plugin in dpm.available_plugins():
            dpm.load_plugin(plugin)

        # Load HPC plugins
        self.logger.info("Loading HPC plugins")
        hpc_pm = hpc.HPCPluginManager()
        hpc_pm.initialize(os.path.join(sierra_root, 'plugins', 'hpc'))
        for plugin in hpc_pm.available_plugins():
            hpc_pm.load_plugin(plugin)

        # Load project cmdline extensions
        self.logger.info("Loading cmdline extensions from project '%s'", bootstrap_args.project)
        path = "projects.{0}.cmdline".format(bootstrap_args.project)

        if not pm.module_exists(path):
            self.logger.exception("Module %s must exist!", path)
            raise ImportError

        module = pm.module_load(path)

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
            sgp = pm.module_load_tiered(self.args.project,
                                        'generators.scenario_generator_parser')
            scenario = sgp.ScenarioGeneratorParser().to_scenario_name(self.args)

            self.logger.info("Controller=%s, Scenario=%s", controller, scenario)
            cmdopts = rdg.from_cmdline(self.args)
            pipeline = Pipeline(self.args, controller, cmdopts)
            pipeline.run()
        else:
            pipeline = Pipeline(self.args, None, {})
            pipeline.run()
