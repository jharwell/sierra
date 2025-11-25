# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""SIERRA plugin management to make SIERRA OPEN/CLOSED.

Also contains checks that selected plugins implement the necessary classes and
functions.  Currently checkes: ``--storage``, ``--execenv``, and ``--engine``.
"""

# Core packages
# Core packages
import importlib.util
import importlib
import typing as tp
import sys
import logging
import pathlib
import inspect

# 3rd party packages

# 3rd party packages
import json

# Project packages
from sierra.core import types


class BasePluginManager:
    """Base class for common functionality."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.loaded = {}  # type: tp.Dict[str, tp.Dict]

    def available_plugins(self):
        raise NotImplementedError

    def loaded_plugins(self):
        return self.loaded

    def load_plugin(self, name: str) -> None:
        """Load a plugin module."""
        plugins = self.available_plugins()
        if name not in plugins:
            self.logger.fatal("Cannot locate plugin %s", name)
            self.logger.fatal(
                "Loaded plugins: %s\n",
                json.dumps(self.loaded, default=lambda x: "<ModuleSpec>", indent=4),
            )
            raise RuntimeError(f"Cannot locate plugin '{name}'")

        init = importlib.util.module_from_spec(plugins[name]["init_spec"])
        plugins[name]["init_spec"].loader.exec_module(init)

        if not hasattr(init, "sierra_plugin_type"):
            self.logger.warning(
                "Cannot load plugin %s: __init__.py does not define sierra_plugin_type()",
                name,
            )
            return

        plugin_type = init.sierra_plugin_type()

        # The name of the module is only needed for pipeline plugins, not
        # project plugins.
        if plugins[name]["module_spec"] is None and plugin_type == "pipeline":
            if not hasattr(init, "sierra_plugin_module"):
                self.logger.warning(
                    "Cannot load plugin %s: __init__.py does not define sierra_plugin_module()",
                    name,
                )
                return

            modname = init.sierra_plugin_module()
            fpath = (
                plugins[name]["parent_dir"] / name.replace(".", "/") / f"{modname}.py"
            )
            plugins[name]["module_spec"] = importlib.util.spec_from_file_location(
                modname, fpath
            )

        if plugin_type == "pipeline":
            self._load_pipeline_plugin(name)

        elif plugin_type == "project":
            self._load_project_plugin(name)
        elif plugin_type == "model":
            if not hasattr(init, "sierra_models"):
                self.logger.warning(
                    "Cannot load plugin %s: __init__.py does not define sierra_models()",
                    name,
                )
                return

            self._load_model_plugin(name)
        else:
            self.logger.warning(
                "Unknown plugin type '%s' for %s: cannot load", plugin_type, name
            )

    def get_plugin(self, name: str) -> dict:
        try:
            return self.loaded[name]
        except KeyError:
            self.logger.fatal("No such plugin %s", name)
            self.logger.fatal(
                "Loaded plugins: %s\n",
                json.dumps(self.loaded, default=lambda x: "<ModuleSpec>", indent=4),
            )
            raise

    def get_plugin_module(self, name: str) -> types.ModuleType:
        try:
            return self.loaded[name]["module"]
        except KeyError:
            self.logger.fatal("No such plugin %s", name)
            self.logger.fatal(
                "Loaded plugins: %s\n",
                json.dumps(self.loaded, default=lambda x: "<ModuleSpec>", indent=4),
            )
            raise

    def has_plugin(self, name: str) -> bool:
        return name in self.loaded

    def _load_pipeline_plugin(self, name: str) -> None:
        if name in self.loaded:
            self.logger.warning("Pipeline plugin %s already loaded", name)
            return

        plugins = self.available_plugins()

        # The parent directory of the plugin must be on sys.path so it can be
        # imported, so we put in on there if it isn't.
        new = str(plugins[name]["parent_dir"])
        if new not in sys.path:
            sys.path = [new, *sys.path[0:]]
            self.logger.debug("Updated sys.path with %s", [new])

        module = importlib.util.module_from_spec(plugins[name]["module_spec"])
        plugins[name]["module_spec"].loader.exec_module(module)

        # When importing with importlib, the module is not automatically added
        # to sys.modules. This means that trying to pickle anything in it will
        # fail with a rather cryptic 'AttributeError', so we explicitly add the
        # last path component of the plugin name--which is the actual name of
        # the module the plugin lives in--to sys.modules so that pickling will
        # work.
        sys_modname = name.split(".")[1]
        if sys_modname not in sys.modules:
            sys.modules[sys_modname] = module

        self.loaded[name] = {
            "spec": plugins[name]["module_spec"],
            "parent_dir": plugins[name]["parent_dir"],
            "module": module,
            "type": "pipeline",
        }
        self.logger.debug(
            "Loaded pipeline plugin %s from %s -> %s",
            name,
            plugins[name]["parent_dir"],
            name,
        )

    def _load_project_plugin(self, name: str) -> None:
        if name in self.loaded:
            self.logger.warning("Project plugin %s already loaded", name)
            return

        plugins = self.available_plugins()

        # The parent directory of the plugin must be on sys.path so it can be
        # imported, so we put in on there if it isn't.
        new = str(plugins[name]["parent_dir"])
        if new not in sys.path:
            sys.path = [new, *sys.path[0:]]
            self.logger.debug("Updated sys.path with %s", [new])

        self.loaded[name] = {
            "spec": plugins[name]["module_spec"],
            "parent_dir": plugins[name]["parent_dir"],
            "type": "project",
        }

        self.logger.debug(
            ("Loaded project plugin %s from %s -> %s"),
            name,
            plugins[name]["parent_dir"],
            name,
        )

    def _load_model_plugin(self, name: str) -> None:
        if name in self.loaded:
            self.logger.warning("Model plugin %s already loaded", name)
            return

        plugins = self.available_plugins()

        # The parent directory of the plugin must be on sys.path so it can be
        # imported, so we put in on there if it isn't.
        new = str(plugins[name]["parent_dir"])
        if new not in sys.path:
            sys.path = [new, *sys.path[0:]]
            self.logger.debug("Updated sys.path with %s", [new])

        self.loaded[name] = {
            "spec": plugins[name]["module_spec"],
            "parent_dir": plugins[name]["parent_dir"],
            "type": "model",
        }

        self.logger.debug(
            ("Loaded model plugin %s from %s -> %s"),
            name,
            plugins[name]["parent_dir"],
            name,
        )


