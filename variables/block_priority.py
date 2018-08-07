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

kMinPriority = 1
kMaxPriority = 10


class Priority(BaseVariable):

    """
    Defines the priority for each type of block in the arena.

    Attributes:
      priorities(list): List of tuples specifying the priorities for each type of block for a set of
      simulations. Each tuple is (cube, ramp) priorities.
    """

    def __init__(self, priorities):
        self.priorities = priorities

    def gen_attr_changelist(self):
        """
        Generate a list of sets of changes necessary to make to the input file to correctly set up
        the simulation with the specified block priorities.
        """
        return [set([
            ("occupancy_grid.block_priorities.cube", "{0}".format(n[0])),
            ("occupancy_grid.block_priorities.ramp", "{0}".format(n[1]))]) for n in self.priorities]


class StaticCube(Priority):
    """Gives a higher priority to cube blocks than ramp blocks that does not change with time."""

    def __init__(self):
        super().__init__([(x, kMinPriority) for x in range(kMinPriority, kMaxPriority + 1)])


class StaticRamp(Priority):
    """Gives a higher priority to ramp blocks than cube blocks that does not change with time."""

    def __init__(self):
        super().__init__([(kMinPriority, x) for x in range(kMinPriority, kMaxPriority + 1)])
