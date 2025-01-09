# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Simple plugin managers to make SIERRA OPEN/CLOSED.

"""
# Core packages
import importlib.util
import importlib
import typing as tp
import sys
import logging
import pathlib

# 3rd party packages
import json

# Project packages
from sierra.core import types, utils


class BasePluginManager():
    """
    Base class for common functionality.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.loaded = {}  # type: tp.Dict[str, tp.Dict]

    def available_plugins(self):
        raise NotImplementedError

    def load_plugin(self, name: str) -> None:
        """Load a plugin module.

        """
        plugins = self.available_plugins()
        if name not in plugins:
            self.logger.fatal("Cannot locate plugin '%s'", name)
            self.logger.fatal('Loaded plugins: %s\n',
                              json.dumps(self.loaded,
                                         default=lambda x: '<ModuleSpec>',
                                         indent=4))
            raise Exception(f"Cannot locate plugin '{name}'")

        if plugins[name]['type'] == 'pipeline':
            parent_scope = pathlib.Path(plugins[name]['parent_dir']).name
            scoped_name = f'{parent_scope}.{name}'

            if name not in self.loaded:
                module = importlib.util.module_from_spec(plugins[name]['spec'])

                plugins[name]['spec'].loader.exec_module(module)
                self.loaded[scoped_name] = {
                    'spec': plugins[name]['spec'],
                    'parent_dir': plugins[name]['parent_dir'],
                    'module': module
                }
                self.logger.debug(("Loaded pipeline plugin '%s' from '%s': "
                                   "accessible as %s"),
                                  scoped_name,
                                  plugins[name]['parent_dir'],
                                  scoped_name)
            else:
                self.logger.warning("Pipeline plugin '%s' already loaded", name)
        elif plugins[name]['type'] == 'project':
            # Projects are addressed directly without scoping. Only one project
            # is loaded at a time, so this should be fine.
            scoped_name = name
            if name not in self.loaded:
                self.loaded[scoped_name] = {
                    'spec': plugins[name]['spec'],
                    'parent_dir': plugins[name]['parent_dir'],
                }
                self.logger.debug(("Loaded project plugin '%s' from '%s' "
                                  "accessible as %s"),
                                  scoped_name,
                                  plugins[name]['parent_dir'],
                                  scoped_name)
            else:
                self.logger.warning("Project plugin '%s' already loaded", name)

    def get_plugin(self, name: str) -> dict:
        try:
            return self.loaded[name]
        except KeyError:
            self.logger.fatal("No such plugin '%s'", name)
            self.logger.fatal('Loaded plugins: %s\n',
                              json.dumps(self.loaded,
                                         default=lambda x: '<ModuleSpec>',
                                         indent=4))
            raise

    def get_plugin_module(self, name: str) -> types.ModuleType:
        try:
            return self.loaded[name]['module']
        except KeyError:
            self.logger.fatal("No such plugin '%s'", name)
            self.logger.fatal('Loaded plugins: %s\n',
                              json.dumps(self.loaded,
                                         default=lambda x: '<ModuleSpec>',
                                         indent=4))
            raise

    def has_plugin(self, name: str) -> bool:
        return name in self.loaded


class FilePluginManager(BasePluginManager):
    """Plugins are ``.py`` files within a root plugin directory.

    Intended for use with :term:`models <Model>`.

    """

    def __init__(self) -> None:
        super().__init__()
        self.search_root = None  # type: tp.Optional[pathlib.Path]
        self.plugins = {}

    def initialize(self, project: str, search_root: pathlib.Path) -> None:
        self.search_root = search_root

    def available_plugins(self) -> tp.Dict[str, tp.Dict]:
        """Get the available plugins in the configured plugin root.

        """
        assert self.search_root is not None, \
            "FilePluginManager not initialized!"

        if self.plugins:
            return self.plugins

        for candidate in self.search_root.iterdir():
            if candidate.is_file() and '.py' in candidate.name:
                name = candidate.stem
                spec = importlib.util.spec_from_file_location(name, candidate)
                self.plugins[name] = {
                    'spec': spec,
                    'parent_dir': self.search_root,
                    'type': 'pipeline'
                }
        return self.plugins


