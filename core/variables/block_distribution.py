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
#
import math
import typing as tp

from core.variables.base_variable import IBaseVariable
from core.utils import ArenaExtent


class BaseDistribution(IBaseVariable):

    """
    Defines the type of distribution of objects in the arena.

    Attributes:
        dist_type: [single_source, dual_source, quad_source, powerlaw, random].
    """

    def __init__(self, dist_type: str) -> None:
        self.dist_type = dist_type
        self.attr_changes = []  # type: tp.List

    def gen_attr_changelist(self):
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified block distribution
        """
        if not self.attr_changes:
            self.attr_changes = [set([(".//arena_map/blocks/distribution",
                                       "dist_type",
                                       "{0}".format(self.dist_type))])]
        return self.attr_changes

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []


class SingleSourceDistribution(BaseDistribution):
    def __init__(self) -> None:
        super().__init__("single_source")


class DualSourceDistribution(BaseDistribution):
    def __init__(self) -> None:
        super().__init__("dual_source")


class QuadSourceDistribution(BaseDistribution):
    def __init__(self) -> None:
        super().__init__("quad_source")


class PowerLawDistribution(BaseDistribution):
    def __init__(self, arena_dim: ArenaExtent) -> None:
        super().__init__("powerlaw")
        self.arena_dim = arena_dim

    def gen_attr_changelist(self):
        r"""
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation for the powerlaw block distribution.

        2020/7/29: As a first guess, I've set the following parameters:

        - Min :math:`2^X` power to 2
        - Max 2^X power to :math:`\sqrt{X}`
        - # clusters to :math:`X`

        where :math:`X` is the arena dimension (assumed to be square). Not all of the clusters will
        be able to be placed in all likelihood for many arena layouts, but this is a good
        starting point.

        """
        changes = super().gen_attr_changelist()
        for c in changes:
            c |= set([(".//arena_map/blocks/distribution/powerlaw",
                       "pwr_min",
                       "{0}".format(2)),
                      (".//arena_map/blocks/distribution/powerlaw",
                       "pwr_max",
                       "{0}".format(math.ceil(math.sqrt(self.arena_dim.x())))),
                      (".//arena_map/blocks/distribution/powerlaw",
                       "n_clusters",
                       "{0}".format(self.arena_dim.x()))])
        return changes


class RandomDistribution(BaseDistribution):
    def __init__(self) -> None:
        super().__init__("random")


class Quantity(IBaseVariable):

    """
    Defines the # of blocks in the arena. An equal # of all block types are created (# blocks/ #
    block types).

    Attributes:
      blocks_list: List of block quantities to be distributed.
    """

    def __init__(self, blocks_list: tp.List) -> None:
        self.blocks_list = blocks_list

    def gen_attr_changelist(self):
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified # blocks.
        """
        return [set([
            (".//arena_map/blocks/distribution/manifest", "n_cube", "{0}".format(int(n / 2.0))),
            (".//arena_map/blocks/distribution/manifest", "n_ramp", "{0}".format(int(n / 2.0)))]) for n in self.blocks_list]

    def gen_tag_addlist(self):
        return []

    def gen_tag_rmlist(self):
        return []


__api__ = [
    'BaseDistribution',
    'SingleSourceDistribution',
    'DualSourceDistribution',
    'QuadSourceDistribution',
    'PowerLawDistribution',
    'RandomDistribution',
    'Quantity',
]
