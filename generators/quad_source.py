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
                 exp_def_fname, sim_opts, controller):
        super().__init__(template_config_file, generation_root, exp_output_root,
                         exp_def_fname, sim_opts)
        self.controller = controller

    def generate(self, xml_luigi):
        # Generate and apply arena dimensions definitions, and write dimensions to file for later
        # retrieval.
        arena_dim = self.sim_opts["arena_dim"]
        shape = ev.arena_shape.SquareArena(sqrange=[arena_dim[0]])
        [xml_luigi.attribute_change(a[0], a[1], a[2]) for a in shape.gen_attr_changelist()[0]]

        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(shape.gen_attr_changelist()[0], f)

        rms = shape.gen_tag_rmlist()
        if len(rms):
            [xml_luigi.tag_remove(a) for a in rms[0]]

        # Generate and apply block distribution type definitions
        source = ev.block_distribution.TypeQuadSource()
        [xml_luigi.attribute_change(a[0], a[1], a[2]) for a in source.gen_attr_changelist()[0]]

        rms = source.gen_tag_rmlist()
        if len(rms):
            [xml_luigi.tag_remove(a) for a in rms[0]]

        # Generate and apply nest definitions
        nest_pose = ev.nest_pose.NestPose("quad_source", [arena_dim])
        [xml_luigi.attribute_change(a[0], a[1], a[2]) for a in nest_pose.gen_attr_changelist()[0]]
        rms = nest_pose.gen_tag_rmlist()
        if len(rms):
            [xml_luigi.tag_remove(a) for a in rms[0]]

        # Generate and apply physics engines definitions
        self.generate_physics_defs(xml_luigi)

        # Generate and apply # blocks definitions if configured
        if self.sim_opts['n_blocks'] is not None:
            self.generate_block_count_defs(xml_luigi)

        if "depth1" in self.controller:
            print("WARNING: QS incompatible with depth1 controllers--either 0 or > 1 caches are needed for reasonable results.")

        # Generate simulation input files now that all simulation changes have been made to the
        # template
        self.generate_inputs(xml_luigi)