class DirectoryPluginManager(BasePluginManager):
    """Container for managing directory-based plugins."""

    def __init__(self) -> None:
        super().__init__()
        self.plugins = {}  # type: tp.Dict[str, tp.Dict]

    def initialize(self, project: str, search_path: list[pathlib.Path]) -> None:
        self.logger.debug(
            "Initializing with plugin search path %s", [str(p) for p in search_path]
        )

        for path in search_path:
            if not path.exists():
                self.logger.warning(
                    "Non-existent path '%s' on SIERRA_PLUGIN_PATH", path
                )
                continue

            self.logger.debug("Searching for plugins in '%s'", path)

            def recursive_search(root: pathlib.Path) -> None:
                for f in root.iterdir():
                    if not f.is_dir():
                        continue
                    recursive_search(f)

                    plugin = f / "plugin.py"
                    init = f / "__init__.py"
                    cookie = f / ".sierraplugin"

                    # 2025-11-24 [JRH]: The cookie is ALWAYS required. We used
                    # to just recognize a directory containing
                    # plugin.py+__init__.py as a SIERRA plugin, but that is far
                    # too generic, and caused conflicts with other python
                    # packages installed in the same environment.
                    if not (cookie.exists() and (plugin.exists() or init.exists())):
                        continue

                    name = f"{f.parent.name}.{f.name}"

                    try:
                        if plugin.exists():
                            module_spec = importlib.util.spec_from_file_location(
                                f.name, plugin
                            )
                        else:
                            module_spec = None

                        init_spec = importlib.util.spec_from_file_location(
                            "__init__", init
                        )
                    except FileNotFoundError:
                        self.logger.warning(
                            "Malformed plugin in %s: not loading", f.relative_to(root)
                        )

                    self.logger.debug("Found plugin in '%s' -> %s", f, name)

                    self.plugins[name] = {
                        "parent_dir": root.parent,
                        "module_spec": module_spec,
                        "init_spec": init_spec,
                    }

            recursive_search(path)

    def available_plugins(self):
        return self.plugins


