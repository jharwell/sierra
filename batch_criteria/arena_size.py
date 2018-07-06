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

from batch_criteria import BaseCriteria


class RectangularArena(BaseCriteria):

    """
    Defines an (X, Y) size of a rectangular arena to test with.

    Attributes:
      dimensions(list): List of (X, Y) tuples of arena size.
    """

    def __init__(self, dimensions):
        self.dimensions = dimensions

    def gen_list(self):
        """Generate list of lists criteria for input into batch pipeline. Each list contains a set of tuples of
        modifications to simulation input files to change:

        - The size of the arena
        - The allowable area of initial distribution of robots in the arena
        - The position of the lights above the nest
        - The position of the nest
        - The position of the source

        The arena is always treated as a left -> right horizontal rectangle, with the nest and the
        source (if applicable) at opposite ends.
        """
        return [[("arena.size", "{0}, {1}, 2".format(s[0], s[1])),
                 ("arena.center", "{0}, {1}, 1".format(s[0] / 2.0, s[1] / 2.0)),
                 ("arena.wall_north.size", "{0}, 0.1, 0.5".format(s[0])),
                 ("arena.wall_north.position", "{0}, {1}, 0".format(s[0] / 2.0, s[1], 0)),
                 ("arena.wall_south.size", "{0}, 0.1, 0.5".format(s[0])),
                 ("arena.wall_south.position", "{0}, 0, 0 ".format(s[0] / 2.0)),
                 ("arena.wall_east.size", "0.1, {0}, 0.5".format(s[1])),
                 ("arena.wall_east.position", "{0}, {1}, 0".format(s[0], s[1] / 2.0)),
                 ("arena.wall_west.size", "0.1, {0}, 0.5".format(s[1])),
                 ("arena.wall_west.position", "0, {0}, 0".format(s[1] / 2.0)),
                 ("arena.distribution.position.max", "{0}, {1}, 0".format(s[0] - 2, s[1] - 1)),
                 ("arena.light1.position", "2, {0}, 1.0".format(s[1] * 0.25)),
                 ("arena.light1.position", "2, {0}, 1.0".format(s[1] * 0.5)),
                 ("arena.light1.position", "2, {0}, 1.0".format(s[1] * 0.75)),
                 ("arena_map.nest.size", "{0}, {1}".format(s[0] / 10.0, s[1] * 0.8)),
                 ("arena_map.nest.center", "2.0, {0}".format(s[1] / 2.0)),
                 ("arena_map.grid.size", "{0}, {1}, 2".format(s[0], s[1]))
                 ("fsm.nest", "2.0, {0}".format(s[1] / 2.0))
                 ("occupancy_grid.grid.size", "{0}, {1}, 2".format(s[0], s[1]))
                 ]
                for s in self.dimensions]


class RectangularArenaTwoByOne(RectangularArena):
    def __init__(self):
        super().__init__([(x, y) for x in range(10, 110, 10) for y in range(5, 55, 5)])


class RectangularArenaCorridor(RectangularArena):
    def __init__(self):
        super().__init__([(x, 5) for x in range(20, 110, 10)])
