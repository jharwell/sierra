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
"""
SUPER DUPER simple plugin managers for being able to add stuff to SIERRA
without having to modify the sierra.core.

"""
# Core packages
import importlib.util
import importlib
import os
import typing as tp
import sys
import logging  # type: tp.Any

# 3rd party packages

# Project packages
from sierra.core import types, utils


class BasePluginManager():
    """
    Base class for common functionality.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.loaded = {}  # type: tp.Dict[str, tp.Dict]

    def loaded_plugins(self):
        return self.loaded.copy()

    def initialize(self, project: str):
        raise NotImplementedError

    def available_plugins(self):
        raise NotImplementedError

    def load_plugin(self, name: str) -> None:
        """
        Loads a plugin module.
        """
        plugins = self.available_plugins()
        if name not in plugins:
            self.logger.fatal("Cannot locate plugin '%s'", name)
            raise Exception("Cannot locate plugin '%s'" % name)

        if plugins[name]['type'] == 'pipeline':
            scoped_name = '{0}.{1}'.format(os.path.basename(plugins[name]['parent_dir'].strip("/")),
                                           name)
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

            return self.loaded[scoped_name]['module']
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
            self.logger.fatal("Loaded plugins: %s", self.loaded)
            raise

    def get_plugin_module(self, name: str) -> types.ModuleType:
        try:
            return self.loaded[name]['module']
        except KeyError:
            self.logger.fatal("No such plugin '%s'", name)
            self.logger.fatal("Loaded plugins: %s", self.loaded)
            raise

    def has_plugin(self, name: str) -> bool:
        return name in self.loaded


class FilePluginManager(BasePluginManager):
    """
    A plugin manager where plugins are ``.py`` files within a root plugin
    directory. Intended for use with :term:`models <Model>`.

    """

    def __init__(self) -> None:
        super().__init__()
        self.search_root = None

    def initialize(self, project: str, search_root: str) -> None:
        self.search_root = search_root

    def available_plugins(self) -> tp.Dict[str, tp.Dict]:
        """
        Returns a dictionary of plugins available in the configured plugin
        root.
        """
        plugins = {}
        for possible in os.listdir(self.search_root):
            candidate = os.path.join(self.search_root, possible)
            if os.path.isfile(candidate) and '.py' in candidate:
                name = "{0}.{1}".format(os.path.basename(candidate),
                                        os.path.splitext(os.path.split(candidate)[1]))

                spec = importlib.util.spec_from_file_location(name, candidate)
                plugins[name] = {
                    'spec': spec,
                    'parent_dir': self.search_root,
                    'type': 'pipeline'
                }
        return plugins


class DirectoryPluginManager(BasePluginManager):
    """
    A plugin manager where plugins are `directories` found in a root plugin
    directory. Intended for use with :term:`Pipeline plugins <plugin>`.

    """

    def __init__(self, search_root: str) -> None:
        super().__init__()
        self.search_root = search_root
        self.main_module = 'plugin'

    def initialize(self, project: str) -> None:
        pass

    def available_plugins(self):
        """
        Finds all pipeline plugins in all directories within the search root.
        """
        plugins = {}
        try:
            for possible in os.listdir(self.search_root):
                location = os.path.join(self.search_root, possible)
                if os.path.isdir(location) and self.main_module + '.py' in os.listdir(location):
                    spec = importlib.util.spec_from_file_location(possible,
                                                                  os.path.join(location,
                                                                               self.main_module + '.py'))
                    plugins[possible] = {
                        'parent_dir': self.search_root,
                        'spec': spec,
                        'type': 'pipeline'
                    }
        except FileNotFoundError:
            pass

        return plugins


class ProjectPluginManager(BasePluginManager):
    """
    A plugin manager where plugins are `directories` found in a root plugin
    directory. Intended for use with :term:`Project plugins
    <plugin>`.

    """

    def __init__(self, search_root: str, project: str) -> None:
        super().__init__()

        self.search_root = search_root
        self.project = project

    def initialize(self, project: str) -> None:
        # Update PYTHONPATH with the directory containing the project so imports
        # of the form 'import project.module' work.
        #
        # 2021/07/19: If you put the entries at the end of sys.path it
        # doesn't work for some reason...
        sys.path = [self.search_root] + sys.path[0:]

    def available_plugins(self):
        """
        Finds all pipeline plugins in all directories within the search root.
        """
        plugins = {}
        try:
            for possible in os.listdir(self.search_root):
                location = os.path.join(self.search_root, possible)
                if self.project in location:
                    plugins[possible] = {
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
        self.components = []

    def loaded_plugins(self):
        return self.loaded.copy()

    def initialize(self, project: str, search_path: tp.List[str]) -> None:
        self.logger.debug("Initializing with plugin search path %s",
                          search_path)
        for d in search_path:
            project_path = os.path.join(d, project)

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
    try:
        mod = __import__(name)
    except ImportError:
        return False
    else:
        return True


def module_load(name: str) -> types.ModuleType:
    return __import__(name, fromlist=["*"])


def bc_load(cmdopts: types.Cmdopts, category: str):
    path = 'variables.{0}'.format(category)
    return module_load_tiered(project=cmdopts['project'],
                              platform=cmdopts['platform'],
                              path=path)


def module_load_tiered(path: str,
                       project: tp.Optional[str] = None,
                       platform: tp.Optional[str] = None) -> types.ModuleType:
    # First, see if the requested module is a project
    if module_exists(path):
        logging.trace("Using project path '%s'", path)
        return module_load(path)

    # First, see if the requested module is part of the project plugin
    if project is not None:
        component_path = '{0}.{1}'.format(project, path)
        if module_exists(component_path):
            logging.trace("Using project component path '%s'", component_path)
            return module_load(component_path)
        else:
            logging.trace("Project component path '%s' does not exist",
                          component_path)

    # If that didn't work, check the platform plugin
    if platform is not None:
        # We manually add 'sierra.plugins' here, rather than adding the
        # necessary directory to PYTHONPATH so that we don't accidentally get
        # the files from other non-platform plugins with the same name as the
        # platform plugin file we are interested in getting picked.
        platform_path = 'sierra.plugins.{0}.{1}'.format(platform, path)
        if module_exists(platform_path):
            logging.trace("Using platform component path '%s'", platform_path)
            return module_load(platform_path)
        else:
            logging.trace("Platform component path '%s' does not exist",
                          platform_path)

    # If that didn't work, then check the SIERRA core
    core_path = 'sierra.core.{0}'.format(path)
    if module_exists(core_path):
        logging.trace("Using SIERRA core path '%s'", core_path)
        return module_load(core_path)
    else:
        logging.trace("SIERRA core path '%s' does not exist", core_path)

    # Module does not exist
    error = "project: '{0}' platform: '{1}' path: '{2}' sys.path: {3}".format(project,
                                                                              platform,
                                                                              path,
                                                                              sys.path)
    raise ImportError(error)
