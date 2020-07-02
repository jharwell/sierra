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

import os
import re
import logging
import yaml

from core.xml_luigi import XMLLuigi


def joint_generator_create(controller, scenario):
    """
    Given a controller(generator), and a scenario(generator), construct a joint generator class
    that can be used for experiment generation.

    """

    def __init__(self) -> None:
        self.controller = controller
        self.scenario = scenario

    def generate(self):
        exp_def = self.scenario.generate()
        return self.controller.generate(exp_def)

    return type('+'.join([controller.__class__.__name__, scenario.__class__.__name__]),
                (object,), {"__init__": __init__, "generate":
                            generate})()


def scenario_generator_create(scenario, controller, **kwargs):
    """
    Creates a scenario generator using arbitrary arena dimensions and with an arbitrary
    controller.
    """

    def __init__(self, **kwargs) -> None:
        res = re.search('[SDQLR][SSSLN]', scenario)
        abbrev = res.group(0)
        cmdopts = kwargs['cmdopts']
        try:
            path = 'plugins.{0}.generators.scenario_generators'.format(cmdopts['plugin'])
            module = __import__(path, fromlist=["*"])
        except ModuleNotFoundError:
            logging.exception("module %s must exist!", path)
            raise

        self.scenario_generator = getattr(module,
                                          abbrev + 'Generator')(controller=controller,
                                                                **kwargs)

    def generate(self):
        return self.scenario_generator.generate()

    return type(scenario,
                (object,), {"__init__": __init__,
                            "generate": generate
                            })(**kwargs)


def controller_generator_create(controller, config_root, cmdopts):
    """
    Creates a controller generator from the cmdline specification that exists in one of
    the configuration files.
    """

    def __init__(self) -> None:
        self.config = yaml.load(open(os.path.join(config_root, 'controllers.yaml')),
                                yaml.FullLoader)
        self.category, self.name = controller.split('.')

    def generate(self, exp_def: XMLLuigi):
        """
        Generates all changes to the input file for the simulation (does not save)
        """
        # Setup loop functions
        for t in self.config[self.category]['xml']['attr_change']:
            exp_def.attr_change(t[0],
                                t[1],
                                t[2],
                                cmdopts['argos_rendering'] is False)

        # Setup controller
        exists = False
        for controller in self.config[self.category]['controllers']:
            if controller['name'] == self.name:
                exists = True
                for t in controller['xml']['attr_change']:
                    exp_def.tag_change(t[0], t[1], t[2])

        assert exists, \
            "FATAL: '{0}' not found in controller YAML config under category '{1}'".format(self.name,
                                                                                           self.category)
        return exp_def

    return type(controller,
                (object,), {"__init__": __init__,
                            "generate": generate
                            })()


__api__ = [
    'joint_generator_create',
    'scenario_generator_create',
    'controller_generator_create',
]
