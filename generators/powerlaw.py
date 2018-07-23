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

from generators.exp_input_generator import ExpInputGenerator
import exp_variables as ev


class PLBaseGenerator(ExpInputGenerator):

    """
    Modifies simulation input file template for powerlaw foraging:

    - Square arena
    - Powerlaw block distribution
    - # robots unspecified
    - # blocks unspecified

    Attributes:
      dimension(int): dimensions of the square arena.
    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads, dimension):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads)
        self.dimension = dimension

    def generate(self, xml_helper):
        shape = ev.arena_shape.SquareArena(sqrange=[self.dimension])
        [xml_helper.set_attribute(a[0], a[1]) for a in shape.gen_attr_changelist()[0]]

        rms = shape.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        source = ev.block_distribution.TypePowerLaw()
        [xml_helper.set_attribute(a[0], a[1]) for a in source.gen_attr_changelist()[0]]
        rms = source.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        nest_pose = ev.nest_pose.NestPose("powerlaw", [(self.dimension, self.dimension)])
        [xml_helper.set_attribute(a[0], a[1]) for a in nest_pose.gen_attr_changelist()[0]]
        rms = nest_pose.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        return xml_helper


class PL10x10(PLBaseGenerator):

    """
    Modifies simulation input file template for powerlaw foraging in a 10x10 arena.

    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads, 10)

    def generate(self, xml_helper):
        self._create_all_sim_inputs(self._generate_random_seeds(), super().generate(xml_helper))


class PL20x20(PLBaseGenerator):

    """
    Modifies simulation input file template for powerlaw foraging in a 20x20 arena.

    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads, 20)

    def generate(self, xml_helper):
        self._create_all_sim_inputs(self._generate_random_seeds(), super().generate(xml_helper))


class PL40x40(PLBaseGenerator):

    """
    Modifies simulation input file template for powerlaw foraging in a 40x40 arena.

    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads, 40)

    def generate(self, xml_helper):
        self._create_all_sim_inputs(self._generate_random_seeds(), super().generate(xml_helper))
