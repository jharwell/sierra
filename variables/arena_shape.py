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

import typing as tp
from variables.base_variable import BaseVariable
import math

kWallWidth = 0.4


class RectangularArena(BaseVariable):

    """
    Maps a list of desired arena dimensions specified in (X,Y) tuples to a list of sets of changes
    from a necessary to modify the arena dimensions to realize each desired area size. This class is
    a base class which should (almost) never be used on its own. Instead, derived classes defined in
    this file should be used instead.

    Attributes:
        dimensions: List of (X, Y) tuples of arena size.
    """

    def __init__(self, dimensions: tp.List[tuple]):
        self.dimensions = dimensions

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation with the specified area size/shape.
        """
        return [set([(".//arena", "size", "{0}, {1}, 2".format(s[0], s[1])),
                     (".//arena", "center", "{0}, {1}, 1".format(s[0] / 2.0, s[1] / 2.0)),

                     # We restrict the places robots can spawn within the arena as follows:
                     #
                     # - Subtract width of the walls so that robots do not spawn inside walls (which
                     #   ARGoS seems to allow?).
                     # - Subtract a little bit more so robots don't get into weird states by being
                     #   near arena boundaries on the first timestep.
                     (".//arena/distribute/position",
                      "max",
                      "{0}, {1}, 0".format(s[0] - 2.0 * kWallWidth - 2.0,
                                           s[1] - 2.0 * kWallWidth - 2.0)),
                     (".//arena/distribute/position",
                      "min",
                      "{0}, {1}, 0".format(2.0 * kWallWidth + 2.0, 2.0 * kWallWidth + 2.0)),

                     (".//arena/*[@id='wall_north']", "size", "{0}, {1}, 0.5".format(s[0],
                                                                                     kWallWidth)),

                     # North wall needs to have its Y coordinate offset by the width of the wall / 2
                     # in order to be centered on the boundary for the arena. This is necessary to
                     # ensure that the maximum Y coordinate that robots can access is LESS than the
                     # upper boundary of physics engines incident along the north wall.
                     #
                     # I think this is a bug in ARGoS.
                     (".//arena/*[@id='wall_north']/body",
                      "position", "{0}, {1}, 0".format(s[0] / 2.0,
                                                       s[1] - kWallWidth / 2.0)),
                     (".//arena/*[@id='wall_south']", "size", "{0}, {1}, 0.5".format(s[0],
                                                                                     kWallWidth)),
                     (".//arena/*[@id='wall_south']/body",
                      "position", "{0}, 0, 0 ".format(s[0] / 2.0)),


                     # Same thing for the east wall.
                     (".//arena/*[@id='wall_east']", "size", "{0}, {1}, 0.5".format(kWallWidth,
                                                                                    s[1] + kWallWidth)),
                     (".//arena/*[@id='wall_east']/body",
                      "position",
                      "{0}, {1}, 0".format(s[0] - kWallWidth / 2.0,
                                           s[1] / 2.0)),

                     (".//arena/*[@id='wall_west']", "size", "{0}, {1}, 0.5".format(kWallWidth,
                                                                                    s[1] + kWallWidth)),
                     (".//arena/*[@id='wall_west']/body",
                      "position", "0, {0}, 0".format(s[1] / 2.0)),

                     (".//arena_map/grid", "size", "{0}, {1}, 2".format(s[0], s[1])),
                     (".//perception/grid", "size", "{0}, {1}, 2".format(s[0], s[1])),

                     (".//convergence/positional_entropy",
                      "horizon",
                      "0:{0}".format(math.sqrt(s[0] ** 2 + s[1] ** 2))),
                     (".//convergence/positional_entropy",
                      "horizon_delta",
                      "{0}".format(math.sqrt(s[0] ** 2 + s[1] ** 2) / 10.0)),

                     # Finally, set camera positioning. Probably will not be used, but IF rendering
                     # is enabled we want to have the visualizations come out nicely. I assume a
                     # single camera is present.
                     (".//camera/placement",
                      "position", "{0}, {1}, {2}".format(s[0] / 2.0,
                                                         s[1] / 2.0,
                                                         max(s[0], s[1]) * 2.0 / 3.0)),
                     (".//camera/placement",
                      "look_at", "{0}, {1}, 0".format(s[0] / 2.0,
                                                      s[1] / 2.0))
                     ])
                for s in self.dimensions]

    def gen_tag_rmlist(self) -> list:
        return []

    def gen_tag_addlist(self) -> list:
        return []


class RectangularArenaTwoByOne(RectangularArena):
    """
    Define arenas that vary in size for each combination of dimensions in the specified X range and
    Y range, where the X dimension is always twices as large as the Y dimension.
    """

    def __init__(self, x_range: range, y_range: range):
        super().__init__([(x, y) for x in x_range for y in y_range])


class SquareArena(RectangularArena):
    """
    Define arenas that vary in size for each combination of dimensions in the specified X range and
    Y range, where the X and y dimensions are always equal.
    """

    def __init__(self, sqrange: range):
        super().__init__([(x, x) for x in sqrange])
