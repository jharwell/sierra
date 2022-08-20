# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#
"""Main module/entry point for SIERRA."""

# Core packages
import logging
import sys
from collections.abc import Iterable
import os
import multiprocessing as mp
import pathlib

# 3rd party packages

# Project packages
import sierra.core.cmdline as cmd
from sierra.core import platform, plugin
from sierra.core.pipeline.pipeline import Pipeline
from sierra.core.generators.controller_generator_parser import ControllerGeneratorParser
import sierra.core.root_dirpath_generator as rdg
import sierra.core.plugin_manager as pm
import sierra.core.logging  # type: ignore
import sierra.core.startup
import sierra.version


class SIERRA():
    """Initialize SIERRA and then launch the pipeline."""

    def __init__(self, bootstrap: cmd.BootstrapCmdline) -> None:
        # Bootstrap the cmdline
        bootstrap_args, other_args = bootstrap.parser.parse_known_args()

        # Setup logging customizations
        sierra.core.logging.initialize(bootstrap_args.log_level)
        self.logger = logging.getLogger(__name__)
        self.logger.info("This is SIERRA %s.", sierra.version.__version__)

        # Check SIERRA runtime environment
        sierra.core.startup.startup_checks(not bootstrap_args.skip_pkg_checks)
        self.logger.info("Using python=%s.", sys.version.replace('\n', ''))

        this_file = pathlib.Path(__file__)
        install_root = pathlib.Path(this_file.parent)

        # Load plugins
        self.logger.info("Loading plugins")
        project = bootstrap_args.project
        plugin_core_path = [install_root / 'plugins' / 'hpc',
                            install_root / 'plugins' / 'storage',
                            install_root / 'plugins' / 'robots',
                            install_root / 'plugins' / 'platform']
        plugin_search_path = plugin_core_path
        env = os.environ.get('SIERRA_PLUGIN_PATH')
        if env is not None:
            for p in env.split(os.pathsep):
                plugin_search_path.append(pathlib.Path(p))

        manager = pm.pipeline
        manager.initialize(project, plugin_search_path)

        for p in manager.available_plugins():
            manager.load_plugin(p)

        # Verify platform plugin
        module = manager.get_plugin_module(bootstrap_args.platform)
        plugin.platform_sanity_checks(module)

        # Verify execution environment plugin
        module = manager.get_plugin_module(bootstrap_args.exec_env)
        plugin.exec_env_sanity_checks(module)

        # Load platform cmdline extensions
        platform_parser = platform.CmdlineParserGenerator(
            bootstrap_args.platform)()

        # Load project cmdline extensions
        self.logger.info("Loading cmdline extensions from project '%s'",
                         project)
        path = f"{project}.cmdline"
        module = pm.module_load(path)

        # Validate cmdline args
        self.args = module.Cmdline([bootstrap.parser, platform_parser],
                                   [-1, 1, 2, 3, 4, 5]).parser.parse_args(other_args)
        module.CmdlineValidator()(self.args)

        # Verify storage plugin (declared as part of core cmdline arguments
        # rather than bootstrap, so we have to wait until after all arguments
        # are parsed to verify it)
        module = manager.get_plugin_module(self.args.storage_medium)
        plugin.storage_sanity_checks(module)

        # Configure cmdopts for platform + execution environment by modifying
        # arguments/adding new arguments as needed.
        configurer = platform.ParsedCmdlineConfigurer(bootstrap_args.platform,
                                                      bootstrap_args.exec_env)
        self.args = configurer(self.args)
        self.args.__dict__['project'] = project

    def __call__(self) -> None:
        # If only 1 pipeline stage is passed, then the list of stages to run is
        # parsed as a non-iterable integer, which can cause the generator to
        # fail to be created. So make it iterable in that case as well.
        if not isinstance(self.args.pipeline, Iterable):
            self.args.pipeline = [self.args.pipeline]

        if 5 not in self.args.pipeline:
            controller = ControllerGeneratorParser()(self.args)
            sgp = pm.module_load_tiered(project=self.args.project,
                                        path='generators.scenario_generator_parser')
            scenario = sgp.ScenarioGeneratorParser().to_scenario_name(self.args)

            self.logger.info("Controller=%s, Scenario=%s", controller, scenario)
            cmdopts = rdg.from_cmdline(self.args)
            pipeline = Pipeline(self.args, controller, cmdopts)
        else:
            pipeline = Pipeline(self.args, None, {})

        try:
            pipeline.run()
        except KeyboardInterrupt:
            self.logger.info("Exiting on user cancel")
            sys.exit()


def main():
    # Necessary on OSX, because python > 3.8 defaults to "spawn" which does not
    # copy loaded modules, which results in the singleton plugin managers not
    # working.
    mp.set_start_method("fork")

    # Bootstrap the cmdline to print version if needed
    bootstrap = cmd.BootstrapCmdline()
    bootstrap_args, _ = bootstrap.parser.parse_known_args()

    if bootstrap_args.version:
        sys.stdout.write(cmd.kVersionMsg)
    else:
        app = SIERRA(bootstrap)
        app()


if __name__ == "__main__":
    main()
