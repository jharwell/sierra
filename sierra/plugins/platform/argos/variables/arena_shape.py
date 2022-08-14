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
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.utils import ArenaExtent
from sierra.core.experiment import xml

kWALL_WIDTH = 0.4


@implements.implements(IBaseVariable)
class ArenaShape():

    """Maps a list of desired arena dimensions sets of XML changes.

    This class is a base class which should (almost) never be used on its
    own. Instead, derived classes defined in this file should be used instead.

    Attributes:

        extents: List of arena extents.

    """

    def __init__(self, extents: tp.List[ArenaExtent]) -> None:
        self.extents = extents
        self.attr_changes = []  # type: tp.List[xml.AttrChangeSet]

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        """Generate changes necessary setup ARGoS with the specified arena sizes.

        """
        if not self.attr_changes:
            for extent in self.extents:
                self.attr_changes.append(self._gen_chgs_for_extent(extent))

        return self.attr_changes

    def _gen_chgs_for_extent(self, extent: ArenaExtent) -> xml.AttrChangeSet:

        xsize = extent.xsize()
        ysize = extent.ysize()
        zsize = extent.zsize()

        chgs = xml.AttrChangeSet(xml.AttrChange(".//arena",
                                                "size",
                                                f"{xsize},{ysize},{zsize}"),
                                 xml.AttrChange(".//arena",
                                                "center",
                                                "{0:.9f},{1:.9f},{2}".format(xsize / 2.0,
                                                                             ysize / 2.0,
                                                                             zsize / 2.0)))

        # We restrict the places robots can spawn within the arena as follows:
        #
        # - Subtract width of the walls so that robots do not spawn inside walls
        #   (which ARGoS seems to allow?).
        #
        # - Subtract a little bit more so robots don't get into weird states by
        #   being near arena boundaries on the first timestep.
        #
        # - All robots start on the ground with Z=0.
        chgs.add(xml.AttrChange(".//arena/distribute/position",
                                "max",
                                "{0:.9f}, {1:.9f}, 0".format(
                                    xsize - 2.0 * kWALL_WIDTH * 1.1,
                                    ysize - 2.0 * kWALL_WIDTH * 1.1)
                                ))
        chgs.add(xml.AttrChange(".//arena/distribute/position",
                                "min",
                                "{0:.9f}, {1:.9f}, 0".format(
                                    2.0 * kWALL_WIDTH * 1.1,
                                    2.0 * kWALL_WIDTH * 1.1)
                                ))

        chgs.add(xml.AttrChange(".//arena/*[@id='wall_north']",
                                "size",
                                "{0:.9f}, {1:.9f}, 0.5".format(xsize,
                                                               kWALL_WIDTH)))

        chgs.add(xml.AttrChange(".//arena/*[@id='wall_north']/body",
                                "position",
                                "{0:.9f}, {1:.9f}, 0".format(xsize / 2.0, ysize)))
        chgs.add(xml.AttrChange(".//arena/*[@id='wall_south']",
                                "size",
                                "{0:.9f}, {1:.9f}, 0.5".format(xsize, kWALL_WIDTH)))

        chgs.add(xml.AttrChange(".//arena/*[@id='wall_north']/body",
                                "position",
                                "{0:.9f}, {1:.9f}, 0".format(xsize / 2.0, ysize)))
        chgs.add(xml.AttrChange(".//arena/*[@id='wall_south']",
                                "size",
                                "{0:.9f}, {1:.9f}, 0.5".format(xsize, kWALL_WIDTH)))
        chgs.add(xml.AttrChange(".//arena/*[@id='wall_south']/body",
                                "position",
                                "{0:.9f}, 0, 0 ".format(xsize / 2.0)))

        # East wall needs to have its X coordinate offset by the width of the
        # wall / 2 in order to be centered on the boundary for the arena. This
        # is necessary to ensure that the maximum X coordinate that robots can
        # access is LESS than the upper boundary of physics engines incident
        # along the east wall.
        #
        # I think this is a bug in ARGoS.
        chgs.add(xml.AttrChange(".//arena/*[@id='wall_east']",
                                "size",
                                "{0:.9f}, {1:.9f}, 0.5".format(kWALL_WIDTH,
                                                               ysize + kWALL_WIDTH)))
        chgs.add(xml.AttrChange(".//arena/*[@id='wall_east']/body",
                                "position",
                                "{0:.9f}, {1:.9f}, 0".format(xsize - kWALL_WIDTH / 2.0,
                                                             ysize / 2.0)))

        chgs.add(xml.AttrChange(".//arena/*[@id='wall_west']",
                                "size",
                                "{0:.9f}, {1:.9f}, 0.5".format(kWALL_WIDTH,
                                                               ysize + kWALL_WIDTH)))
        chgs.add(xml.AttrChange(".//arena/*[@id='wall_west']/body",
                                "position",
                                "0, {0:.9f}, 0".format(ysize / 2.0)))

        return chgs

    def gen_tag_rmlist(self) -> tp.List[xml.TagRmList]:
        return []

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        return []

    def gen_files(self) -> None:
        pass


__api__ = [
    'kWALL_WIDTH',
    'ArenaShape',
]