def module_exists(name: str) -> bool:
    """
    Check if a module exists before trying to import it.
    """
    try:
        _ = __import__(name)
    except ImportError:
        return False

    return True


def module_load(name: str) -> types.ModuleType:
    """
    Import the specified module.
    """
    return __import__(name, fromlist=["*"])


def bc_load(cmdopts: types.Cmdopts, category: str):
    """
    Load the specified :term:`Batch Criteria`.
    """
    path = f"variables.{category}"
    return module_load_tiered(
        project=cmdopts["project"], engine=cmdopts["engine"], path=path
    )


def module_load_tiered(
    path: str, project: tp.Optional[str] = None, engine: tp.Optional[str] = None
) -> types.ModuleType:
    """Attempt to load the specified python module with tiered precedence.

    Generally, the precedence is project -> project submodule -> engine module
    -> SIERRA core module, to allow users to override SIERRA core functionality
    with ease.  Specifically:

        #. Check if the requested module directly exists.  If it does, return
           it.

        #. Check if the requested module is a part of a project (i.e.,
           ``<project>.<path>`` exists).  If it does, return it.  This requires
           that :envvar:`SIERRA_PLUGIN_PATH` to be set properly.

        #. Check if the requested module is provided by the engine plugin (i.e.,
           ``sierra.engine.<engine>.<path>`` exists).  If it does, return it.

        #. Check if the requested module is part of the SIERRA core (i.e.,
           ``sierra.core.<path>`` exists).  If it does, return it.

    If no match was found using any of these, throw an error.
    """
    # First, see if the requested module is a project/directly exists as
    # specified.
    if module_exists(path):
        logging.trace("Using direct path %s", path)
        return module_load(path)

    # Next, check if the requested module is part of the project plugin
    if project is not None:
        component_path = f"{project}.{path}"
        if module_exists(component_path):
            logging.trace("Using project component path %s", component_path)
            return module_load(component_path)

        logging.trace(
            "Project component path %s does not exist",
            component_path,
        )

    # If that didn't work, check the engine plugin
    if engine is not None:
        engine_path = f"{engine}.{path}"
        if module_exists(engine_path):
            logging.trace("Using engine component path %s", engine_path)
            return module_load(engine_path)

    # If that didn't work, then check the SIERRA core
    core_path = f"sierra.core.{path}"
    if module_exists(core_path):
        logging.trace("Using SIERRA core path %s", core_path)
        return module_load(core_path)

    logging.trace("SIERRA core path %s does not exist", core_path)

    # Module does not exist
    error = (
        f"project: '{project}' "
        f"engine: '{engine}' "
        f"path: '{path}' "
        f"sys.path: {sys.path}"
    )
    raise ImportError(error)


def storage_sanity_checks(medium: str, module) -> None:
    """
    Check the selected ``--storage`` plugin.
    """
    logging.trace("Verifying --storage=%s plugin interface", medium)

    functions = ["supports_input", "supports_output"]
    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in functions:
        assert any(
            f == name for (name, _) in in_module
        ), f"Storage medium {medium} does not define {f}()"


def expdef_sanity_checks(expdef: str, module) -> None:
    """
    Check the selected ``--expdef`` plugin.
    """
    logging.trace("Verifying --expdef=%s plugin interface", expdef)

    functions = ["root_querypath", "unpickle"]
    module_funcs = inspect.getmembers(module, inspect.isfunction)
    module_classes = inspect.getmembers(module, inspect.isclass)
    classes = ["ExpDef", "Writer"]

    for c in classes:
        assert any(
            c == name for (name, _) in module_classes
        ), f"Expdef plugin {expdef} does not define {c}"

    for f in functions:
        assert any(
            f == name for (name, _) in module_funcs
        ), f"Expdef  {expdef} does not define {f}()"


