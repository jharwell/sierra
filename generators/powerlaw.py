"""
 Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

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

from exp_input_generator import ExpInputGenerator
import exp_variables as ev


class PowerlawGenerator(ExpInputGenerator):

    """
    Modifies simulation input file template  for powerlaw stateless foraging:

    - Square arena
    - Powerlaw block distribution
    - # robots unspecified
    - # blocks unspecified
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate(self, xml_helper):
        [xml_helper.set_attribute(a[0], a[1])
         for a in ev.arena_shape.SquareArena(sqrange=[10]).gen_list()[0]]

        [xml_helper.set_attribute(a[0], a[1])
         for a in ev.block_distribution.TypePowerLaw().gen_list()[0]]

        [xml_helper.set_attribute(a[0], a[1])
         for a in ev.nest_pose("powerlaw", [(10, 10)]).gen_list()[0]]
        return xml_helper
