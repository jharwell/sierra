# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""Main module/entry point for SIERRA."""

# Core packages
import logging
import sys
from collections.abc import Iterable
import os
import multiprocessing as mp
import pathlib
import argparse
import typing as tp

# 3rd party packages

# Project packages
import sierra.core.cmdline as cmd
from sierra import version
from sierra.core import platform, plugin, startup, batchroot, exec_env, utils
from sierra.core.pipeline.pipeline import Pipeline
import sierra.core.plugin_manager as pm
import sierra.core.logging  # type: ignore

kIssuesURL = "https://github.com/jharwell/sierra/issues"


class SIERRA:
    """Initialize SIERRA and then launch the pipeline."""

    def __init__(self, bootstrap: cmd.BootstrapCmdline) -> None:
        bootstrap_args, other_args = self._bootstrap(bootstrap)
        manager = self._load_plugins(bootstrap_args)
        self._load_cmdline(bootstrap_args, other_args)
        self._verify_plugins(manager, bootstrap_args)

    def __call__(self) -> None:
        # If only 1 pipeline stage is passed, then the list of stages to run is
        # parsed as a non-iterable integer, which can cause the generator to
        # fail to be created. So make it iterable in that case as well.
        if not isinstance(self.args.pipeline, Iterable):
            self.args.pipeline = [self.args.pipeline]

        if 5 not in self.args.pipeline:
            self.logger.info(
                "Controller=%s, Scenario=%s", self.args.controller, self.args.scenario
            )
            pathset = batchroot.from_cmdline(self.args)

            pipeline = Pipeline(self.args, self.args.controller, pathset)
        else:
            pipeline = Pipeline(self.args, None)

        try:
            pipeline.run()
        except KeyboardInterrupt:
            self.logger.info("Exiting on user cancel")
            sys.exit()

    def _bootstrap(
        self, bootstrap: cmd.BootstrapCmdline
    ) -> tp.Tuple[argparse.Namespace, tp.List[str]]:
        # Bootstrap the cmdline
        bootstrap_args, other_args = bootstrap.parser.parse_known_args()

        if bootstrap_args.rcfile:
            bootstrap_args.rcfile = os.path.expanduser(bootstrap_args.rcfile)

        # Setup logging customizations
        sierra.core.logging.initialize(bootstrap_args.log_level)
        self.logger = logging.getLogger(__name__)
        self.logger.info("This is SIERRA %s.", version.__version__)

        bootstrap_args = self._handle_rc(bootstrap_args.rcfile, bootstrap_args)

        # Check SIERRA runtime environment
        startup.startup_checks(not bootstrap_args.skip_pkg_checks)
        self.logger.info("Using python=%s.", sys.version.replace("\n", ""))

        return bootstrap_args, other_args

    def _load_cmdline(
        self, bootstrap_args: argparse.Namespace, other_args: tp.List[str]
    ) -> None:
        # Load additional project cmdline extensions
        self.logger.info(
            "Loading cmdline extensions from project '%s'", bootstrap_args.project
        )
        path = f"{bootstrap_args.project}.cmdline"
        module = pm.module_load(path)

        # Load core cmdline+platform extensions
        platform_parser = platform.cmdline_parser(bootstrap_args.platform)

        # Parse all cmdline args and validate. This is done BEFORE post-hoc
        # configuration, because you shouldn't have to configure things post-hoc
        # in order for them to be valid.
        parents = [platform_parser] if platform_parser else []
        nonbootstrap_cmdline = module.Cmdline(parents, [-1, 1, 2, 3, 4, 5])

        self.args = nonbootstrap_cmdline.parser.parse_args(other_args)
        self.args.sierra_root = os.path.expanduser(self.args.sierra_root)

        self.args = self._handle_rc(bootstrap_args.rcfile, self.args)

        nonbootstrap_cmdline.validate(self.args)

        # Configure cmdopts for platform + execution environment by modifying
        # arguments/adding new arguments as needed, and perform additional
        # validation.
        self.args = exec_env.cmdline_postparse_configure(
            bootstrap_args.exec_env, self.args
        )
        self.args = platform.cmdline_postparse_configure(
            bootstrap_args.platform, bootstrap_args.exec_env, self.args
        )

        self.args.__dict__["project"] = bootstrap_args.project

    def _load_plugins(self, bootstrap_args: argparse.Namespace):
        this_file = pathlib.Path(__file__)
        install_root = pathlib.Path(this_file.parent)

        # Load plugins
        self.logger.info("Loading plugins")
        plugin_search_path = [install_root / "plugins"]
        if env := os.environ.get("SIERRA_PLUGIN_PATH"):
            for p in env.split(os.pathsep):
                plugin_search_path.append(pathlib.Path(p))

        manager = pm.pipeline
        manager.initialize(bootstrap_args.project, plugin_search_path)

        for p in manager.available_plugins():
            manager.load_plugin(p)

        return manager

    def _verify_plugins(self, manager, bootstrap_args: argparse.Namespace) -> None:
        # Verify platform plugin
        module = manager.get_plugin_module(bootstrap_args.platform)
        plugin.platform_sanity_checks(bootstrap_args.platform, module)

        # Verify execution environment plugin
        module = manager.get_plugin_module(bootstrap_args.exec_env)
        plugin.exec_env_sanity_checks(bootstrap_args.exec_env, module)

        # Verify storage plugin (declared as part of core cmdline arguments
        # rather than bootstrap, so we have to wait until after all arguments
        # are parsed to verify it)
        module = manager.get_plugin_module(self.args.storage)
        plugin.storage_sanity_checks(self.args.storage, module)

    def _handle_rc(
        self, rcfile_path: tp.Optional[str], args: argparse.Namespace
    ) -> argparse.Namespace:
        """
        Populate cmdline arguments from a .sierrarc file.

        In order of priority:

        #. ``--rcfile``

        #. ``SIERRA_RCFILE``

        #. ``~/.sierrarc``


        Anything passed on the cmdline overrides, if both are present.

        """
        # Check rcfile envvar first, so that you can override it on cmdline if
        # desired.
        realpath = os.getenv("SIERRA_RCFILE", None)

        if realpath:
            self.logger.debug("Reading rcfile from envvar")

        if rcfile_path:
            self.logger.debug("Reading rcfile from cmdline")
            realpath = rcfile_path

        if not realpath and os.path.exists(os.path.expanduser("~/.sierrarc")):
            self.logger.debug("Reading rcfile from ~/.sierrarc")
            realpath = "~/.sierrarc"

        if not realpath:
            return args

        path = pathlib.Path(realpath).expanduser()

        with utils.utf8open(path, "r") as rcfile:
            for line in rcfile.readlines():
                # There are 3 ways to pass arguments in the rcfile:
                #
                # 1. --arg
                # 2. --arg=foo
                # 3. --arg foo
                #
                # If you encounter a ~, we assume its a path, so we expand it to
                # match cmdline behavior.
                line = line.strip("\n")
                components = line.split()

                if len(components) == 1 and "=" not in components[0]:  # boolean
                    key = line[2:].replace("-", "_")
                    args.__dict__[key] = True

                elif len(components) == 1 and "=" in components[0]:
                    key = line.split("=")[0][2:].replace("-", "_")
                    value = os.path.expanduser(line.split("=")[1])

                    args.__dict__[key] = value
                else:
                    key = line.split()[0][2:].replace("-", "_")
                    value = os.path.expanduser(line.split()[1])
                    args.__dict__[key] = value

                self.logger.trace(
                    "Applied cmdline arg from rcfile='%s': %s", path, line
                )

        return args


def excepthook(exc_type, exc_value, exc_traceback):
    logging.fatal(
        (
            "SIERRA has encountered an unexpected error and will now "
            "terminate.\n\n"
            "If you think this is a bug, please report it at:\n\n%s\n\n"
            "When reporting, please include as much information as you "
            "can. Ideally:\n\n"
            "1. What you were trying to do in SIERRA.\n"
            "2. The terminal output of sierra-cli, including the "
            "below traceback.\n"
            "3. The exact command you used to run SIERRA.\n"
            "\n"
            "In some cases, creating a Minimum Working Example (MWE) "
            "reproducing the error with specific input files and/or "
            "data is also helpful for quick triage and fix.\n"
        ),
        kIssuesURL,
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def main():
    # Necessary on OSX, because python > 3.8 defaults to "spawn" which does not
    # copy loaded modules, which results in the singleton plugin managers not
    # working.
    mp.set_start_method("fork")

    # Nice traceback on unexpected errors
    sys.excepthook = excepthook

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
