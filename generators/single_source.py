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
import variables as ev
import pickle


class SSBaseGenerator(ExpInputGenerator):
    """
    Modifies simulation input file template for single source foraging:

    - Rectangular 2x1 arena
    - Single source block distribution
    - # blocks unspecified
    - # robots unspecified

    Attributes:
      dimension(tuple): X,Y dimensions of the rectangular arena.
      controller(str): The controller used for the experiment.
    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads, dimension, tsetup, controller, exp_def_fname):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads, tsetup, exp_def_fname)
        self.dimension = dimension
        self.controller = controller

    def generate(self, xml_helper):
        shape = ev.arena_shape.RectangularArenaTwoByOne(x_range=[self.dimension[0]],
                                                        y_range=[self.dimension[1]])
        [xml_helper.set_attribute(a[0], a[1]) for a in shape.gen_attr_changelist()[0]]

        # Write arena dimension info to file for later retrieval
        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(shape.gen_attr_changelist()[0], f)

        rms = shape.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        source = ev.block_distribution.TypeSingleSource()
        [xml_helper.set_attribute(a[0], a[1]) for a in source.gen_attr_changelist()[0]]

        rms = source.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        nest_pose = ev.nest_pose.NestPose("single_source", [self.dimension])
        [xml_helper.set_attribute(a[0], a[1]) for a in nest_pose.gen_attr_changelist()[0]]
        rms = nest_pose.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        if "depth1" in self.controller:
            cache = ev.static_cache.StaticCache([2], [self.dimension])
            [xml_helper.set_attribute(a[0], a[1]) for a in cache.gen_attr_changelist()[0]]
            rms = cache.gen_tag_rmlist()
            if len(rms):
                [xml_helper.remove_element(a) for a in rms[0]]
        return xml_helper


class SS12x6(SSBaseGenerator):

    """
    Modifies simulation input file template for single source foraging in a 12x6 arena.

    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads, tsetup, controller, exp_def_fname):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads, (10, 5), tsetup, controller, exp_def_fname)

    def generate(self, xml_helper):
        self._create_all_sim_inputs(self._generate_random_seeds(), super().generate(xml_helper))


class SS24x12(SSBaseGenerator):

    """
    Modifies simulation input file template for single source foraging in a 24x12 arena.

    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads, tsetup, controller, exp_def_fname):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads, (20, 10), tsetup, controller, exp_def_fname)

    def generate(self, xml_helper):
        self._create_all_sim_inputs(self._generate_random_seeds(), super().generate(xml_helper))


class SS48x24(SSBaseGenerator):

    """
    Modifies simulation input file template for single source foraging in a 48x24 arena.

    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads, tsetup, controller, exp_def_fname):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads, (40, 20), tsetup, controller, exp_def_fname)

    def generate(self, xml_helper):
        self._create_all_sim_inputs(self._generate_random_seeds(), super().generate(xml_helper))
