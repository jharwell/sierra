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

from variables.base_variable import BaseVariable
from variables.arena_shape import RectangularArena
from variables.block_distribution import TypeRandom, TypeSingleSource
from variables.swarm_density_parser import SwarmDensityParser


def Calculate(n_robots, arena_x, arena_y):
    """Calculate the swarm density \rho, from Hamann2013."""
    return int(arena_x) * int(arena_y) / n_robots


class ConstantDensity(BaseVariable):

    """
    Defines a range of swarm and arena sizes to test with such that the arena ratio is always the
    same. Does not change the # blocks/block manifest.

    Attributes:
      target_density(list): The target swarm density.
      dimensions(): List of (X,Y) dimensions to use.
      dist_type(str): The type of block distribution to use. Can be "single_source" or "random".
    """
    kRect2x1Dims = [(x, int(x / 2)) for x in range(12, 72, 12)]

    def __init__(self, target_density, dimensions, dist_type):
        self.target_density = target_density

        self.changes = RectangularArena(dimensions).gen_attr_changelist()

        for changeset in self.changes:
            for c in eval(dist_type)().gen_attr_changelist():
                changeset = changeset | c

    def gen_attr_changelist(self):
        """
        Generate list of sets of changes to input file to set the # robots for a set of arena
        sizes such that the swarm density is constant. Robots are approximated as point masses.
        """
        for changeset in self.changes:
            for c in changeset:
                if c[0] == ".//arena" and c[1] == "size":
                    x, y, z = c[2].split(',')
                    # ARGoS won't start if there are 0 robots, so you always need to put at least
                    # 1.
                    n_robots = max(1, (int(x) * int(y)) * (self.target_density / 100.0))
                    changeset.add((".//arena/distribute/entity", "quantity", str(int(n_robots))))
                    break
        return self.changes

    def gen_tag_rmlist(self):
        return []

    def gen_tag_addlist(self):
        return []


def Factory(criteria_str):
    """
    Creates variance classes from the command line definition of batch criteria.
    """
    attr = SwarmDensityParser().parse(criteria_str.split(".")[1])

    if "TypeSingleSource" == attr["block_dist_type"]:
        dims = ConstantDensity.kRect2x1Dims

    def __init__(self):
        ConstantDensity.__init__(self,
                                 attr["target_density"],
                                 dims,
                                 attr["block_dist_type"])

    return type(criteria_str,
                (ConstantDensity,),
                {"__init__": __init__})
