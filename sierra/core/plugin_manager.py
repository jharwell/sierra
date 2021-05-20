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

# 3rd party packages
from singleton_decorator import singleton

# Project packages


class BasePluginManager():
    """
    Base class for common functionality.
    """

    def __init__(self) -> None:
        self.plugin_root = ''
        self.loaded = dict()
        self.logger = logging.getLogger(__name__)

    def initialize(self, plugin_root: str) -> None:
        self.plugin_root = plugin_root
        self.loaded = dict()

    def loaded_plugins(self):
        """
        Returns a dictionary of the loaded plugin modules
        """
        return self.loaded.copy()

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

            self.loaded[name] = {
                'spec': plugins[name]['spec'],
                'module': module
            }
            self.logger.debug("Loaded plugin '%s'",
                              os.path.join(os.path.basename(self.plugin_root), name))
        else:
            self.logger.warning("Plugin '%s' already loaded", name)

        return self.loaded[name]['module']

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

    def available_plugins(self) -> tp.Dict[str, tp.Dict[str, importlib.machinery.ModuleSpec]]:
        """
        Returns a dictionary of plugins available in the configured plugin root.
        """
        plugins = {}
        for possible in os.listdir(self.plugin_root):
            candidate = os.path.join(self.plugin_root, possible)
            if os.path.isfile(candidate) and '.py' in candidate:
                name = os.path.split(candidate)[1].split('.')[0]
                spec = importlib.util.spec_from_file_location(name, candidate)
                plugins[name] = {
                    'spec': spec
                }
        return plugins


class DirectoryPluginManager(BasePluginManager):
    """
    A simple plugin manager where plugins are `directories` found in a root plugin directory.
    """

    def __init__(self) -> None:
        super().__init__()
        self.main_module = 'foo'

    def initialize(self, plugin_root: str) -> None:
        super().initialize(plugin_root)
        self.main_module = 'main'

    def available_plugins(self):
        """
        Returns a dictionary of plugins available in the configured plugin root.
        """
        plugins = {}
        for possible in os.listdir(self.plugin_root):
            location = os.path.join(self.plugin_root, possible)
            if os.path.isdir(location) and self.main_module + '.py' in os.listdir(location):
                spec = importlib.util.spec_from_file_location(possible,
                                                              os.path.join(location,
                                                                           self.main_module + '.py'))
                plugins[possible] = {
                    'spec': spec
                }
        return plugins


@singleton
class ModelPluginManager(FilePluginManager):
    pass


def module_exists(name: str):
    # print(sys.modules.keys())
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


def load_bc(cmdopts: tp.Dict[str, tp.Any], category: str):
    path = 'variables.{0}'.format(category)
    return module_load_tiered(cmdopts['project'], path)


def module_load_tiered(project: str, path: str):
    # First, see if the variable is part of the project plugin
    plugin_path = 'projects.{0}.{1}'.format(project, path)
    if module_exists(plugin_path):
        logging.debug("Using project plugin path '%s'", plugin_path)
        return module_load(plugin_path)
    else:
        logging.debug("Project plugin path '%s' does not exist", plugin_path)

    # If that didn't work, then check the SIERRA core
    core_path = 'sierra.core.{0}'.format(path)
    if module_exists(core_path):
        logging.debug("Using SIERRA core path '%s'", core_path)
        return module_load(core_path)
    else:
        logging.debug("SIERRA core path '%s' does not exist", core_path)

    # Module does not exist
    raise ImportError(path)
