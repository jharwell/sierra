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


class QSGenerator(ExpInputGenerator):
    """
    Modifies simulation input file template for dual source foraging:

    - Square arena
    - Quad source block distribution
    - # blocks unspecified
    - # robots unspecified

    Attributes:
      controller(str): The controller used for the experiment.
    """

    def __init__(self, template_config_file, generation_root, exp_output_root,
                 n_sims, n_threads, tsetup, controller, exp_def_fname, dimensions):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         n_sims, n_threads, tsetup, exp_def_fname, dimensions)
        self.controller = controller

    def generate(self, xml_helper):
        shape = ev.arena_shape.SquareArena(sqrange=[self.dimensions[0]])
        [xml_helper.set_attribute(a[0], a[1]) for a in shape.gen_attr_changelist()[0]]

        # Write arena dimensions info to file for later retrieval
        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(shape.gen_attr_changelist()[0], f)

        rms = shape.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        source = ev.block_distribution.TypeQuadSource()
        [xml_helper.set_attribute(a[0], a[1]) for a in source.gen_attr_changelist()[0]]

        rms = source.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        nest_pose = ev.nest_pose.NestPose("quad_source", [self.dimensions])
        [xml_helper.set_attribute(a[0], a[1]) for a in nest_pose.gen_attr_changelist()[0]]
        rms = nest_pose.gen_tag_rmlist()
        if len(rms):
            [xml_helper.remove_element(a) for a in rms[0]]

        if "depth1" in self.controller:
            print("WARNING: QS incompatible with depth1 controllers--either 0 or > 1 caches are needed for reasonable results.")
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)
