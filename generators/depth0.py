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


class BaseGenerator(ExpInputGenerator):

    """
    Generates simulation input common to all depth0 simulations.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_sim_defs(self):
        """
        Initialize sim defs common to all depth0 simulations (does nothing for now...)
        """
        xml_luigi = super().init_sim_defs()

        return xml_luigi

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save).
        """
        xml_luigi = self.init_sim_defs()
        return xml_luigi

    def generate_and_save(self):
        """
        Generates and saves input file for the simulation.
        """
        self._create_all_sim_inputs(self._generate_random_seeds(), self.init_sim_defs())


class StatefulGenerator(BaseGenerator):

    """
    Generates simulation inputs common to all stateful foraging experiments.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_sim_defs(self):
        """
        Initialize sim defs common to all stateful simulations.
        """
        xml_luigi = super().init_sim_defs()

        xml_luigi.tag_change(".//controllers", "__template__", "stateful_controller")
        xml_luigi.attribute_change(".//loop_functions", "label", "stateful_loop_functions")
        return xml_luigi

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save).
        """
        xml_luigi = self.init_sim_defs()
        return xml_luigi

    def generate_and_save(self):
        """
        Generates and saves input file for the simulation.
        """
        self._create_all_sim_inputs(self._generate_random_seeds(), self.init_sim_defs())


class StatelessGenerator(BaseGenerator):
    """
    Generates simulation inputs common to all stateless foraging experiments.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def init_sim_defs(self):
        """
        Initialize sim defs common to all stateless simulations.
        """
        xml_luigi = super().init_sim_defs()

        xml_luigi.tag_change(".//controllers", "__template__", "stateless_controller")
        xml_luigi.attribute_change(".//loop_functions", "label", "stateless_loop_functions")
        return xml_luigi

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save).
        """
        xml_luigi = self.init_sim_defs()
        return xml_luigi

    def generate_and_save(self):
        """
        Generates and saves input file for the simulation.
        """
        self._create_all_sim_inputs(self._generate_random_seeds(), self.init_sim_defs())
