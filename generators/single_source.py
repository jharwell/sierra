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


from generators.base_scenario_generator import BaseScenarioGenerator
import variables as ev


class SSGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for single source foraging.

    This includes:

    - Rectangular 2x1 arena
    - Single source block distribution

    Changes are *NOT* generated for the following:

    - # robots

    """

    def __init__(self, *args, **kwargs):
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim[0] == 2 * arena_dim[1],\
            "FATAL: SS distribution requires a 2x1 arena: xdim={0},ydim={1}".format(arena_dim[0],
                                                                                    arena_dim[1])

        self.generate_arena_shape(exp_def,
                                  ev.arena_shape.RectangularArenaTwoByOne(x_range=[arena_dim[0]],
                                                                          y_range=[arena_dim[1]]))

        # Generate and apply block distribution type definitions
        BaseScenarioGenerator.generate_block_dist(exp_def, ev.block_distribution.TypeSingleSource())

        # Generate and apply nest definitions
        BaseScenarioGenerator.generate_nest_pose(exp_def, arena_dim, "single_source")

        if "depth1" in self.controller:
            self.generate_static_cache(exp_def, arena_dim)
        if "depth2" in self.controller:
            BaseScenarioGenerator.generate_dynamic_cache(exp_def, arena_dim)

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        return exp_def