class PipelinePluginManager(BasePluginManager):
    """Plugins are *subdirs* in a directory on :envvar`SIERRA_PLUGIN_PATH`.

    Used with :term:`Pipeline plugins <plugin>`.

    """

    def __init__(self, search_root: pathlib.Path) -> None:
        super().__init__()
        self.search_root = search_root
        self.main_module = 'plugin'
        self.plugins = {}

    def initialize(self, project: str) -> None:
        # Update PYTHONPATH with the directory containing the project so imports
        # of the form 'import project.module' work. This is needed so projects
        # which define e.g., platform plugins work as expected.
        #
        # 2021/07/19: If you put the entries at the end of sys.path it
        # doesn't work for some reason...
        sys.path = [str(self.search_root)] + sys.path[0:]

    def available_plugins(self):
        """
        Find all pipeline plugins in all directories within the search root.
        """
        if self.plugins:
            return self.plugins

        self.logger.debug("Searching for directory-based plugins in '%s'",
                          self.search_root)

        try:
            for location in self.search_root.iterdir():
                plugin = location / (self.main_module + '.py')
                self.logger.trace("Trying directory '%s': has %s: %s",
                                  plugin,
                                  (self.main_module + '.py'),
                                  plugin in location.iterdir() if
                                  location.is_dir() else False)
                if location.is_dir() and plugin in location.iterdir():
                    self.logger.debug("Found directory-based plugin in '%s'",
                                      location)
                    spec = importlib.util.spec_from_file_location(location.name,
                                                                  plugin)
                    self.plugins[location.name] = {
                        'parent_dir': self.search_root,
                        'spec': spec,
                        'type': 'pipeline'
                    }
        except FileNotFoundError:
            pass

        return self.plugins


class ProjectPluginManager(BasePluginManager):
    """Plugins are *directories* found in a root plugin directory.

    Intended for use with :term:`Project plugins <plugin>`.

    """

    def __init__(self, search_root: pathlib.Path, project: str) -> None:
        super().__init__()

        self.search_root = search_root
        self.project = project
        self.plugins = {}

    def initialize(self, project: str) -> None:
        # Update PYTHONPATH with the directory containing the project so imports
        # of the form 'import project.module' work.
        #
        # 2021/07/19: If you put the entries at the end of sys.path it
        # doesn't work for some reason...
        sys.path = [str(self.search_root)] + sys.path[0:]

    def available_plugins(self):
        """
        Find all pipeline plugins in all directories within the search root.
        """
        if self.plugins:
            return self.plugins

        self.logger.debug("Searching for project plugins in '%s'",
                          self.search_root)
        try:
            for location in self.search_root.iterdir():
                if self.project in location.name:
                    self.logger.debug("Found project plugin in '%s'", location)
                    self.plugins[location.name] = {
                        'parent_dir': self.search_root,
                        'spec': None,
                        'type': 'project'
                    }

        except FileNotFoundError:
            pass

        return self.plugins


class CompositePluginManager(BasePluginManager):
    """Container for managing multiple types of plugins via multiple managers."""

    def __init__(self) -> None:
        super().__init__()
        self.components = []  # type: tp.List[tp.Union[DirectoryPluginManager,ProjectPluginManager]]

    def initialize(self,
                   project: str,
                   search_path: tp.List[pathlib.Path]) -> None:
        self.logger.debug("Initializing with plugin search path %s",
                          [str(p) for p in search_path])
        for d in search_path:
            project_path = d / project

            if utils.path_exists(d) and not utils.path_exists(project_path):
                pipeline_plugin = PipelinePluginManager(d)
                self.components.append(pipeline_plugin)
            elif utils.path_exists(project_path):
                project_plugin = ProjectPluginManager(d, project)
                self.components.append(project_plugin)
            else:
                pipeline_plugin = PipelinePluginManager(d)
                self.components.append(pipeline_plugin)

        for c in self.components:
            c.initialize(project)

    def available_plugins(self):
        plugins = {}

        for c in self.components:
            plugins.update(c.available_plugins())

        return plugins


# Singletons
pipeline = CompositePluginManager()
models = FilePluginManager()