def proc_sanity_checks(proc: str, module) -> None:
    """
    Check the selected ``--proc`` plugins.
    """
    logging.trace("Verifying --proc=%s plugin interface", proc)

    functions = ["proc_batch_exp"]
    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in functions:
        assert any(
            f == name for (name, _) in in_module
        ), f"Processing plugin  {proc} does not define {f}()"


def prod_sanity_checks(prod: str, module) -> None:
    """
    Check the selected ``--prod`` plugins.
    """
    logging.trace("Verifying --prod=%s plugin interface", prod)

    functions = ["proc_batch_exp"]
    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in functions:
        assert any(
            f == name for (name, _) in in_module
        ), f"Product plugin  {prod} does not define {f}()"


def compare_sanity_checks(compare: str, module) -> None:
    """
    Check the selected ``--compare`` plugins.
    """
    logging.trace("Verifying --compare=%s plugin interface", compare)

    functions = ["proc_exps"]
    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in functions:
        assert any(
            f == name for (name, _) in in_module
        ), f"Comparison plugin  {compare} does not define {f}()"


def execenv_sanity_checks(execenv: str, module) -> None:
    """
    Check the selected ``--execenv`` plugin.
    """
    logging.trace("Verifying --execenv=%s plugin interface", execenv)

    in_module = inspect.getmembers(module, inspect.isclass)

    opt_functions = ["cmdline_postparse_configure", "execenv_check"]
    opt_classes = ["ExpRunShellCmdsGenerator", "ExpShellCmdsGenerator"]

    for c in opt_classes:
        if not any(c == name for (name, _) in in_module):
            logging.debug(
                (
                    "Execution environment plugin %s does not define "
                    "%s--some SIERRA functionality may not be "
                    "available. See docs for details."
                ),
                execenv,
                c,
            )

    for f in opt_functions:
        if not any(f in name for (name, _) in in_module):
            logging.debug(
                ("Execution environment plugin %s does not define %s()."),
                execenv,
                f,
            )


def engine_sanity_checks(engine: str, module) -> None:
    """
    Check the selected ``--engine`` plugin.
    """
    logging.trace("Verifying --engine=%s plugin interface", engine)

    req_classes = [
        "ExpConfigurer",
    ]

    req_functions = []  # type: list[str]

    opt_classes = ["ExpRunShellCmdsGenerator", "ExpShellCmdsGenerator"]

    opt_functions = [
        "cmdline_postparse_configure",
        "execenv_check",
        "agent_prefix_extract",
        "arena_dims_from_criteria",
        "population_size_from_def",
        "population_size_from_pickle",
    ]

    in_module = inspect.getmembers(module, inspect.isclass)

    for c in req_classes:
        assert any(
            c == name for (name, _) in in_module
        ), f"Engine plugin {engine} does not define {c}"

    for f in opt_classes:
        if not any(f in name for (name, _) in in_module):
            logging.debug(
                (
                    "Engine plugin %s does not define %s"
                    "--some SIERRA functionality may not be available. "
                    "See docs for details."
                ),
                engine,
                f,
            )

    in_module = inspect.getmembers(module, inspect.isfunction)

    for f in req_functions:
        assert any(
            f == name for (name, _) in in_module
        ), f"Engine plugin {engine} does not define {f}()"

    for f in opt_functions:
        if not any(f == name for (name, _) in in_module):
            logging.debug(
                (
                    "Engine plugin %s does not define %s()"
                    "--some SIERRA functionality may not be available. "
                    "See docs for details."
                ),
                engine,
                f,
            )


# Singletons
pipeline = DirectoryPluginManager()
models = DirectoryPluginManager()

__all__ = [
    "DirectoryPluginManager",
    "bc_load",
    "compare_sanity_checks",
    "engine_sanity_checks",
    "execenv_sanity_checks",
    "module_exists",
    "module_load",
    "module_load_tiered",
    "proc_sanity_checks",
    "prod_sanity_checks",
    "storage_sanity_checks",
]
