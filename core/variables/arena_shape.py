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

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from core.variables.base_variable import IBaseVariable
from core.utils import ArenaExtent
from core.xml_luigi import XMLAttrChange, XMLAttrChangeSet, XMLTagRmList, XMLTagAddList

kWALL_WIDTH = 0.4


@implements.implements(IBaseVariable)
class ArenaShape():

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
        self.attr_changes = []  # type: tp.List[XMLAttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation with the specified arena.
        """
        if not self.attr_changes:
            for extent in self.extents:
                chgs = XMLAttrChangeSet(XMLAttrChange(".//arena",
                                                      "size",
                                                      "{0}, {1}, {2}".format(extent.xsize(),
                                                                             extent.ysize(),
                                                                             extent.zsize())),
                                        XMLAttrChange(".//arena",
                                                      "center",
                                                      "{0:.9f},{1:.9f},1".format(extent.xsize() / 2.0,
                                                                                 extent.ysize() / 2.0)),

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
                                        XMLAttrChange(".//arena/distribute/position",
                                                      "max",
                                                      "{0:.9f}, {1:.9f}, 0".format(extent.xsize() - 2.0 * kWALL_WIDTH - 2.0,
                                                                                   extent.ysize() - 2.0 * kWALL_WIDTH - 2.0)),
                                        XMLAttrChange(".//arena/distribute/position",
                                                      "min",
                                                      "{0:.9f}, {1:.9f}, 0".format(2.0 * kWALL_WIDTH + 2.0, 2.0 * kWALL_WIDTH + 2.0)),

                                        XMLAttrChange(".//arena/*[@id='wall_north']",
                                                      "size",
                                                      "{0:.9f}, {1:.9f}, 0.5".format(extent.xsize(), kWALL_WIDTH)),

                                        XMLAttrChange(".//arena/*[@id='wall_north']/body",
                                                      "position", "{0:.9f}, {1:.9f}, 0".format(extent.xsize() / 2.0, extent.ysize())),
                                        XMLAttrChange(".//arena/*[@id='wall_south']",
                                                      "size",
                                                      "{0:.9f}, {1:.9f}, 0.5".format(extent.xsize(), kWALL_WIDTH)),
                                        XMLAttrChange(".//arena/*[@id='wall_south']/body",
                                                      "position",
                                                      "{0:.9f}, 0, 0 ".format(extent.xsize() / 2.0)),

                                        # East wall needs to have its X coordinate offset by the width
                                        # of the wall / 2 in order to be centered on the boundary for
                                        # the arena. This is necessary to ensure that the maximum X
                                        # coordinate that robots can access is LESS than the upper
                                        # boundary of physics engines incident along the east wall.
                                        #
                                        # I think this is a bug in ARGoS.
                                        XMLAttrChange(".//arena/*[@id='wall_east']",
                                                      "size",
                                                      "{0:.9f}, {1:.9f}, 0.5".format(kWALL_WIDTH,
                                                                                     extent.ysize() + kWALL_WIDTH)),
                                        XMLAttrChange(".//arena/*[@id='wall_east']/body",
                                                      "position",
                                                      "{0:.9f}, {1:.9f}, 0".format(extent.xsize() - kWALL_WIDTH / 2.0,
                                                                                   extent.ysize() / 2.0)),

                                        XMLAttrChange(".//arena/*[@id='wall_west']",
                                                      "size",
                                                      "{0:.9f}, {1:.9f}, 0.5".format(kWALL_WIDTH,
                                                                                     extent.ysize() + kWALL_WIDTH)),
                                        XMLAttrChange(".//arena/*[@id='wall_west']/body",
                                                      "position",
                                                      "0, {0:.9f}, 0".format(extent.ysize() / 2.0)))
                self.attr_changes.append(chgs)

        return self.attr_changes

    def gen_tag_rmlist(self) -> tp.List[XMLTagRmList]:
        return []

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        return []


__api__ = [
    'kWALL_WIDTH',
    'ArenaShape',
]
