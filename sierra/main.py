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
import sierra.core.cmdline as corecmd
from sierra import version
from sierra.core import engine, startup, batchroot, execenv, utils
from sierra.core.pipeline.pipeline import Pipeline
import sierra.core.plugin as pm
import sierra.core.logging
from sierra.core import expdef, prod, proc, storage, compare

ISSUES_URL = "https://github.com/jharwell/sierra/issues"


class SIERRA:
    """Initialize SIERRA and then launch the pipeline."""

    def __init__(self, bootstrap: corecmd.BootstrapCmdline) -> None:
        bootstrap_args, other_args = self._bootstrap(bootstrap)
        manager = self._load_plugins(bootstrap_args)
        self._verify_plugins(manager, bootstrap_args)
        self.args = self._load_cmdline(bootstrap_args, other_args)

        # Configure cmdopts for engine + execution environment by modifying
        # arguments/adding new arguments as needed, and perform additional
        # validation.
        self.args = execenv.cmdline_postparse_configure(
            bootstrap_args.execenv, self.args
        )
        self.args = engine.cmdline_postparse_configure(
            bootstrap_args.engine, bootstrap_args.execenv, self.args
        )

        # Inject bootstrap arguments into the namespace for non-bootstrap
        # arguments to make setting up the pipeline downstream much more
        # uniform.
        self.args.__dict__["project"] = bootstrap_args.project
        self.args.__dict__["engine"] = bootstrap_args.engine
        self.args.__dict__["execenv"] = bootstrap_args.execenv
        self.args.__dict__["expdef"] = bootstrap_args.expdef
        self.args.__dict__["storage"] = bootstrap_args.storage
        self.args.__dict__["proc"] = bootstrap_args.proc
        self.args.__dict__["prod"] = bootstrap_args.prod
        self.args.__dict__["compare"] = bootstrap_args.compare

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
        self, bootstrap: corecmd.BootstrapCmdline
    ) -> tuple[argparse.Namespace, list[str]]:
        # Bootstrap the cmdline
        bootstrap_args, other_args = bootstrap.parser.parse_known_args()
        if bootstrap_args.rcfile:
            bootstrap_args.rcfile = pathlib.Path(bootstrap_args.rcfile).expanduser()

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
        self, bootstrap_args: argparse.Namespace, other_args: list[str]
    ) -> argparse.Namespace:
        """Build the cmdline from the selected plugins and parse args.

        This is one of the places where the SIERRA magic happens. This function
        dynamically combines declared cmdlines from each active plugin, in the
        following partial dependency order::

               --project -> {--expdef, --proc, --prod, --compare, --storage} -> --execenv --> --engine

        Plugins in the {} could *probably* be reordered without breaking things,
        but the other plugins (--project, --execenv, --engine) need to be where
        they are in the chain. Change the order at your own risk!
        """

        self.logger.info("Dynamically building cmdline from selected plugins")
        parents = [corecmd.CoreCmdline([], [-1, 1, 2, 3, 4, 5]).parser]
        stages = [-1, 1, 2, 3, 4, 5]

        # For plugin options which don't take lists, we can just iterate over
        # them with some simple conf and build their portions of the cmdline.
        simple = {
            "engine": {"arg": "--engine", "module": engine},
            "execenv": {"arg": "--execenv", "module": execenv},
            "expdef": {"arg": "--expdef", "module": expdef},
            "storage": {"arg": "--storage", "module": storage},
        }
        for name, conf in simple.items():
            if parser := conf["module"].cmdline_parser(
                bootstrap_args.__dict__[name], parents, stages
            ):
                self.logger.debug(
                    "Loaded %s=%s cmdline", conf["arg"], bootstrap_args.__dict__[name]
                )
                parents = [parser]

        # These plugin options take lists of plugins to use, and so take
        # slightly more complicated processing.
        lists = {
            "proc": {"arg": "--proc", "module": proc},
            "prod": {"arg": "--prod", "module": prod},
            "compare": {"arg": "--compare", "module": compare},
        }
        for name, conf in lists.items():
            for to_load in bootstrap_args.__dict__[name]:
                if parser := conf["module"].cmdline_parser(to_load, parents, stages):
                    self.logger.debug("Loaded %s=%s cmdline", conf["arg"], to_load)
                    parents = [parser]

        path = f"{bootstrap_args.project}.cmdline"
        module = pm.module_load(path)

        nonbootstrap_cmdline = module.build(parents, stages)
        args = nonbootstrap_cmdline.parser.parse_args(other_args)
        args.sierra_root = pathlib.Path(args.sierra_root).expanduser()

        # Make sure cmdline args override rcfile args
        return self._handle_rc(bootstrap_args.rcfile, args)

    def _load_plugins(self, bootstrap_args: argparse.Namespace):
        this_file = pathlib.Path(__file__)
        install_root = pathlib.Path(this_file.parent)

        # Load plugins
        self.logger.info("Loading plugins")
        plugin_search_path = [install_root / "plugins"]
        if env := os.environ.get("SIERRA_PLUGIN_PATH"):
            plugin_search_path.extend([pathlib.Path(p) for p in env.split(os.pathsep)])

        manager = pm.pipeline
        manager.initialize(bootstrap_args.project, plugin_search_path)

        # 2025-06-14 [JRH]: All found plugins are loaded/executed as python
        # modules, even if they are not currently selected. I don't know if this
        # is a good idea or not.
        for p in manager.available_plugins():
            manager.load_plugin(p)

        return manager

    def _verify_plugins(
        self,
        manager,
        bootstrap_args: argparse.Namespace,
    ) -> None:
        # Verify engine plugin
        module = manager.get_plugin_module(bootstrap_args.engine)
        pm.engine_sanity_checks(bootstrap_args.engine, module)

        # Verify execution environment plugin
        module = manager.get_plugin_module(bootstrap_args.execenv)
        pm.execenv_sanity_checks(bootstrap_args.execenv, module)

        # Verify processing plugins
        for p in bootstrap_args.proc:
            module = manager.get_plugin_module(p)
            pm.proc_sanity_checks(p, module)

        # Verify product plugins
        for p in bootstrap_args.prod:
            module = manager.get_plugin_module(p)
            pm.prod_sanity_checks(p, module)

        # Verify comparison plugins
        for p in bootstrap_args.compare:
            module = manager.get_plugin_module(p)
            pm.compare_sanity_checks(p, module)

        # Verify expdef plugin
        module = manager.get_plugin_module(bootstrap_args.expdef)
        pm.expdef_sanity_checks(bootstrap_args.expdef, module)

        # Verify storage plugin
        module = manager.get_plugin_module(bootstrap_args.storage)
        pm.storage_sanity_checks(bootstrap_args.storage, module)

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
            self.logger.debug("Reading rcfile from SIERRA_RCFILE")

        if rcfile_path:
            self.logger.debug("Reading rcfile from --rcfile")
            realpath = rcfile_path

        if not realpath and pathlib.Path("~/.sierrarc").expanduser().exists():
            self.logger.debug("Reading rcfile from ~/.sierrarc")
            realpath = "~/.sierrarc"

        if not realpath:
            return args

        path = pathlib.Path(realpath).expanduser()
        with utils.utf8open(path, "r") as rcfile:
            for line in rcfile.readlines():
                if self._rcfile_line_proc(line, args):
                    self.logger.trace(
                        "Applied cmdline arg from rcfile='%s': %s",
                        path,
                        line.strip("\n"),
                    )

        return args

    def _rcfile_line_proc(self, line: str, args: argparse.Namespace) -> bool:
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
            if line in sys.argv:  # Passed on cmdline
                self.logger.trace("Skip bool rcfile arg %s: passed on cmdline", line)
                return False

            key = line[2:].replace("-", "_")
            args.__dict__[key] = True

        elif len(components) == 1 and "=" in components[0]:
            # The == here instead of 'in' is important! Otherwise a
            # --expdef-template the cmdline will cause a --expdef in the
            # rcfile not to work.
            if any(line.split("=")[0] == a.split("=")[0] for a in sys.argv if "=" in a):
                self.logger.trace("Skip =rcfile arg %s: passed on cmdline", line)
                return False

            key = line.split("=")[0][2:].replace("-", "_")
            if "~" in line:
                value = pathlib.Path(line.split("=")[1]).expanduser()
            else:
                value = line.split("=")[1]

            args.__dict__[key] = value
        else:
            # The == here instead of 'in' is important! Otherwise a
            # --project-rendering on the cmdline will cause a --project in the
            # rcfile not to work.
            if any(line.split()[0] == a for a in sys.argv):
                self.logger.trace("Skip rcfile2 arg %s: passed on cmdline", line)
                return False
            key = line.split()[0][2:].replace("-", "_")
            if "~" in line:
                value = str(pathlib.Path(line.split()[1]).expanduser())
            else:

                # If true, this is an arg which takes a list/has
                # multiple values, so it should be put into the argparse
                # namespace as a list, to match cmdline behavior.
                value = line.split()[1:] if len(line.split()) > 2 else line.split()[1]

            args.__dict__[key] = value

        return True


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
        ISSUES_URL,
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
    bootstrap = corecmd.BootstrapCmdline()
    bootstrap_args, _ = bootstrap.parser.parse_known_args()

    if bootstrap_args.version:
        sys.stdout.write(corecmd.VERSION_MSG)
    else:
        app = SIERRA(bootstrap)
        app()


if __name__ == "__main__":
    main()
