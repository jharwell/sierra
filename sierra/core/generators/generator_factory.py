# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Factory for combining controller+scenario expdef modification generators.

By combining them together, the result can be easily used to apply modifications
to the template expdef file to scaffold the batch experiment.

"""
# Core packages
import typing as tp
import logging
import copy
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core.experiment import definition
from sierra.core.experiment import spec as expspec
import sierra.core.plugin_manager as pm
from sierra.core import types, config, utils


class ControllerGenerator():
    """Generate expdef changes for a selected ``--controller``.

    If the specified controller is not found in ``controllers.yaml`` for the
    loaded :term:`Project`, an assert will be triggered.
    """

    def __init__(self,
                 controller: str,
                 config_root: pathlib.Path,
                 cmdopts: types.Cmdopts,
                 exp_spec: expspec.ExperimentSpec) -> None:
        controllers_yaml = config_root / config.kYAML.controllers
        with utils.utf8open(controllers_yaml) as f:
            self.controller_config = yaml.load(f, yaml.FullLoader)

        main_yaml = config_root / config.kYAML.main
        with utils.utf8open(main_yaml) as f:
            self.main_config = yaml.load(f, yaml.FullLoader)

        n_components = len(controller.split('.'))
        if n_components != 2:
            raise RuntimeError(("Expected 2 controller components, got "
                                f"{n_components}. Arguments to --controller "
                                "must be of the form CATEGORY.TYPE (i.e., 2 "
                                "components separated by a '.')."))

        self.category, self.name = controller.split('.')
        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)
        self.spec = exp_spec

    def generate(self, exp_def: definition.BaseExpDef) -> definition.BaseExpDef:
        """Generate all modifications to the experiment definition from the controller.

        Does not save.

        """
        self._generate_controller_support(exp_def)
        self._generate_controller(exp_def)
        return exp_def

    def _pp_for_element_add(self,
                            add: definition.ElementAdd,
                            robot_id: tp.Optional[int] = None) -> definition.ElementAdd:
        module = pm.pipeline.get_plugin_module(self.cmdopts['platform'])

        if '__UUID__' in add.path:
            prefix = module.robot_prefix_extract(self.main_config, self.cmdopts)
            add.path = add.path.replace('__UUID__', f"{prefix}{robot_id}")

        return add

    def _do_element_add(self,
                        exp_def: definition.BaseExpDef,
                        add: definition.ElementAdd) -> None:

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
            assert hasattr(self.spec.criteria, 'n_agents'), \
                (f"When using __UUID__ and element_add in {controllers}, the batch "
                 "criteria must implement bc.IQueryableBatchCriteria")
            n_agents = self.spec.criteria.n_agents(self.spec.exp_num)

            assert n_agents > 0, \
                "Batch criteria {self.spec.criteria} returned 0 agents?"

            for robot_id in range(0, n_agents):
                to_pp = copy.deepcopy(add)
                pp_add = self._pp_for_element_add(to_pp, robot_id)
                exp_def.element_add(pp_add.path,
                                    pp_add.tag,
                                    pp_add.attr,
                                    True)
        else:
            to_pp = copy.deepcopy(add)
            pp_add = self._pp_for_element_add(to_pp)
            exp_def.element_add(pp_add.path,
                                pp_add.tag,
                                pp_add.attr,
                                False)

    def _generate_controller_support(self,
                                     exp_def: definition.BaseExpDef) -> None:
        # Setup controller support code (if any)
        xml_mods = self.controller_config.get(self.category, {}).get('xml', {})

        chgs = xml_mods.get('attr_change', {})
        for t in chgs:
            exp_def.attr_change(t[0], t[1], t[2])

        chgs = xml_mods. get('element_change', {})
        for t in chgs:
            exp_def.element_change(t[0], t[1], t[2])

        adds = xml_mods.get('element_add', {})
        for t in adds:
            self._do_element_add(exp_def, definition.ElementAdd(t[0],
                                                                t[1],
                                                                eval(t[2]),
                                                                False))

    def _generate_controller(self, exp_def: definition.BaseExpDef) -> None:
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

            chgs = controller.get('xml', {}).get('element_change', {})
            for t in chgs:
                exp_def.element_change(t[0], t[1], t[2])

            adds = controller.get('xml', {}).get('element_add', {})
            for t in adds:
                self._do_element_add(exp_def, definition.ElementAdd(t[0],
                                                                    t[1],
                                                                    eval(t[2]),
                                                                    False))


def joint_generator_create(controller, scenario):
    """
    Combine controller and scenario expdef modification generators together.
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


def scenario_generator_create(spec: expspec.ExperimentSpec,
                              controller,
                              **kwargs):
    """
    Create a scenario generator using the plugin search path.
    """

    def __init__(self, **kwargs) -> None:
        cmdopts = kwargs['cmdopts']
        self.logger = logging.getLogger(__name__)
        module = pm.module_load_tiered(project=cmdopts['project'],
                                       path='generators.scenario')
        self.generator = getattr(module,
                                 module.to_generator_name(spec.scenario_name))

    def generate(self):
        return self.generator(spec=spec,
                              controller=controller,
                              **kwargs)

    return type(spec.scenario_name,
                (object,), {"__init__": __init__,
                            "generate": generate
                            })(**kwargs)


def controller_generator_create(controller: str,
                                config_root: pathlib.Path,
                                cmdopts: types.Cmdopts,
                                spec: expspec.ExperimentSpec):
    """
    Create a controller generator from the cmdline specification.
    """
    return type(controller,
                (ControllerGenerator,), {})(controller,
                                            config_root,
                                            cmdopts,
                                            spec)


__all__ = [
    'ControllerGenerator',
    'joint_generator_create',
    'scenario_generator_create',
    'controller_generator_create',
]
