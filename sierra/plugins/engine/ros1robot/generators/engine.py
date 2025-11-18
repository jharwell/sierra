# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Classes for generating common XML modifications to :term:`ROS1` input files.

I.e., changes which are engine-specific, but applicable to all projects using
ROS with a real robot execution environment.

"""
# Core packages
import logging
import pathlib

# 3rd party packages
import yaml

# Project packages
from sierra.core.experiment import definition
from sierra.core.experiment import spec as expspec
from sierra.core import types, ros1, config, utils

_logger = logging.getLogger(__name__)


def for_all_exp(
    spec: expspec.ExperimentSpec,
    controller: str,
    cmdopts: types.Cmdopts,
    expdef_template_fpath: pathlib.Path,
) -> definition.BaseExpDef:
    """Generate changes for all experiments in the batch."""
    exp_def = ros1.generators.for_all_exp(
        spec, controller, cmdopts, expdef_template_fpath
    )

    _logger.debug("Writing separate <master> launch file")
    exp_def.write_config.add(
        {
            "src_parent": ".",
            "src_tag": "master",
            "opath_leaf": "_master" + config.ROS["launch_file_ext"],
            "new_children": None,
            "rename_to": "launch",
            "new_children_parent": None,
        }
    )

    # Add <robot> tag
    if not exp_def.has_element("./robot"):
        exp_def.element_add(".", "robot", {})
    if not exp_def.has_element("./robot/group/[@ns='sierra']"):
        exp_def.element_add("./robot", "group", {"ns": "sierra"})

    return exp_def


def for_single_exp_run(
    exp_def: definition.BaseExpDef,
    run_num: int,
    run_output_path: pathlib.Path,
    launch_stem_path: pathlib.Path,
    random_seed: int,
    cmdopts: types.Cmdopts,
) -> None:
    """Generate changes for a single experimental run."""
    ros1.generators.for_single_exp_run(
        exp_def, run_num, run_output_path, launch_stem_path, random_seed, cmdopts
    )

    main_path = pathlib.Path(cmdopts["project_config_root"], config.PROJECT_YAML.main)

    with utils.utf8open(main_path) as f:
        main_config = yaml.load(f, yaml.FullLoader)

    n_agents = utils.get_n_agents(
        main_config, cmdopts, launch_stem_path.parent, exp_def
    )

    for i in range(0, n_agents):
        prefix = main_config["ros"]["robots"][cmdopts["robot"]]["prefix"]
        exp_def.write_config.add(
            {
                "src_parent": "./robot",
                "src_tag": f"group/[@ns='{prefix}{i}']",
                "opath_leaf": f"_robot{i}" + config.ROS["launch_file_ext"],
                "new_children": [definition.ElementAdd.as_root("launch", {})],
                "new_children_parent": ".",
                "rename_to": None,
                "child_grafts_parent": ".",
                "child_grafts": ["./robot/group/[@ns='sierra']"],
            }
        )


__all__ = ["for_all_exp", "for_single_exp_run"]
