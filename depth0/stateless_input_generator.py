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

from experiment_input_generator import ExperimentInputGenerator
from xml_helper import XMLHelper
import xml

class StatelessInputGenerator(ExperimentInputGenerator):

    """
    Generates simulation input for base/simple stateless foraging experiments.

    Extends ExperimentInputGenerator.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def generate(self):
        '''Generates and saves all the input files for all the experiments'''
        xml_helper = super().generate()

        # xml_helper.set_attribute("argos-configuration.controllers.__template__",
        #                          "stateless_foraging_controller")
        xml_helper.set_attribute("argos-configuration.loop_functions.label",
                                 "stateless_foraging_loop_functions")

        self._generate_all_sim_inputs(self._generate_random_seeds(), xml_helper)
        xml_helper.write()
        return xml_helper
