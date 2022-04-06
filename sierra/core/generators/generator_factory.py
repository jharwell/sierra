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
import copy

# 3rd party packages
import yaml

# Project packages
from sierra.core.xml import XMLLuigi, XMLTagAdd
from sierra.core.experiment.spec import ExperimentSpec
import sierra.core.plugin_manager as pm
from sierra.core import types, config


class ControllerGenerator():
    """Generate XML changes for a selected ``--controller``.

    If the specified controller is not found in ``controllers.yaml`` for the
    loaded :term:`Project`, an assert will be triggered.
    """

    def __init__(self,
                 controller: str,
                 config_root: str,
                 cmdopts: types.Cmdopts,
                 spec: ExperimentSpec) -> None:
        self.controller_config = yaml.load(open(os.path.join(config_root,
                                                             config.kYAML['controllers'])),
                                           yaml.FullLoader)
        self.main_config = yaml.load(open(os.path.join(config_root,
                                                       config.kYAML['main'])),
                                     yaml.FullLoader)
        self.category, self.name = controller.split('.')
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)
        self.spec = spec

    def generate(self, exp_def: XMLLuigi) -> XMLLuigi:
        """
        Generates all changes to the input file for the :term:`Experimental Run`
        (does not save).

        """
        self._generate_controller_support(exp_def)
        self._generate_controller(exp_def)
        return exp_def

    def _pp_for_tag_add(self,
                        add: XMLTagAdd,
                        robot_id: tp.Optional[int] = None) -> tp.List[str]:
        module = pm.pipeline.get_plugin_module(
            self.cmdopts['platform'])
        if '__UUID__' in add.path:
            prefix = module.robot_prefix_extract(self.main_config, self.cmdopts)
            add.path = add.path.replace('__UUID__', f"{prefix}{robot_id}")

        add.attr = eval(add.attr)
        return add

    def _do_tag_add(self, exp_def: XMLLuigi, add: XMLTagAdd) -> None:

        # If the user is applying tags for each robot, then they might be added
        # multiple tags with the same name, but different attributes, so we
        # allow that explicitly here. Otherwise, we force all tag adds to be
        # unique.
        if '__UUID__' in add.path:
            # We can't use platform.population_size_from_def() here because we
            # haven't added any tags to the experiment definition yet, and if
            # the platform relies on added tags to calculate population sizes,
            # then this won't work.
            yaml = config.kYAML['controllers']
            assert hasattr(self.spec.criteria, 'n_robots'),\
                (f"When using __UUID__ and tag_add in {yaml}, the batch "
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

    def _generate_controller_support(self, exp_def: XMLLuigi) -> None:
        # Setup controller support code (if any)
        chgs = self.controller_config.get(self.category,
                                          {}).get('xml',
                                                  {}).get('attr_change',
                                                          {})
        for t in chgs:
            exp_def.attr_change(t[0], t[1], t[2])

        chgs = self.controller_config.get(self.category, {}).get('xml',
                                                                 {}).get('tag_change',
                                                                         {})
        for t in chgs:
            exp_def.tag_change(t[0], t[1], t[2])

        adds = self.controller_config.get(self.category, {}).get('xml',
                                                                 {}).get('tag_add',
                                                                         {})
        for t in adds:
            self._do_tag_add(exp_def, t)

    def _generate_controller(self, exp_def: XMLLuigi) -> None:
        if self.category not in self.controller_config:
            self.logger.fatal("Controller category '%s' not found in YAML configuration",
                              self.category)
            assert False

        if not any([self.name in config['name'] for config in self.controller_config[self.category]['controllers']]):
            self.logger.fatal("Controller name '%s' not found in YAML configuration",
                              self.name)
            assert False

        self.logger.debug(
            "Applying changes from controllers.yaml (all experiments)")
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
                self._do_tag_add(exp_def, XMLTagAdd(t[0],
                                                    t[1],
                                                    t[2],
                                                    False))


def joint_generator_create(controller, scenario):
    """
    Combinate controller and scenario XML change generators together.
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
                                cmdopts: types.Cmdopts,
                                spec: ExperimentSpec):
    """
    Creates a controller generator from the cmdline specification.
    """

    return type(controller,
                (ControllerGenerator,), {})(controller,
                                            config_root,
                                            cmdopts,
                                            spec)


__api__ = [
    'ControllerGenerator',

    'joint_generator_create',
    'scenario_generator_create',
    'controller_generator_create',
]
