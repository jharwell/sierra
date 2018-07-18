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


class SingleSourceGenerator(ExpInputGenerator):
    """
    Modifies simulation input file template for single source foraging:

    - Rectangular 2x1 arena
    - Single source block distribution
    - # blocks unspecified
    - # robots unspecified
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate(self):
        xml_helper = self.init_sim_defs()
        [xml_helper.set_attribute(a[0], a[1])
         for a in ev.arena_shape.RectangularArenaTwoByOne(x_range=[10],
                                                          y_range=[5]).gen_list()[0]]
        [xml_helper.set_attribute(a[0], a[1])
         for a in ev.block_distribution.TypeSingleSource().gen_list()[0]]

        [xml_helper.set_attribute(a[0], a[1])
         for a in ev.nest_pose("single_source", [(10, 5)]).gen_list()[0]]
        return xml_helper
