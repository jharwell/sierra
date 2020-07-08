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
A SUPER DUPER simple plugin manager for being able to add stuff to SIERRA without having to modify
the core.
"""
import importlib
import os
import logging
from singleton_decorator import singleton


@singleton
class PluginManager():
    """
    A SUPER simple plugin manager.
    """

    def __init__(self):
        self.plugin_root = ''
        self.main_module = 'foo'
        self.loaded_plugins = None

    def initialize(self, plugin_root):
        self.main_module = 'main'
        self.plugin_root = plugin_root
        self.loaded_plugins = dict()

    def available_plugins(self):
        """
        Returns a dictionary of plugins available in the configured plugin root.
        """
        plugins = {}
        for possible in os.listdir(self.plugin_root):
            location = os.path.join(self.plugin_root, possible)
            if os.path.isdir(location) and self.main_module + '.py' in os.listdir(location):
                spec = importlib.machinery.PathFinder().find_spec(self.main_module, [location])
                plugins[possible] = {
                    'spec': spec
                }
        return plugins

    def loaded(self):
        """
        Returns a dictionary of the loaded plugin modules
        """
        return self.loaded_plugins.copy()

    def load_plugin(self, name: str):
        """
        Loads a plugin module.
        """
        plugins = self.available_plugins()
        if name not in plugins:
            logging.error("Cannot locate plugin '%s'", name)
            raise Exception("Cannot locate plugin '%s'" % name)

        if name not in self.loaded_plugins:
            module = plugins[name]['spec'].loader.load_module()
            self.loaded_plugins[name] = {
                'spec': plugins[name]['spec'],
                'module': module
            }
            logging.info("Loaded plugin '%s'", os.path.join(self.plugin_root, name))
        else:
            logging.warning("Plugin '%s' already loaded", name)

    def get_plugin(self, name: str):
        return self.loaded_plugins[name]['module']
