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
import logging # type: tp.Any
import sys
from collections.abc import Iterable
import os

# 3rd party packages

# Project packages
import sierra.core.cmdline as cmd
import sierra.core.hpc as hpc
import sierra.core.storage as storage
from sierra.core.pipeline.pipeline import Pipeline
from sierra.core.generators.controller_generator_parser import ControllerGeneratorParser
import sierra.core.root_dirpath_generator as rdg
import sierra.core.plugin_manager as pm
import sierra.core.logging


class SIERRA():
    def __init__(self) -> None:

        # check python version
        if sys.version_info < (3, 6):
            raise RuntimeError("Python >= 3.6 must be used to run SIERRA.")

        bootstrap = cmd.BootstrapCmdline()
        bootstrap_args, other_args = bootstrap.parser.parse_known_args()

        # Setup logging customizations
        sierra.core.logging.initialize(bootstrap_args.log_level)

        self.logger = logging.getLogger(__name__)

        sierra_root = os.path.dirname(os.path.abspath(__file__))

        # Load plugins
        self.logger.info("Loading plugins")
        plugin_core_path = [os.path.join(sierra_root, 'plugins', 'hpc'),
                            os.path.join(sierra_root, 'plugins', 'storage')]
        plugin_search_path = plugin_core_path
        env = os.environ.get('SIERRA_PLUGIN_PATH')
        if env is not None:
            plugin_search_path += env.split(os.pathsep)

        manager = pm.SIERRAPluginManager(plugin_search_path)
        manager.initialize()

        for plugin in manager.available_plugins():
            manager.load_plugin(plugin)

        # Update PYTHONPATH with SIERRA_PROJECT_PATH
        env = os.environ.get('SIERRA_PROJECT_PATH')
        if env is not None:
            # 2021/07/19: If you put the entries at the end of sys.path it
            # doesn't work for some reason...
            sys.path = env.split(os.pathsep) + sys.path[0:]

        # Load project cmdline extensions.
        project = bootstrap_args.project
        self.logger.info("Loading cmdline extensions from project '%s'",
                         project)
        path = "{0}.cmdline".format(project)
        module = pm.module_load(path)

        # Validate cmdline args
        self.args = module.Cmdline(bootstrap.parser,
                                   [-1, 1, 2, 3, 4, 5],
                                   False).parser.parse_args(other_args)
        module.CmdlineValidator()(self.args)

        self.args = hpc.EnvConfigurer()(bootstrap_args.hpc_env, self.args)
        self.args.__dict__['project'] = project

    def __call__(self) -> None:
        # If only 1 pipeline stage is passed, then the list of stages to run is
        # parsed as a non-iterable integer, which can cause the generator to
        # fail to be created. So make it iterable in that case as well.
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


def main():
    SIERRA()()


if __name__ == "__main__":
    main()
