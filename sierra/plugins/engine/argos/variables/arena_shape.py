# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Functionality for modifying/setting the size of the arena in ARGoS."""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.utils import ArenaExtent
from sierra.core.experiment import definition

WALL_WIDTH = 0.4


@implements.implements(IBaseVariable)
class ArenaShape:
    """Maps a list of desired arena dimensions sets of XML changes.

    This class is a base class which should (almost) never be used on its
    own. Instead, derived classes defined in this file should be used instead.

    Attributes:
        extents: List of arena extents.

    """

    def __init__(self, extents: list[ArenaExtent]) -> None:
        self.extents = extents
        self.attr_changes = []  # type: tp.List[definition.AttrChangeSet]

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        """Generate changes necessary setup ARGoS with the specified arena sizes."""
        if not self.attr_changes:
            for extent in self.extents:
                self.attr_changes.append(self._gen_chgs_for_extent(extent))

        return self.attr_changes

    def _gen_chgs_for_extent(self, extent: ArenaExtent) -> definition.AttrChangeSet:

        xsize = extent.xsize()
        ysize = extent.ysize()
        zsize = extent.zsize()

        chgs = definition.AttrChangeSet(
            definition.AttrChange(".//arena", "size", f"{xsize},{ysize},{zsize}"),
            definition.AttrChange(
                ".//arena",
                "center",
                "{:.9f},{:.9f},{}".format(xsize / 2.0, ysize / 2.0, zsize / 2.0),
            ),
        )

        # We restrict the places robots can spawn within the arena as follows:
        #
        # - Subtract width of the walls so that robots do not spawn inside walls
        #   (which ARGoS seems to allow?).
        #
        # - Subtract a little bit more so robots don't get into weird states by
        #   being near arena boundaries on the first timestep.
        #
        # - All robots start on the ground with Z=0.
        chgs.add(
            definition.AttrChange(
                ".//arena/distribute/position",
                "max",
                "{:.9f}, {:.9f}, 0".format(
                    xsize - 2.0 * WALL_WIDTH * 1.1, ysize - 2.0 * WALL_WIDTH * 1.1
                ),
            )
        )
        chgs.add(
            definition.AttrChange(
                ".//arena/distribute/position",
                "min",
                "{:.9f}, {:.9f}, 0".format(
                    2.0 * WALL_WIDTH * 1.1, 2.0 * WALL_WIDTH * 1.1
                ),
            )
        )

        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_north']",
                "size",
                "{:.9f}, {:.9f}, 0.5".format(xsize, WALL_WIDTH),
            )
        )

        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_north']/body",
                "position",
                "{:.9f}, {:.9f}, 0".format(xsize / 2.0, ysize),
            )
        )
        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_south']",
                "size",
                "{:.9f}, {:.9f}, 0.5".format(xsize, WALL_WIDTH),
            )
        )

        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_north']/body",
                "position",
                "{:.9f}, {:.9f}, 0".format(xsize / 2.0, ysize),
            )
        )
        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_south']",
                "size",
                "{:.9f}, {:.9f}, 0.5".format(xsize, WALL_WIDTH),
            )
        )
        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_south']/body",
                "position",
                "{:.9f}, 0, 0 ".format(xsize / 2.0),
            )
        )

        # East wall needs to have its X coordinate offset by the width of the
        # wall / 2 in order to be centered on the boundary for the arena. This
        # is necessary to ensure that the maximum X coordinate that robots can
        # access is LESS than the upper boundary of physics engines incident
        # along the east wall.
        #
        # I think this is a bug in ARGoS.
        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_east']",
                "size",
                "{:.9f}, {:.9f}, 0.5".format(WALL_WIDTH, ysize + WALL_WIDTH),
            )
        )
        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_east']/body",
                "position",
                "{:.9f}, {:.9f}, 0".format(xsize - WALL_WIDTH / 2.0, ysize / 2.0),
            )
        )

        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_west']",
                "size",
                "{:.9f}, {:.9f}, 0.5".format(WALL_WIDTH, ysize + WALL_WIDTH),
            )
        )
        chgs.add(
            definition.AttrChange(
                ".//arena/*[@id='wall_west']/body",
                "position",
                "0, {:.9f}, 0".format(ysize / 2.0),
            )
        )

        return chgs

    def gen_tag_rmlist(self) -> list[definition.ElementRmList]:
        return []

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        return []

    def gen_files(self) -> None:
        pass


__all__ = [
    "ArenaShape",
]
