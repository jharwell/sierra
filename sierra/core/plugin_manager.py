# Copyright 2020 John Harwell, All rights reserved.
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
"""Simple plugin managers to make SIERRA OPEN/CLOSED.

"""
# Core packages
import importlib.util
import importlib
import os
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
                self.logger.debug("Loaded pipeline plugin '%s' from '%s'",
                                  scoped_name,
                                  plugins[name]['parent_dir'])
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
                self.logger.debug("Loaded project plugin '%s' from '%s'",
                                  scoped_name,
                                  plugins[name]['parent_dir'])
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

    def initialize(self, project: str, search_root: pathlib.Path) -> None:
        self.search_root = search_root

    def available_plugins(self) -> tp.Dict[str, tp.Dict]:
        """Get the available plugins in the configured plugin root.

        """
        plugins = {}
        assert self.search_root is not None, \
            "FilePluginManager not initialized!"

        for candidate in self.search_root.iterdir():
            if candidate.is_file() and '.py' in candidate.name:
                name = candidate.stem
                spec = importlib.util.spec_from_file_location(name, candidate)
                plugins[name] = {
                    'spec': spec,
                    'parent_dir': self.search_root,
                    'type': 'pipeline'
                }
        return plugins


class DirectoryPluginManager(BasePluginManager):
    """Plugins are `directories` found in a root plugin directory.

    Intended for use with :term:`Pipeline plugins <plugin>`.

    """

    def __init__(self, search_root: pathlib.Path) -> None:
        super().__init__()
        self.search_root = search_root
        self.main_module = 'plugin'

    def initialize(self, project: str) -> None:
        pass

    def available_plugins(self):
        """
        Find all pipeline plugins in all directories within the search root.
        """
        plugins = {}
        try:
            for location in self.search_root.iterdir():
                plugin = location / (self.main_module + '.py')

                if location.is_dir() and plugin in location.iterdir():
                    spec = importlib.util.spec_from_file_location(location.name,
                                                                  plugin)
                    plugins[location.name] = {
                        'parent_dir': self.search_root,
                        'spec': spec,
                        'type': 'pipeline'
                    }
        except FileNotFoundError:
            pass

        return plugins


class ProjectPluginManager(BasePluginManager):
    """Plugins are `directories` found in a root plugin directory.

    Intended for use with :term:`Project plugins <plugin>`.

    """

    def __init__(self, search_root: pathlib.Path, project: str) -> None:
        super().__init__()

        self.search_root = search_root
        self.project = project

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
        plugins = {}
        try:
            for location in self.search_root.iterdir():
                if self.project in location.name:
                    plugins[location.name] = {
                        'parent_dir': self.search_root,
                        'spec': None,
                        'type': 'project'
                    }

        except FileNotFoundError:
            pass

        return plugins


class CompositePluginManager(BasePluginManager):
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

            if utils.path_exists(project_path):
                project_plugin = ProjectPluginManager(d, project)
                self.components.append(project_plugin)
            else:
                pipeline_plugin = DirectoryPluginManager(d)
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
        # We manually add 'sierra.plugins' here, rather than adding the
        # necessary directory to PYTHONPATH so that we don't accidentally get
        # the files from other non-platform plugins with the same name as the
        # platform plugin file we are interested in getting picked.
        platform_path = f'sierra.plugins.{platform}.{path}'
        if module_exists(platform_path):
            logging.trace("Using platform component path '%s'",  # type: ignore
                          platform_path)
            return module_load(platform_path)
        else:
            logging.trace("Platform component path '%s' does not exist",  # type: ignore
                          platform_path)

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
