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


class RectangularArena(BaseVariable):

    """
    Defines an (X, Y) size of a rectangular arena to test with.

    Attributes:
      dimensions(list): List of (X, Y) tuples of arena size.
    """

    def __init__(self, dimensions):
        self.dimensions = dimensions

    def gen_attr_changelist(self):
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation with the specified area size/shape.

        Tuples of modifications to simulation input files to change:

        - The shape of the arena [square, rectangular]
        - The size of the arena
        """
        return [set([("arena.size", "{0}, {1}, 2".format(s[0], s[1])),
                     ("arena.center", "{0}, {1}, 1".format(s[0] / 2.0, s[1] / 2.0)),
                     ("arena.wall_north.size", "{0}, 0.1, 0.5".format(s[0])),
                     ("arena.wall_north.position", "{0}, {1}, 0".format(s[0] / 2.0, s[1], 0)),
                     ("arena.wall_south.size", "{0}, 0.1, 0.5".format(s[0])),
                     ("arena.wall_south.position", "{0}, 0, 0 ".format(s[0] / 2.0)),
                     ("arena.wall_east.size", "0.1, {0}, 0.5".format(s[1])),
                     ("arena.wall_east.position", "{0}, {1}, 0".format(s[0], s[1] / 2.0)),
                     ("arena.wall_west.size", "0.1, {0}, 0.5".format(s[1])),
                     ("arena.wall_west.position", "0, {0}, 0".format(s[1] / 2.0)),
                     ("arena.distribute.position.max", "{0}, {1}, 0".format(s[0] - 2, s[1] - 1)),
                     ("arena_map.grid.size", "{0}, {1}, 2".format(s[0], s[1])),
                     ("occupancy_grid.grid.size", "{0}, {1}, 2".format(s[0], s[1]))
                     ])
                for s in self.dimensions]

    def gen_tag_rmlist(self):
        return []


class RectangularArenaTwoByOne(RectangularArena):
    def __init__(self, x_range=range(12, 120, 12), y_range=range(6, 66, 6)):
        super().__init__([(x, y) for x in x_range for y in y_range])


class RectangularArenaCorridor(RectangularArena):
    def __init__(self, x_range=range(24, 120, 12)):
        super().__init__([(x, 6) for x in x_range])


class SquareArena(RectangularArena):
    def __init__(self, sqrange=range(12, 120, 12)):
        super().__init__([(x, x) for x in sqrange])
