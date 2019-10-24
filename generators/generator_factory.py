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

import yaml
import os
import re
import generators.single_source
import generators.dual_source
import generators.quad_source
import generators.powerlaw
import generators.random
from generators.exp_input_generator import ExpInputGenerator


def BivarGeneratorFactory(controller, scenario, **kwargs):
    """
    Given a controller(generator), and a scenario(generator), construct a bivariate generator class
    that can be used for experiment generation.

    """

    def __init__(self, **kwargs):
        self.controller = controller
        self.scenario = scenario

    def generate(self):
        self.scenario.generate(self.controller.generate())

    return type('+'.join([controller.__class__.__name__, scenario.__class__.__name__]),
                (object,), {"__init__": __init__, "generate":
                            generate})(**kwargs)


def ScenarioGeneratorFactory(scenario, controller, **kwargs):
    """
    Creates a scenario generator using arbitrary arena dimensions and with an arbitrary
    controller.

    scenario(str): The name of scenario to run. Format of <dist type>.AxB
    controller(str): The name of controller to run. Formatof <depth>.<controller name>

    """
    abbrev_dict = {"SS": "single_source",
                   "DS": "dual_source",
                   "QS": "quad_source",
                   "PL": "powerlaw",
                   "RN": "random"}

    def __init__(self, **kwargs):
        res = re.search('[SDQLR][SSSLN]', scenario)
        assert res is not None

        abbrev = res.group(0)
        qualified_name = 'generators.' + abbrev_dict[abbrev] + '.' + abbrev + 'Generator'
        self.scenario_generator = eval(qualified_name)(controller=controller, **kwargs)

    def generate(self, xml_luigi):
        return self.scenario_generator.generate(xml_luigi)

    return type(scenario,
                (object,), {"__init__": __init__,
                            "generate": generate
                            })(**kwargs)


def ControllerGeneratorFactory(controller, config_root, **kwargs):
    """
    Creates a controller generator from the cmdline specification that exists in one of
    the configuration files.

    controller(str): Parsed controller identification string from the cmdline.
    config_root(str): Path to the YAML configuration root.
    """

    def __init__(self, **kwargs):
        ExpInputGenerator.__init__(self, **kwargs)
        self.config = yaml.load(open(os.path.join(config_root, 'controllers.yaml')))
        self.category, self.name = controller.split('.')

    def generate(self):
        """
        Generates all changes to the input file for the simulation (does not save)
        """
        xml_luigi = self.generate_common_defs()

        # Setup loop functions
        for t in self.config[self.category]['xml']['attr_change']:
            xml_luigi.attr_change(t[0],
                                  t[1],
                                  t[2],
                                  kwargs['cmdopts']['with_rendering'] is False)

        # Setup controller
        exists = False
        for controller in self.config[self.category]['controllers']:
            if controller['name'] == self.name:
                exists = True
                for t in controller['xml']['attr_change']:
                    xml_luigi.tag_change(t[0], t[1], t[2])

        assert exists, "FATAL: Controller {0} not found in controller YAML config".format(self.name)
        return xml_luigi

    return type(controller,
                (ExpInputGenerator,), {"__init__": __init__,
                                       "generate": generate
                                       })(**kwargs)
