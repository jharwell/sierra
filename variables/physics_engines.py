"""
 Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

from variables.base_variable import BaseVariable
import math


class PhysicsEngines(BaseVariable):

    """
    Defines the # of physics engines that a simulation will employ, and how they will be arranged
    within an arena. Assumes that all entities in simulation are ground robots.

    Attributes:
      n_engines(int): # of engines. Can be one of [1,4,16].
      iter_per_tick(int): # of iterations physics engines should perform per tick.
      layout(str): Arrangement method. Can be one of: {uniform_grid}.
      dimensions(list): List of (X,Y) tuples of arena sizes.
    """

    def __init__(self, n_engines, iter_per_tick, layout, dimensions):
        self.n_engines = n_engines
        self.iter_per_tick = iter_per_tick
        self.layout = layout
        self.dimensions = dimensions

    def gen_attr_changelist(self):
        """
        Does nothing because all tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self):
        """
        Always remove the physics_engines tag if it exists so we are starting from a clean slate
        each time. Obviously you *must* call this function BEFORE adding new definitions.
        """
        return [set([(".", "./physics_engines")])]

    def gen_tag_addlist(self):
        """
        Add definitions for each of the physics engines the user has indicated that they want to
        use.
        """
        if 1 == self.n_engines:
            return [self._add_1engines_for_dims(s) for s in self.dimensions]
        elif 4 == self.n_engines:
            return [self._add_4engines_for_dims(s) for s in self.dimensions]
        elif 16 == self.n_engines:
            return [self._add_16engines_for_dims(s) for s in self.dimensions]
        else:
            raise RuntimeError

    def _add_1engines_for_dims(self, dims):
        """
        Add definitions for physics engines for the specified pair of (X,Y) dimensions if the #
        requested engines was 1.
        """
        return [('.', 'physics_engines', {}),
                (".//physics_engines", 'dynamics2d', {'id': 'dyn2d'})]

    def _add_4engines_for_dims(self, dims):
        """
        Add definitions for physics engines for the specified pair of (X,Y) dimensions if the #
        requested engines was 4.
        """
        adds = [('.', 'physics_engines', {})]
        size_x = self.dimensions[0] / (self.n_engines / 2)
        size_y = self.dimensions[1] / (self.n_engines / 2)

        for i in range(0, self.n_engines):
            name = 'dyn2d' + str(i)
            adds.append(('.//physics_engines', 'dynamics2d', {'id': name,
                                                              'iterations': str(self.iter_per_tick)}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]",
                         "boundaries", {}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "top", {'height': '1'}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "bottom", {'height': '0'}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "sides", {}))

            ll_x = size_x * (i > 0 and i < 3)
            lr_x = size_x * ((i > 0 and i < 3) + 1)
            ur_x = lr_x
            ul_x = ll_x

            ll_y = size_y * (i > 1)
            ul_y = size_y * ((i > 1) + 1)
            lr_y = ll_y
            ur_y = ul_y

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ll_x, ll_y)}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(lr_x, lr_y)}))

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ur_x, ur_y)}))

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ul_x, ul_y)}))
        return adds

    def _add_16engines_for_dims(self, dims):
        """
        Add definitions for physics engines for the specified pair of (X,Y) dimensions if the #
        requested engines was 16.
        """
        adds = [('.', 'physics_engines', {})]
        size_x = self.dimensions[0] / math.sqrt(self.n_engines)
        size_y = self.dimensions[1] / math.sqrt(self.n_engines)

        for i in range(0, self.n_engines):
            name = 'dyn2d' + str(i)
            adds.append(('.//physics_engines', 'dynamics2d', {'id': name,
                                                              'iterations': str(self.iter_per_tick)}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]",
                         "boundaries", {}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "top", {'height': '1'}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "bottom", {'height': '0'}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "sides", {}))

            if (i <= 3 or (i >= 8 and i <= 11)):
                ll_x = size_x * (i % math.sqrt(self.n_engines))
                lr_x = size_x * ((i % math.sqrt(self.n_engines)) + 1)

            else:
                ll_x = size_x * (math.sqrt(self.n_engines) -
                                 (i % math.sqrt(self.n_engines)) - 1)
                lr_x = size_x * ((math.sqrt(self.n_engines) -
                                  (i % math.sqrt(self.n_engines)) - 1) + 1)

            ur_x = lr_x
            ul_x = ll_x
            ll_y = size_y * (int(i / math.sqrt(self.n_engines)))
            ul_y = size_y * (int(i / math.sqrt(self.n_engines)) + 1)

            lr_y = ll_y
            ur_y = ul_y

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ll_x, ll_y)}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(lr_x, lr_y)}))

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ur_x, ur_y)}))

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ul_x, ul_y)}))
        return adds
