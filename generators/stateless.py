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
import generators.powerlaw as pl
import generators.single_source as ss
import generators.random as rnd


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
        return xml_helper


class SS10x5Generator(BaseGenerator):

    """
    Modifies simulation input file template for single source stateless foraging in a small 10x5
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = ss.SSGenerator10x5(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class SS20x10Generator(BaseGenerator):

    """
    Modifies simulation input file template for single source stateless foraging in a 20x10
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = ss.SSGenerator20x10(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class SS40x20Generator(BaseGenerator):

    """
    Modifies simulation input file template for single source stateless foraging in a 40x20
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = ss.SSGenerator40x20(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class PL10x10Generator(BaseGenerator):

    """
    Modifies simulation input file template for powerlaw stateless foraging in a 10x10
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = pl.PLGenerator10x10(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class PL20x20Generator(BaseGenerator):

    """
    Modifies simulation input file template for powerlaw stateless foraging in a 20x20
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = pl.PLGenerator20x20(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class PL40x40Generator(BaseGenerator):

    """
    Modifies simulation input file template for powerlaw stateless foraging in a 40x40
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = pl.PLGenerator40x40(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class RND10x10Generator(BaseGenerator):

    """
    Modifies simulation input file template for powerlaw stateless foraging in a 10x10
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = rnd.RNDGenerator10x10(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class RND20x20Generator(BaseGenerator):

    """
    Modifies simulation input file template for powerlaw stateless foraging in a 20x20
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = rnd.RNDGenerator20x20(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)


class RND40x40Generator(BaseGenerator):

    """
    Modifies simulation input file template for powerlaw stateless foraging in a 40x40
    arena.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ss = rnd.RNDGenerator40x40(*args, **kwargs)

    def generate(self):
        xml_helper = self.ss.generate(super().generate())
        self._create_all_sim_inputs(self._generate_random_seeds(), xml_helper)
