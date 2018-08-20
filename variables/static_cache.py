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


class StaticCache(BaseVariable):

    """
    Defines the size and capacity of a static cache to test with. Only really applicable to single
    source foraging scenarios, but will work with only types as well.

    Attributes:
      sizes(list): List of the # of blocks the cache should have each time the simulation respawns it.
      dimension(list) List of the arena (X,Y) dimensions.
    """

    def __init__(self, sizes, dimension):
        self.sizes = sizes
        self.dimension = dimension

    def gen_attr_changelist(self):
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation with the specified static cache.

        Tuples of modifications to simulation input files to change:

        """
        return [set([("static_caches.enable", "true"),
                     ("static_caches.size", "{0}".format(s)),
                     ("static_caches.min_dist", "{0}".format(d[0] / 10.0)),
                     ("static_caches.dimension", "{0}".format(d[0] / 10.0))
                     ])
                for d in self.dimension for s in self.sizes]

    def gen_tag_rmlist(self):
        return []
