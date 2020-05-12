# Copyright 2020 John Harwell, All rights reserved.
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

from core.variables.base_variable import BaseVariable
from core.utils import ArenaExtent as ArenaExtent


class NestPose(BaseVariable):

    """
    Defines the position/size of the nest based on construction target dimensions. Multiple nests
    can be specified for SILICON construction.

    Attributes:
      extents: List of construction target extents to generate nest poses for.
    """

    def __init__(self, extents: tp.List[ArenaExtent]):
        self.extents = extents

    def gen_attr_changelist(self):
        return []

    def gen_tag_rmlist(self):
        return [set([(".//arena_map", "nests")])]

    def gen_tag_addlist(self):
        """
        Generate list of sets of XML tag adds necessary to make to the input file to correctly set
        up the simulation for the specified construction targets.

        """
        adds = [(".//arena_map", "nests", {})]
        nests = [(".//arena_map/nests",
                  "nest",
                  {
                      "dims": "{0}, {1}".format(s.xmax * 0.1, s.ymax * 0.8),
                      "center": "{0}, {1}".format(s.xmax * 0.1, s.ymax / 2.0)
                  }) for s in self.extents]
        adds.extend(nests)
        return [adds]
