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

# Core packages
import os
import typing as tp
import logging  # type: tp.Any

# 3rd party packages
import yaml

# Project packages
from sierra.core.xml import XMLLuigi
from sierra.core.experiment_spec import ExperimentSpec
import sierra.core.plugin_manager as pm
from sierra.core import types


def joint_generator_create(controller, scenario):
    """
    Given a controller (generator), and a scenario(generator), construct a joint
    generator class that can be used for experiment generation.

    """
    joint_name = '+'.join([controller.__class__.__name__,
                           scenario.__class__.__name__])

    def __init__(self) -> None:
        self.controller = controller
        self.scenario = scenario
        self.joint_name = joint_name

    def generate(self):
        exp_def = self.scenario.generate()
        return self.controller.generate(exp_def)

    return type(joint_name,
                (object,), {"__init__": __init__, "generate":
                            generate})()


def scenario_generator_create(spec: ExperimentSpec,
                              controller,
                              **kwargs):
    """
    Creates a scenario generator using the plugin search path.
    """

    def __init__(self, **kwargs) -> None:
        cmdopts = kwargs['cmdopts']
        self.logger = logging.getLogger(__name__)
        module = pm.module_load_tiered(project=cmdopts['project'],
                                       path='generators.scenario_generators')
        generator_name = module.gen_generator_name(spec.scenario_name)
        self.scenario_generator = getattr(module, generator_name)(controller=controller,
                                                                  spec=spec,
                                                                  **kwargs)

    def generate(self):
        return self.scenario_generator.generate()

    return type(spec.scenario_name,
                (object,), {"__init__": __init__,
                            "generate": generate
                            })(**kwargs)


def controller_generator_create(controller: str,
                                config_root: str,
                                cmdopts: types.Cmdopts):
    """
    Creates a controller generator from the cmdline specification that exists in
    one of the configuration files.
    """

    def __init__(self) -> None:
        self.config = yaml.load(open(os.path.join(config_root, 'controllers.yaml')),
                                yaml.FullLoader)
        self.category, self.name = controller.split('.')
        self.logger = logging.getLogger(__name__)

    def generate(self, exp_def: XMLLuigi):
        """
        Generates all changes to the input file for the :term:`Experimental Run`
        (does not save).

        """
        # Setup controller support code (if any)
        try:
            for t in self.config[self.category]['xml']['attr_change']:
                exp_def.attr_change(t[0],
                                    t[1],
                                    t[2],
                                    cmdopts['platform_vc'] is False)
        except KeyError:
            self.logger.fatal("Controller support category '%s' not found in YAML configuration",
                              self.category)
            raise

        # Setup controller
        try:
            for controller in self.config[self.category]['controllers']:
                if controller['name'] == self.name:
                    for t in controller['xml']['attr_change']:
                        exp_def.tag_change(t[0], t[1], t[2])
        except KeyError:
            self.logger.fatal("Controller category '%s' or name '%s' not found in YAML configuration",
                              self.category,
                              self.name)
            raise

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
