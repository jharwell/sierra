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

import math
import typing as tp
from core.variables.base_variable import BaseVariable
from core.utils import ArenaExtent

kWALL_WIDTH = 0.4


class RectangularArena(BaseVariable):

    """
    Maps a list of desired arena dimensions specified in (X,Y) tuples to a list of sets of changes
    from a necessary to modify the arena dimensions to realize each desired area size. This class is
    a base class which should (almost) never be used on its own. Instead, derived classes defined in
    this file should be used instead.

    Attributes:
        dimensions: List of (X, Y, Z) tuples of arena size.
    """

    def __init__(self, dimensions: tp.List[ArenaExtent]) -> None:
        self.dimensions = dimensions

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation with the specified area size/shape.
        """
        return [set([(".//arena", "size", "{0}, {1}, 2".format(extent.x(), extent.y())),
                     (".//arena", "center",
                      "{0:.9f}, {1:.9f}, 1".format(extent.x() / 2.0, extent.y() / 2.0)),

                     # We restrict the places robots can spawn within the arena as follows:
                     #
                     # - Subtract width of the walls so that robots do not spawn inside walls (which
                     #   ARGoS seems to allow?).
                     #
                     # - Subtract a little bit more so robots don't get into weird states by being
                     #   near arena boundaries on the first timestep.
                     #
                     # - All robots start on the ground with Z=0.
                     (".//arena/distribute/position",
                      "max",
                      "{0:.9f}, {1:.9f}, 0".format(extent.x() - 2.0 * kWALL_WIDTH - 2.0,
                                                   extent.y() - 2.0 * kWALL_WIDTH - 2.0)),
                     (".//arena/distribute/position",
                      "min",
                      "{0:.9f}, {1:.9f}, 0".format(2.0 * kWALL_WIDTH + 2.0, 2.0 * kWALL_WIDTH + 2.0)),

                     (".//arena/*[@id='wall_north']", "size", "{0:.9f}, {1:.9f}, 0.5".format(extent.x(),
                                                                                             kWALL_WIDTH)),

                     (".//arena/*[@id='wall_north']/body",
                      "position", "{0:.9f}, {1:.9f}, 0".format(extent.x() / 2.0, extent.y())),
                     (".//arena/*[@id='wall_south']", "size", "{0:.9f}, {1:.9f}, 0.5".format(extent.x(),
                                                                                             kWALL_WIDTH)),
                     (".//arena/*[@id='wall_south']/body",
                      "position", "{0:.9f}, 0, 0 ".format(extent.x() / 2.0)),

                     # East wall needs to have its X coordinate offset by the width of the wall / 2
                     # in order to be centered on the boundary for the arena. This is necessary to
                     # ensure that the maximum X coordinate that robots can access is LESS than the
                     # upper boundary of physics engines incident along the east wall.
                     #
                     # I think this is a bug in ARGoS.
                     (".//arena/*[@id='wall_east']", "size", "{0:.9f}, {1:.9f}, 0.5".format(kWALL_WIDTH,
                                                                                            extent.y() + kWALL_WIDTH)),
                     (".//arena/*[@id='wall_east']/body",
                      "position",
                      "{0:.9f}, {1:.9f}, 0".format(extent.x() - kWALL_WIDTH / 2.0,
                                                   extent.y() / 2.0)),

                     (".//arena/*[@id='wall_west']", "size", "{0:.9f}, {1:.9f}, 0.5".format(kWALL_WIDTH,
                                                                                            extent.y() + kWALL_WIDTH)),
                     (".//arena/*[@id='wall_west']/body",
                      "position", "0, {0:.9f}, 0".format(extent.y() / 2.0)),

                     (".//arena_map/grid2D", "dims",
                      "{0}, {1}, 2".format(extent.x(), extent.y())),
                     (".//perception/grid2D", "dims",
                      "{0}, {1}, 2".format(extent.x(), extent.y())),

                     (".//convergence/positional_entropy",
                      "horizon",
                      "0:{0:.9f}".format(math.sqrt(extent.x() ** 2 + extent.y() ** 2))),
                     (".//convergence/positional_entropy",
                      "horizon_delta",
                      "{0:.9f}".format(math.sqrt(extent.x() ** 2 + extent.y() ** 2) / 10.0)),

                     # Finally, set camera positioning. Probably will not be used, but IF rendering
                     # is enabled we want to have the visualizations come out nicely. I assume a
                     # single camera is present.
                     (".//camera/placement",
                      "position", "{0:.9f}, {1:.9f}, {2:.9f}".format(extent.x() / 2.0,
                                                                     extent.y() / 2.0,
                                                                     max(extent.x(), extent.y()) * 2.0 / 3.0)),
                     (".//camera/placement",
                      "look_at", "{0:.9f}, {1:.9f}, 0".format(extent.x() / 2.0,
                                                              extent.y() / 2.0))
                     ])
                for extent in self.dimensions]

    def gen_tag_rmlist(self) -> list:
        return []

    def gen_tag_addlist(self) -> list:
        return []


class RectangularArenaTwoByOne(RectangularArena):
    """
    Define arenas that vary in size for each combination of dimensions in the specified X range and
    Y range, where the X dimension is always twices as large as the Y dimension.
    """

    def __init__(self, x_range: range, y_range: range) -> None:
        super().__init__([ArenaExtent((x, y, 1)) for x in x_range for y in y_range])


class SquareArena(RectangularArena):
    """
    Define arenas that vary in size for each combination of dimensions in the specified X range and
    Y range, where the X and y dimensions are always equal.
    """

    def __init__(self, sqrange: range) -> None:
        super().__init__([ArenaExtent((x, x, 1)) for x in sqrange])


__api__ = [
    'BaseVariable',
    'ArenaExtent',
    'kWALL_WIDTH',
    'RectangularArena',
    'RectangularArenaTwoByOne',
    'SquareArena',
]
