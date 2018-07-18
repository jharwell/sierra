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
import powerlaw
import single_source


class BaseGenerator(ExpInputGenerator):

    """
    Generates simulation input for base/simple stateless foraging experiments.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_sim_defs(self):
        """
        Initialize sim defs common to all stateless simulations.
        """
        xml_helper = super().init_sim_defs()

        xml_helper.set_tag("argos-configuration.controllers.__template__",
                           "stateless_foraging_controller")
        xml_helper.set_attribute("argos-configuration.loop_functions.label",
                                 "stateless_foraging_loop_functions")
        return xml_helper

    def generate(self):
        """
        Generates and saves all the input files for all the experiments.
        """
        xml_helper = self.init_sim_defs()
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)
        return xml_helper


class PowerlawGenerator(BaseGenerator):

    """
    Modifies simulation input file template for powerlaw stateless foraging.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.powerlaw = powerlaw.PowerlawGenerator(*args, **kwargs)

    def generate(self):
        xml_helper = self.powerlaw.generate(self.init_sim_defs())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class SingleSourceGenerator(BaseGenerator):

    """
    Modifies simulation input file template for single source stateless foraging.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.powerlaw = single_source.SingleSourceGenerator(*args, **kwargs)

    def generate(self):
        xml_helper = self.powerlaw.generate(self.init_sim_defs())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)
