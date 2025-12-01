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
import sierra.core.plugin as pm
from sierra.core import types, config, utils


class ControllerGenerator:
    """Generate expdef changes for a selected ``--controller``.

    If the specified controller is not found in ``controllers.yaml`` for the
    loaded :term:`Project`, a warning will be issued.
    """

    def __init__(
        self,
        controller: str,
        config_root: pathlib.Path,
        cmdopts: types.Cmdopts,
        spec: expspec.ExperimentSpec,
    ) -> None:
        controllers_yaml = config_root / config.PROJECT_YAML.controllers
        self.logger = logging.getLogger(__name__)
        self.name = controller

        try:
            with utils.utf8open(controllers_yaml) as f:
                self.controller_config = yaml.load(f, yaml.FullLoader)
        except FileNotFoundError:
            self.logger.debug("%s does not exist", controllers_yaml)
            self.controller_config = {}

        main_yaml = config_root / config.PROJECT_YAML.main
        with utils.utf8open(main_yaml) as f:
            self.main_config = yaml.load(f, yaml.FullLoader)

        # Only check this if controllers.yaml exists. If it doesn't, then user's
        # can use whatever they want as the controller name (i.e., doesn't need
        # to conform to the below schema).
        if self.controller_config:
            n_components = len(controller.split("."))
            if n_components != 2:
                raise RuntimeError(
                    "Expected 2 controller components, got "
                    f"{n_components}. Arguments to --controller "
                    "must be of the form CATEGORY.TYPE (i.e., 2 "
                    "components separated by a '.')."
                )
            self.category, self.name = controller.split(".")
        else:
            self.category = None
            self.name = None

        self.cmdopts = cmdopts
        self.logger = logging.getLogger(__name__)
        self.spec = spec

    def generate(self, exp_def: definition.BaseExpDef) -> definition.BaseExpDef:
        """Generate all modifications to the expdef from the controller.

        Returns a new, modified expdef. Does not save to filesystem.

        """
        self._generate_controller_support(exp_def)
        self._generate_controller(exp_def)
        return exp_def

    def _pp_for_element_add(
        self, add: definition.ElementAdd, robot_id: tp.Optional[int] = None
    ) -> definition.ElementAdd:
        module = pm.pipeline.get_plugin_module(self.cmdopts["engine"])

        if "__UUID__" in add.path:
            prefix = module.robot_prefix_extract(self.main_config, self.cmdopts)
            add.path = add.path.replace("__UUID__", f"{prefix}{robot_id}")

        return add

    def _do_element_add(
        self, exp_def: definition.BaseExpDef, add: definition.ElementAdd
    ) -> None:

        # If the user is applying tags for each robot, then they might be added
        # multiple tags with the same name, but different attributes, so we
        # allow that explicitly here. Otherwise, we force all tag adds to be
        # unique.
        if "__UUID__" in add.path:
            # We can't use engine.population_size_from_def() here because we
            # haven't added any tags to the experiment definition yet, and if
            # the engine relies on added tags to calculate population sizes,
            # then this won't work.
            controllers = config.PROJECT_YAML.controllers
            assert hasattr(self.spec.criteria, "n_agents"), (
                f"When using __UUID__ and element_add in {controllers}, the batch "
                "criteria must implement bc.IQueryableBatchCriteria"
            )
            n_agents = self.spec.criteria.n_agents(self.spec.exp_num)

            assert (
                n_agents > 0
            ), "Batch criteria {self.spec.criteria} returned 0 agents?"

            for robot_id in range(0, n_agents):
                to_pp = copy.deepcopy(add)
                pp_add = self._pp_for_element_add(to_pp, robot_id)
                exp_def.element_add(pp_add.path, pp_add.tag, pp_add.attr, True)
        else:
            to_pp = copy.deepcopy(add)
            pp_add = self._pp_for_element_add(to_pp)
            exp_def.element_add(pp_add.path, pp_add.tag, pp_add.attr, False)

    def _generate_controller_support(
        self,
        exp_def: definition.BaseExpDef,
    ) -> None:
        # Setup controller support code (if any)
        for fmt in ["xml", "json", "yaml"]:
            mods = self.controller_config.get(self.category, {}).get(fmt, {})
            if mods is None:
                continue
            chgs = mods.get("attr_change", {})
            for t in chgs:
                exp_def.attr_change(t[0], t[1], t[2])

            chgs = mods.get("element_change", {})
            for t in chgs:
                exp_def.element_change(t[0], t[1], t[2])

            adds = mods.get("element_add", {})
            for t in adds:
                self._do_element_add(
                    exp_def, definition.ElementAdd(t[0], t[1], eval(t[2]), False)
                )

    def _generate_controller(self, exp_def: definition.BaseExpDef) -> None:
        if self.category is None:
            return

        if self.category not in self.controller_config:
            self.logger.warning(
                "Controller category '%s' not found in YAML configuration",
                self.category,
            )
            return

        if not any(
            self.name in config["name"]
            for config in self.controller_config[self.category]["controllers"]
        ):
            self.logger.warning(
                "Controller name '%s' not found in YAML configuration", self.name
            )
            return

        self.logger.debug(
            "Applying changes from %s (all experiments)",
            config.PROJECT_YAML.controllers,
        )

        for controller in self.controller_config[self.category]["controllers"]:
            if controller["name"] != self.name:
                continue

            for fmt in ["xml", "json", "yaml"]:
                chgs = controller.get(fmt, {}).get("attr_change", {})
                for t in chgs:
                    exp_def.attr_change(t[0], t[1], t[2])

                chgs = controller.get(fmt, {}).get("element_change", {})
                for t in chgs:
                    exp_def.element_change(t[0], t[1], t[2])

                adds = controller.get(fmt, {}).get("element_add", {})
                for t in adds:
                    self._do_element_add(
                        exp_def, definition.ElementAdd(t[0], t[1], eval(t[2]), False)
                    )


class ScenarioGenerator:
    """Generate expdef changes for a selected ``--scenario``."""

    def __init__(
        self, spec: expspec.ExperimentSpec, controller: str, scenario: str, **kwargs
    ):
        self.logger = logging.getLogger(__name__)
        self.spec = spec
        self.controller = controller
        self.name = scenario
        self.kwargs = kwargs

        cmdopts = kwargs["cmdopts"]
        module = pm.module_load_tiered(
            project=cmdopts["project"], path="generators.scenario"
        )
        self.generator = getattr(module, module.to_generator_name(spec.scenario_name))

    def generate(self):
        return self.generator(spec=self.spec, controller=self.controller, **self.kwargs)


class JointGenerator:
    """
    Combine controller and scenario expdef modification generators together.
    """

    def __init__(
        self, controller: ControllerGenerator, scenario: ScenarioGenerator
    ) -> None:
        self.name = f"{controller.name}+{scenario.name}"
        self.controller = controller
        self.scenario = scenario

    def generate(self):
        exp_def = self.scenario.generate()
        return self.controller.generate(exp_def)


__all__ = [
    "ControllerGenerator",
    "JointGenerator",
    "ScenarioGenerator",
]
