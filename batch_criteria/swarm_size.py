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

from base_criteria import BaseCriteria


class SwarmSize(BaseCriteria):

    """
    Defines a range of swarm sizes to test with

    Attributes:
      size_list(list): List of integer sizes to test with.
    """

    def __init__(self, size_list):
        self.size_list = size_list

    def gen_list(self):
        """Generate list of lists criteria for input into batch pipeline."""
        return [[("arena.entity.quantity", s)] for s in self.size_list]


class Linear1024(SwarmSize):
    def __init__(self):
        super().__init__([x for x in range(4, 1028, 4)])


class Linear512(SwarmSize):
    def __init__(self):
        super().__init__([x for x in range(4, 516, 4)])


class Linear256(SwarmSize):
    def __init__(self):
        super().__init__([x for x in range(4, 260, 4)])


class Linear64(SwarmSize):
    def __init__(self):
        super().__init__([x for x in range(4, 68, 4)])


class Log1024(SwarmSize):
    def __init__(self):
        super().__init__([x ** 2 for x in range(2, 11)])


class Log256(SwarmSize):
    def __init__(self):
        super().__init__([x ** 2 for x in range(2, 10)])


class Log128(SwarmSize):
    def __init__(self):
        super().__init__([x ** 2 for x in range(2, 8)])


class Log64(SwarmSize):
    def __init__(self):
        super().__init__([x ** 2 for x in range(2, 7)])