def module_exists(name: str) -> bool:
    """
    Check if a module exists before trying to import it.
    """
    try:
        _ = __import__(name)
    except ImportError:
        return False
    else:
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
    path = f'variables.{category}'
    return module_load_tiered(project=cmdopts['project'],
                              platform=cmdopts['platform'],
                              path=path)


def module_load_tiered(path: str,
                       project: tp.Optional[str] = None,
                       platform: tp.Optional[str] = None) -> types.ModuleType:
    """Attempt to load the specified python module with tiered precedence.

    Generally, the precedence is project -> project submodule -> platform module
    -> SIERRA core module, to allow users to override SIERRA core functionality
    with ease. Specifically:

    #. Check if the requested module is a project. If it is, return it.

    #. Check if the requested module is a part of a project (i.e.,
       ``<project>.<path>`` exists). If it does, return it. This requires that
       :envvar:`SIERRA_PLUGIN_PATH` to be set properly.

    #. Check if the requested module is provided by the platform plugin (i.e.,
       ``sierra.platform.<platform>.<path>`` exists). If it does, return it.

    #. Check if the requested module is part of the SIERRA core (i.e.,
       ``sierra.core.<path>`` exists). If it does, return it.

    If no match was found using any of these, throw an error.

    """
    # First, see if the requested module is a project
    if module_exists(path):
        logging.trace("Using project path '%s'", path)  # type: ignore
        return module_load(path)

    # First, see if the requested module is part of the project plugin
    if project is not None:
        component_path = f'{project}.{path}'
        if module_exists(component_path):
            logging.trace("Using project component path '%s'",  # type: ignore
                          component_path)
            return module_load(component_path)
        else:
            logging.trace("Project component path '%s' does not exist",  # type: ignore
                          component_path)

    # If that didn't work, check the platform plugin
    if platform is not None:

        # 2025-01-13 [JRH]: We handle two types of platform plugins:
        #
        # - Those defined in the SIERRA core. sierra/plugins is on PYTHONPATH
        #   since those paths/modules are all known, we don't have to worry
        #   about getting the files from other non-platform plugin with the same
        #   name as a file in the platform plugin picked during import.
        #
        # - Those defined outside the SIERRA core. Since the directory they
        #   reside in can be anywhere on SIERRA_PLUGIN_PATH, AND we can't know
        #   if there is ANOTHER directory on PYTHONPATH containing a file with
        #   the same name as the one we are trying to match with AND we can't
        #   depend on the order of PYTHONPATH, we have to get creative to avoid
        #   picking up a false positive match. Specifically, we try each of the
        #   sub-paths of the path we are trying to lookup to see if we get a hit
        #   relative to a directory which IS on PYTHONPATH.
        #
        #   The case where the user puts platform plugins on SIERRA_PLUGIN_PATH
        #   as e.g., ~/plugins/myplugin, and then uses --platform=myplugin is a
        #   special case of the above.
        #
        #   This approach is a bit hacky, but I don't know of a better way to do
        #   it.

        platform_path = f'{platform}.{path}'
        substr = platform_path

        while '.' in substr:
            if module_exists(substr):
                logging.trace(("Using platform component path '%s' with matched "
                               "PYTHONPATH fragment '%s'"),
                              platform_path,
                              substr)  # type: ignore
                return module_load(substr)
            else:
                logging.trace(("Platform component path '%s' does not exist with "
                               "matched component fragment '%s'"),
                              platform_path,
                              substr)   # type: ignore

            substr = '.'.join(substr.split('.')[1:])

    # If that didn't work, then check the SIERRA core
    core_path = f'sierra.core.{path}'
    if module_exists(core_path):
        logging.trace("Using SIERRA core path '%s'",  # type: ignore
                      core_path)
        return module_load(core_path)
    else:
        logging.trace("SIERRA core path '%s' does not exist",  # type: ignore
                      core_path)

    # Module does not exist
    error = (f"project: '{project}' "
             f"platform: '{platform}' "
             f"path: '{path}' "
             f"sys.path: {sys.path}")
    raise ImportError(error)


__api__ = [
    'BasePluginManager',
    'FilePluginManager',
    'DirectoryPluginManager',
    'ProjectPluginManager',
    'CompositePluginManager',
    'module_exists',
    'module_load',
    'bc_load',
    'module_load_tiered'
]
