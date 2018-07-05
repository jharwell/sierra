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

import numpy as np


class BaseCriteria:
    def gen_list(self):
        """Generate list of lists criteria for input into batch pipeline."""
        raise NotImplementedError


class SwarmSize(BaseCriteria):

    """
    Defines a range of swarm sizes to test with

    Attributes:
      size_list(list): List of integer sizes to test with.
    """
    def __init__(self, size_list):
        self.size_list = size_list

    def gen_list(self):
        """Generate list of lists criteria for input into batch pipeline."""
        return [[("arena.entity.quantity", s)] for s in self.size_list]


class SwarmSize1024Linear(SwarmSize):
    def __init__(self):
        super().__init__([x for x in range(4, 1028, 4)])


class SwarmSize512Linear(SwarmSize):
    def __init__(self):
        super().__init__([x for x in range(4, 516, 4)])


class SwarmSize256Linear(SwarmSize):
    def __init__(self):
        super().__init__([x for x in range(4, 260, 4)])


class SwarmSize64Linear(SwarmSize):
    def __init__(self):
        super().__init__([x for x in range(4, 68, 4)])


class SwarmSize1024Log(SwarmSize):
    def __init__(self):
        super().__init__([x ** 2 for x in range(2, 11)])


class SwarmSize256Log(SwarmSize):
    def __init__(self):
        super().__init__([x ** 2 for x in range(2, 10)])


class SwarmSize128Log(SwarmSize):
    def __init__(self):
        super().__init__([x ** 2 for x in range(2, 8)])


class SwarmSize64Log(SwarmSize):
    def __init__(self):
        super().__init__([x ** 2 for x in range(2, 7)])


class RectArenaSize(BaseCriteria):

    """
    Defines an (X, Y) size of a rectangular arena to test with.

    Attributes:
      dimensions(list): List of (X, Y) tuples of arena size.
    """
    def __init__(self, dimensions):
        self.dimensions = dimensions

    def gen_list(self):
        """Generate list of lists criteria for input into batch pipeline. Each list contains a set of tuples of
        modifications to simulation input files to change the size of the arena"""
        return [[("arena.size", "{0}, {1}, 2".format(s[0], s[1])),
                 ("arena.center", "{0}, {1}, 1".format(s[0] / 2.0, s[1] / 2.0)),

                 ("arena.wall_north.size", "{0}, 0.1, 0.5".format(s[0])),
                 ("arena.wall_north.position", "{0}, {1}, 0".format(s[0] / 2.0, s[1], 0)),
                 ("arena.wall_south.size", "{0}, 0.1, 0.5".format(s[0])),
                 ("arena.wall_south.position", "{0}, 0, 0 ".format(s[0] / 2.0)),
                 ("arena.wall_east.size", "0.1, {0}, 0.5".format(s[1])),
                 ("arena.wall_east.position", "{0}, {1}, 0".format(s[0], s[1] / 2.0)),
                 ("arena.wall_west.size", "0.1, {0}, 0.5".format(s[1])),
                 ("arena.wall_west.position", "0, {0}, 0".format(s[1] / 2.0))]
                for s in self.dimensions]


class RectArenaSizeTwoByOne(RectArenaSize):
    def __init__(self):
        super().__init__([(x, y) for x in range(10, 110, 10) for y in range(5, 55, 5)])


class RectArenaSizeCorridor(RectArenaSize):
    def __init__(self):
        super().__init__([(x, 5) for x in range(20, 110, 10)])


class TaskEstimationAlpha(BaseCriteria):
    """
    Define a list of floating point values in [0,1] to test with.
    Attributes:
      range_list(list): List of values for estimation alpha.
    """
    def gen_list(self):
        """Generate list of lists criteria for input into batch pipeline."""
        return [[("params.task_executive.estimation.alpha", s)] for s in np.arange(0.1, 0.95, 0.05)]
