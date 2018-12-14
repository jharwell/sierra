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
import generators.single_source
import generators.dual_source
import generators.quad_source
import generators.powerlaw
import generators.random
import generators.depth0
import generators.depth1
import generators.depth2


def GeneratorPairFactory(controller, scenario, **kwargs):
    """
    Given a controller(str), and a scenario(generator), construct a joint generator class that can
    be used for experiment generation.

    """

    def __init__(self, **kwargs):

        self.controller = eval(controller)(**kwargs)
        self.scenario = scenario

    def generate(self):
        self.scenario.generate(self.controller.generate())

    return type('+'.join([controller, scenario.__class__.__name__]),
                (object,), {"__init__": __init__, "generate":
                            generate})(**kwargs)


def ScenarioGeneratorFactory(scenario, controller, **kwargs):
    """
    Creates a scenario generator using arbitrary arena dimensions and with an arbitrary controller.

    scenario(str): The name of scenario to run.
    controller(str): The name of controller to run.

    """

    def __init__(self, **kwargs):
        self.scenario_changes = eval(scenario)(controller=controller,
                                               **kwargs)

    def generate(self, xml_luigi):
        return self.scenario_changes.generate(xml_luigi)

    arena_dim = kwargs["sim_opts"]["arena_dim"]
    return type(scenario + '{0}x{1}'.format(arena_dim[0], arena_dim[1]),
                (object,), {"__init__": __init__,
                            "generate": generate
                            })(**kwargs)
