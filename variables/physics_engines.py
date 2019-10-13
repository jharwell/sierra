# Copyright 2018 John Harwell, All rights reserved.
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


from variables.base_variable import BaseVariable


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
            return [self._gen1_engines(s) for s in self.dimensions]
        elif 4 == self.n_engines:
            return [self._gen4_engines(s) for s in self.dimensions]
        elif 8 == self.n_engines:
            return [self._gen8_engines(s) for s in self.dimensions]
        elif 16 == self.n_engines:
            return [self._gen16_engines(s) for s in self.dimensions]
        elif 24 == self.n_engines:
            return [self._gen24_engines(s) for s in self.dimensions]
        else:
            raise RuntimeError

    def _gen1_engines(self, dims):
        """
        Generate definitions for physics engines for the specified pair of (X,Y) dimensions if the #
        requested engines was 1.
        """
        return [('.', 'physics_engines', {}),
                (".//physics_engines", 'dynamics2d', {'id': 'dyn2d'})]

    def _gen4_engines(self, dims):
        """
        Generate definitions for 4 physics engines for the specified pair of (X,Y) dimensions. The
        layout is:

         3 2
         0 1
        """
        return self._gen_engines(dims,
                                 n_engines_x=2,
                                 n_engines_y=2,
                                 forward_engines=[0, 1])

    def _gen8_engines(self, dims):
        """
        Generate definitions for 8 physics engines for the specified pair of (X,Y) dimensions. The
        layout is:

        7 6 5 4
        0 1 2 3
        """
        return self._gen_engines(dims,
                                 n_engines_x=4,
                                 n_engines_y=2,
                                 forward_engines=[0, 1, 2, 3])

    def _gen16_engines(self, dims):
        """
        Generate definitions for 16 physics engines for the specified pair of (X,Y) dimensions. The
        layout is:

        15 14 13 12
        8  9  10 11
        7  6  5  4
        0  1  2  3
        """
        return self._gen_engines(dims,
                                 n_engines_x=4,
                                 n_engines_y=4,
                                 forward_engines=[0, 1, 2, 3, 8, 9, 10, 11])

    def _gen24_engines(self, dims):
        """
        Generate definitions for 24 physics engines for the specified pair of (X,Y). The layout is:

        23  22 21  20 19 18
        12  13 14  15 16 17
        11  10  9  8  7  6
        0   1   2  3  4  5
        """
        return self._gen_engines(dims,
                                 n_engines_x=6,
                                 n_engines_y=4,
                                 forward_engines=[0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17])

    def _gen_engines(self, dims, n_engines_x, n_engines_y, forward_engines):
        """
        Generate definitions for physics engines for the specified pair of (X,Y) dimensions.

        n_engines_x: # engines in the x direction.
        n_engines_y: # engines in the y direction.
        forward_engines: IDs of engines that are placed in increasing order in X when layed out
                         L->R.
        """
        adds = [('.', 'physics_engines', {})]
        size_x = self.dimensions[0] / n_engines_x
        size_y = self.dimensions[1] / n_engines_y

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

            # Engine lower X coord increasing as engine id increases
            if i in forward_engines:
                ll_x = size_x * (i % n_engines_x)
                lr_x = size_x * ((i % n_engines_x) + 1)

            else:  # Engine lower X coord increasing as engine id DECREASES
                ll_x = size_x * (n_engines_x - (i % n_engines_x) - 1)
                lr_x = size_x * ((n_engines_x - (i % n_engines_x) - 1) + 1)

            ur_x = lr_x
            ul_x = ll_x

            # We use the max of # engines in X/Y to get the nice numbering/layout of engines.
            ll_y = size_y * (int(i / max(n_engines_x, n_engines_y)))
            ul_y = size_y * (int(i / max(n_engines_x, n_engines_y)) + 1)

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
