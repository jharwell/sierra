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

from generators.exp_input_generator import ExpInputGenerator
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

    def generate(self, xml_helper):
        shape = ev.arena_shape.RectangularArenaTwoByOne(x_range=[10],
                                                        y_range=[5])
        [xml_helper.set_attribute(a[0], a[1]) for a in shape.gen_attr_changelist()[0]]
        rms = shape.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        source = ev.block_distribution.TypeSingleSource()
        [xml_helper.set_attribute(a[0], a[1]) for a in source.gen_attr_changelist()[0]]

        rms = source.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        nest_pose = ev.nest_pose.NestPose("single_source", [(10, 5)])
        [xml_helper.set_attribute(a[0], a[1]) for a in nest_pose.gen_attr_changelist()[0]]
        rms = nest_pose.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        return xml_helper
