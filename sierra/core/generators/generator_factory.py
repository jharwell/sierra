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
"""Factory for combining controller+scenario XML modification generators.

By combining them together, the result can be easily used to apply modifications
to the template XML file to scaffold the batch experiment.

"""
# Core packages
import typing as tp
import logging
import copy
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core.experiment import spec, xml, definition
import sierra.core.plugin_manager as pm
from sierra.core import types, config, utils


class ControllerGenerator():
    """Generate XML changes for a selected ``--controller``.

    If the specified controller is not found in ``controllers.yaml`` for the
    loaded :term:`Project`, an assert will be triggered.
    """

    def __init__(self,
                 controller: str,
                 config_root: pathlib.Path,
                 cmdopts: types.Cmdopts,
                 exp_spec: spec.ExperimentSpec) -> None:
        controllers_yaml = config_root / config.kYAML.controllers
        with utils.utf8open(controllers_yaml) as f:
            self.controller_config = yaml.load(f, yaml.FullLoader)

        main_yaml = config_root / config.kYAML.main
        with utils.utf8open(main_yaml) as f:
            self.main_config = yaml.load(f, yaml.FullLoader)

        self.category, self.name = controller.split('.')
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)
        self.spec = exp_spec

    def generate(self, exp_def: definition.XMLExpDef) -> definition.XMLExpDef:
        """Generate all modifications to the experiment definition from the controller.

        Does not save.

        """
        self._generate_controller_support(exp_def)
        self._generate_controller(exp_def)
        return exp_def

    def _pp_for_tag_add(self,
                        add: xml.TagAdd,
                        robot_id: tp.Optional[int] = None) -> xml.TagAdd:
        module = pm.pipeline.get_plugin_module(self.cmdopts['platform'])

        if '__UUID__' in add.path:
            prefix = module.robot_prefix_extract(self.main_config, self.cmdopts)
            add.path = add.path.replace('__UUID__', f"{prefix}{robot_id}")

        return add

    def _do_tag_add(self,
                    exp_def: definition.XMLExpDef,
                    add: xml.TagAdd) -> None:

        # If the user is applying tags for each robot, then they might be added
        # multiple tags with the same name, but different attributes, so we
        # allow that explicitly here. Otherwise, we force all tag adds to be
        # unique.
        if '__UUID__' in add.path:
            # We can't use platform.population_size_from_def() here because we
            # haven't added any tags to the experiment definition yet, and if
            # the platform relies on added tags to calculate population sizes,
            # then this won't work.
            controllers = config.kYAML.controllers
            assert hasattr(self.spec.criteria, 'n_robots'),\
                (f"When using __UUID__ and tag_add in {controllers}, the batch "
                 "criteria must implement bc.IQueryableBatchCriteria")
            n_robots = self.spec.criteria.n_robots(self.spec.exp_num)

            assert n_robots > 0,\
                "Batch criteria {self.spec.criteria} returned 0 robots?"

            for robot_id in range(0, n_robots):
                to_pp = copy.deepcopy(add)
                pp_add = self._pp_for_tag_add(to_pp, robot_id)
                exp_def.tag_add(pp_add.path,
                                pp_add.tag,
                                pp_add.attr,
                                True)
        else:
            to_pp = copy.deepcopy(add)
            pp_add = self._pp_for_tag_add(to_pp)
            exp_def.tag_add(pp_add.path,
                            pp_add.tag,
                            pp_add.attr,
                            False)

    def _generate_controller_support(self,
                                     exp_def: definition.XMLExpDef) -> None:
        # Setup controller support code (if any)
        xml_mods = self.controller_config.get(self.category, {}).get('xml', {})

        chgs = xml_mods.get('attr_change', {})
        for t in chgs:
            exp_def.attr_change(t[0], t[1], t[2])

        chgs = xml_mods. get('tag_change', {})
        for t in chgs:
            exp_def.tag_change(t[0], t[1], t[2])

        adds = xml_mods.get('tag_add', {})
        for t in adds:
            self._do_tag_add(exp_def, xml.TagAdd(t[0],
                                                 t[1],
                                                 eval(t[2]),
                                                 False))

    def _generate_controller(self, exp_def: definition.XMLExpDef) -> None:
        if self.category not in self.controller_config:
            self.logger.fatal("Controller category '%s' not found in YAML configuration",
                              self.category)
            raise RuntimeError

        if not any(self.name in config['name'] for config in self.controller_config[self.category]['controllers']):
            self.logger.fatal("Controller name '%s' not found in YAML configuration",
                              self.name)
            raise RuntimeError

        self.logger.debug("Applying changes from %s (all experiments)",
                          config.kYAML.controllers)

        for controller in self.controller_config[self.category]['controllers']:
            if controller['name'] != self.name:
                continue

            chgs = controller.get('xml', {}).get('attr_change', {})
            for t in chgs:
                exp_def.attr_change(t[0], t[1], t[2])

            chgs = controller.get('xml', {}).get('tag_change', {})
            for t in chgs:
                exp_def.tag_change(t[0], t[1], t[2])

            adds = controller.get('xml', {}).get('tag_add', {})
            for t in adds:
                self._do_tag_add(exp_def, xml.TagAdd(t[0],
                                                     t[1],
                                                     eval(t[2]),
                                                     False))


def joint_generator_create(controller, scenario):
    """
    Combine controller and scenario XML modification generators together.
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


def scenario_generator_create(exp_spec: spec.ExperimentSpec,
                              controller,
                              **kwargs):
    """
    Create a scenario generator using the plugin search path.
    """

    def __init__(self, **kwargs) -> None:
        cmdopts = kwargs['cmdopts']
        self.logger = logging.getLogger(__name__)
        module = pm.module_load_tiered(project=cmdopts['project'],
                                       path='generators.scenario_generators')
        generator_name = module.gen_generator_name(exp_spec.scenario_name)
        self.scenario_generator = getattr(module, generator_name)(controller=controller,
                                                                  exp_spec=exp_spec,
                                                                  **kwargs)

    def generate(self):
        return self.scenario_generator.generate()

    return type(exp_spec.scenario_name,
                (object,), {"__init__": __init__,
                            "generate": generate
                            })(**kwargs)


def controller_generator_create(controller: str,
                                config_root: pathlib.Path,
                                cmdopts: types.Cmdopts,
                                exp_spec: spec.ExperimentSpec):
    """
    Create a controller generator from the cmdline specification.
    """

    return type(controller,
                (ControllerGenerator,), {})(controller,
                                            config_root,
                                            cmdopts,
                                            exp_spec)


__api__ = [
    'ControllerGenerator',
    'joint_generator_create',
    'scenario_generator_create',
    'controller_generator_create',
]
