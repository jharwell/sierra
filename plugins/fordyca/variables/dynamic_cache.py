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

from core.variables.base_variable import BaseVariable
from core.utils import ArenaExtent as ArenaExtent


class DynamicCache(BaseVariable):

    """
    Defines the size and capacity of a dynamic cache to test with. Only really applicable to single
    source foraging scenarios, but will work with only types as well.

    Attributes:
        extents: List of the extents within the arena to generate definitions for.
    """

    def __init__(self, extents: tp.List[ArenaExtent]):
        self.extents = extents

    def gen_attr_changelist(self):
        """
        Generate list of sets of changes necessary to make to the input file to correctly set up the
        simulation for the list of static cache sizes specified in constructor.

        - Disables dynamic caches
        - Enables static caches
        """
        return [set([
            (".//loop_functions/caches/dynamic", "enable", "true"),
            (".//loop_functions/caches/static", "enable", "false"),
            (".//loop_functions/caches/dynamic", "min_dist", "{0}".format(min(e.xmax * 0.20,
                                                                              e.ymax * 0.20))),

            (".//loop_functions/caches", "dimension", "{0}".format(max(e.xmax * 0.20,
                                                                       e.ymax * 0.20))),

            # Set to dimensions of cache to ensure that caches will not be created such that they
            # overlap
            (".//cache_sel_matrix", "cache_prox_dist", "{0}".format(max(e.xmax * 0.20,
                                                                        e.ymax * 0.20))),

            (".//cache_sel_matrix", "nest_prox_dist", "{0}".format(max(e.xmax * 0.25,
                                                                       e.ymax * 0.25))),

            (".//cache_sel_matrix", "block_prox_dist", "{0}".format(max(e.xmax * 0.20,
                                                                        e.ymax * 0.20))),

            (".//cache_sel_matrix", "site_xrange", "{0}:{1}".format(max(e.xmax * 0.20,
                                                                        e.ymax * 0.20) / 2.0,
                                                                    e.xmax - max(e.xmax * 0.20,
                                                                                 e.ymax * 0.20) / 2.0)),
            (".//cache_sel_matrix", "site_yrange", "{0}:{1}".format(max(e.xmax * 0.20,
                                                                        e.ymax * 0.20) / 2.0,
                                                                    e.ymax - max(e.xmax * 0.20,
                                                                                 e.ymax * 0.20) / 2.0)),
        ]) for e in self.extents]

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []
