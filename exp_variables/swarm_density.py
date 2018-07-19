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

from exp_variables.base_variable import BaseVariable
from exp_variables.arena_shape import SquareArena


class ConstantDensity(BaseVariable):

    """
    Defines a range of swarm and arena sizes to test with such that the arena ratio is always the
    same. Sets arena dimensions to be square.

    Attributes:
      target_density(list): The target swarm density.
    """

    def __init__(self, target_density):
        self.sqrange = range(10, 110, 10)
        self.target_density = target_density
        self.changes = SquareArena(sqrange=self.sqrange).gen_attr_changelist()

    def gen_attr_changelist(self):
        """
        Generate list of sets of changes to input file to set the # robots for a set of arena
        sizes such that the swarm density is constant. Robots are approximated as point masses, an
        assumption that should be valid as long as the environment is large compared to the size of
        a robot.
        """
        for changeset in self.changes:
            for c in changeset:
                if c[0] == "arena.size":
                    x, y, z = c[1].split(',')
                    n_robots = (int(x) * int(y)) * (self.target_density / 100.0)
                    changeset.add(("arena.entity.quantity", int(n_robots)))
                    break
        return self.changes

    def gen_tag_rmlist(self):
        return []


class ConstantDensity2p0(ConstantDensity):
    def __init__(self):
        super().__init__(2.0)


class ConstantDensity2p5(ConstantDensity):
    def __init__(self):
        super().__init__(2.5)


class ConstantDensity3p0(ConstantDensity):
    def __init__(self):
        super().__init__(3.0)


class ConstantDensity3p5(ConstantDensity):
    def __init__(self):
        super().__init__(3.5)


class ConstantDensity4p0(ConstantDensity):
    def __init__(self):
        super().__init__(4.0)


class ConstantDensity4p5(ConstantDensity):
    def __init__(self):
        super().__init__(4.5)


class ConstantDensity5p0(ConstantDensity):
    def __init__(self):
        super().__init__(5.0)
