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
SUPER DUPER simple plugin managers for being able to add stuff to SIERRA without having to modify
the sierra.core.
"""
# Core packages
import importlib.util
import importlib
import os
import logging
import typing as tp
import sys

# 3rd party packages
from singleton_decorator import singleton

# Project packages


class BasePluginManager():
    """
    Base class for common functionality.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.loaded = {}

    def loaded_plugins(self):
        return self.loaded.copy()

    def initialize(self):
        raise NotImplementedError

    def available_plugins(self):
        raise NotImplementedError

    def load_plugin(self, name: str):
        """
        Loads a plugin module.
        """
        plugins = self.available_plugins()
        if name not in plugins:
            self.logger.error("Cannot locate plugin '%s'", name)
            raise Exception("Cannot locate plugin '%s'" % name)

        if name not in self.loaded:
            module = importlib.util.module_from_spec(plugins[name]['spec'])

            plugins[name]['spec'].loader.exec_module(module)
            scoped_name = '{0}.{1}'.format(os.path.basename(plugins[name]['parent_dir'].strip("/")),
                                           name)
            self.loaded[scoped_name] = {
                'spec': plugins[name]['spec'],
                'module': module
            }
            self.logger.debug("Loaded plugin '%s' from '%s'",
                              scoped_name,
                              plugins[name]['parent_dir'])
        else:
            self.logger.warning("Plugin '%s' already loaded", name)

        return self.loaded[scoped_name]['module']

    def get_plugin(self, name: str):
        try:
            return self.loaded[name]['module']
        except KeyError:
            self.logger.critical("No such plugin '%s'", name)
            raise


class FilePluginManager(BasePluginManager):
    """
    A simple plugin manager where plugins are ``.py`` `files` within a root plugin directory.
    """

    def __init__(self, search_root: str) -> None:
        super().__init__()
        self.search_root = search_root
        self.plugins = {}

    def initialize(self) -> None:
        self.plugins = self.calc_available_plugins()

    def available_plugins(self) -> tp.Dict[str, tp.Dict[str, importlib.machinery.ModuleSpec]]:
        """
        Returns a dictionary of plugins available in the configured plugin root.
        """
        return self.plugins

    def calc_available_plugins(self):
        plugins = {}
        for possible in os.listdir(self.search_root):
            candidate = os.path.join(self.search_root, possible)
            if os.path.isfile(candidate) and '.py' in candidate:
                name = os.path.split(candidate)[1].split('.')[0]
                spec = importlib.util.spec_from_file_location(name, candidate)
                plugins[name] = {
                    'spec': spec,
                    'parent_dir': self.search_root,
                }
        return plugins


class DirectoryPluginManager(BasePluginManager):
    """
    A simple plugin manager where plugins are `directories` found in a root plugin directory.
    """

    def __init__(self, search_root: str) -> None:
        super().__init__()

        self.search_root = search_root
        self.plugins = {}
        self.main_module = 'main'

    def initialize(self) -> None:
        self.plugins = self.calc_available_plugins()

    def available_plugins(self):
        """
        Returns a dictionary of plugins available in the configured plugin root.
        """
        return self.plugins

    def calc_available_plugins(self):
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
                        'spec': spec
                    }
        except FileNotFoundError:
            pass

        return plugins


class CompositePluginManager(BasePluginManager):
    def __init__(self, search_path: tp.List[str]) -> None:
        super().__init__()
        self.search_path = search_path
        self.logger.debug("Using plugin search path %s", self.search_path)
        self.components = [DirectoryPluginManager(d) for d in search_path]
        self.plugins = {}

    def loaded_plugins(self):
        return self.loaded.copy()

    def initialize(self) -> None:
        for c in self.components:
            c.initialize()

        self.plugins = self.calc_available_plugins()

    def available_plugins(self):
        return self.plugins

    def calc_available_plugins(self):
        plugins = {}
        for c in self.components:
            plugins.update(c.available_plugins())

        return plugins


@singleton
class SIERRAPluginManager(CompositePluginManager):
    pass


@singleton
class ModelPluginManager(FilePluginManager):
    pass


def module_exists(name: str):
    try:
        mod = __import__(name)
    except ImportError:
        return False
    else:
        return True


def module_load(name: str):
    try:
        mod = __import__(name, fromlist=["*"])
    except ImportError:
        return None
    else:
        return mod


def bc_load(cmdopts: tp.Dict[str, tp.Any], category: str):
    path = 'variables.{0}'.format(category)
    return module_load_tiered(cmdopts['project'], path)


def module_load_tiered(project: str, path: str):
    # First, see if the requested module is a project
    if module_exists(path):
        logging.trace("Using project path '%s'", path)
        return module_load(path)

    # First, see if the requested module is part of the project plugin
    plugin_path = 'projects.{0}.{1}'.format(project, path)
    if module_exists(plugin_path):
        logging.trace("Using project plugin path '%s'", plugin_path)
        return module_load(plugin_path)
    else:
        logging.trace("Project plugin path '%s' does not exist", plugin_path)

    # If that didn't work, then check the SIERRA core
    core_path = 'sierra.core.{0}'.format(path)
    if module_exists(core_path):
        logging.trace("Using SIERRA core path '%s'", core_path)
        return module_load(core_path)
    else:
        logging.trace("SIERRA core path '%s' does not exist", core_path)

    # Module does not exist
    raise ImportError('project: {0} path: {1} sys.path: {2}', project, path, sys.path)
