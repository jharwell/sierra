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
from core.variables.base_variable import IBaseVariable
from core.utils import ArenaExtent
from core.vector import Vector3D

kWALL_WIDTH = 0.4


class RectangularArena(IBaseVariable):

    """
    Maps a list of desired arena dimensions specified in (X,Y) tuples to a list of sets of changes
    from a necessary to modify the arena dimensions to realize each desired area size. This class is
    a base class which should (almost) never be used on its own. Instead, derived classes defined in
    this file should be used instead.

    Attributes:
        extents: List of (X, Y, Z) tuples of arena size.
    """

    def __init__(self, extents: tp.List[ArenaExtent]) -> None:
        self.extents = extents
        self.attr_changes = []  # type: tp.List

    def gen_attr_changelist(self) -> list:
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation with the specified area size/shape.
        """
        if not self.attr_changes:
            self.attr_changes = [set([(".//arena",
                                       "size",
                                       "{0}, {1}, {2}".format(extent.xspan(), extent.yspan(), extent.zspan())),
                                      (".//arena",
                                       "center",
                                       "{0:.9f},{1:.9f},1".format(extent.xspan() / 2.0, extent.yspan() / 2.0)),

                                      # We restrict the places robots can spawn within the arena as
                                      # follows:
                                      #
                                      # - Subtract width of the walls so that robots do not spawn
                                      #   inside walls (which ARGoS seems to allow?).
                                      #
                                      # - Subtract a little bit more so robots don't get into weird
                                      #   states by being near arena boundaries on the first
                                      #   timestep.
                                      #
                                      # - All robots start on the ground with Z=0.
                                      (".//arena/distribute/position",
                                       "max",
                                       "{0:.9f}, {1:.9f}, 0".format(extent.xspan() - 2.0 * kWALL_WIDTH - 2.0,
                                                                    extent.yspan() - 2.0 * kWALL_WIDTH - 2.0)),
                                      (".//arena/distribute/position",
                                       "min",
                                       "{0:.9f}, {1:.9f}, 0".format(2.0 * kWALL_WIDTH + 2.0, 2.0 * kWALL_WIDTH + 2.0)),

                                      (".//arena/*[@id='wall_north']",
                                       "size",
                                       "{0:.9f}, {1:.9f}, 0.5".format(extent.xspan(), kWALL_WIDTH)),

                                      (".//arena/*[@id='wall_north']/body",
                                       "position", "{0:.9f}, {1:.9f}, 0".format(extent.xspan() / 2.0, extent.yspan())),
                                      (".//arena/*[@id='wall_south']",
                                       "size",
                                       "{0:.9f}, {1:.9f}, 0.5".format(extent.xspan(), kWALL_WIDTH)),
                                      (".//arena/*[@id='wall_south']/body",
                                       "position",
                                       "{0:.9f}, 0, 0 ".format(extent.xspan() / 2.0)),

                                      # East wall needs to have its X coordinate offset by the width
                                      # of the wall / 2 in order to be centered on the boundary for
                                      # the arena. This is necessary to ensure that the maximum X
                                      # coordinate that robots can access is LESS than the upper
                                      # boundary of physics engines incident along the east wall.
                                      #
                                      # I think this is a bug in ARGoS.
                                      (".//arena/*[@id='wall_east']",
                                       "size",
                                       "{0:.9f}, {1:.9f}, 0.5".format(kWALL_WIDTH,
                                                                      extent.yspan() + kWALL_WIDTH)),
                                      (".//arena/*[@id='wall_east']/body",
                                       "position",
                                       "{0:.9f}, {1:.9f}, 0".format(extent.xspan() - kWALL_WIDTH / 2.0,
                                                                    extent.yspan() / 2.0)),

                                      (".//arena/*[@id='wall_west']",
                                       "size",
                                       "{0:.9f}, {1:.9f}, 0.5".format(kWALL_WIDTH,
                                                                      extent.yspan() + kWALL_WIDTH)),
                                      (".//arena/*[@id='wall_west']/body",
                                       "position",
                                       "0, {0:.9f}, 0".format(extent.yspan() / 2.0)),

                                      (".//arena_map/grid2D",
                                       "dims",
                                       "{0}, {1}, 2".format(extent.xspan(), extent.yspan())),
                                      (".//perception/grid2D", "dims",
                                       "{0}, {1}, 2".format(extent.xspan(), extent.yspan())),

                                      (".//convergence/positional_entropy",
                                       "horizon",
                                       "0:{0:.9f}".format(math.sqrt(extent.xspan() ** 2 + extent.yspan() ** 2))),
                                      (".//convergence/positional_entropy",
                                       "horizon_delta",
                                       "{0:.9f}".format(math.sqrt(extent.xspan() ** 2 + extent.yspan() ** 2) / 10.0)),
                                      ])
                                 for extent in self.extents]
        return self.attr_changes

    def gen_tag_rmlist(self) -> list:
        return []

    def gen_tag_addlist(self) -> list:
        return []


class RectangularArenaTwoByOne(RectangularArena):
    """
    Define arenas that vary in size for each combination of extents in the specified X range and
    Y range, where the X dimension is always twices as large as the Y dimension.
    """

    def __init__(self, x_range: range, y_range: range, z: int) -> None:
        super().__init__([ArenaExtent(Vector3D(x, y, z)) for x in x_range for y in y_range])


class SquareArena(RectangularArena):
    """
    Define arenas that vary in size for each combination of extents in the specified X range and
    Y range, where the X and y extents are always equal.
    """

    def __init__(self, sqrange: range, z: int) -> None:
        super().__init__([ArenaExtent(Vector3D(x, x, z)) for x in sqrange])


__api__ = [
    'kWALL_WIDTH',
    'RectangularArena',
    'RectangularArenaTwoByOne',
    'SquareArena',
]
