# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Classes for generating common XML modifications for :term:`ROS1+Gazebo`.

I.e., changes which are engine-specific, but applicable to all projects using
the engine.

"""
# Core packages
import logging
import pathlib

# 3rd party packages

# Project packages
from sierra.core.experiment import spec as expspec
from sierra.core.experiment import definition
from sierra.core import types, ros1, config

_logger = logging.getLogger(__name__)


def for_all_exp(
    spec: expspec.ExperimentSpec,
    controller: str,
    cmdopts: types.Cmdopts,
    expdef_template_fpath: pathlib.Path,
) -> definition.BaseExpDef:
    """Generate XML modifications common to all ROS1+Gazebo experiments."""
    exp_def = ros1.generators.for_all_exp(
        spec, controller, cmdopts, expdef_template_fpath
    )

    exp_def.write_config.add(
        {
            "src_parent": ".",
            "src_tag": "master",
            "opath_leaf": "_master" + config.ROS["launch_file_ext"],
            "new_children": None,
            "new_children_parent": None,
            "rename_to": "launch",
        }
    )

    exp_def.write_config.add(
        {
            "src_parent": ".",
            "src_tag": "robot",
            "opath_leaf": "_robots" + config.ROS["launch_file_ext"],
            "new_children": None,
            "new_children_parent": None,
            "rename_to": "launch",
        }
    )

    # Setup gazebo experiment
    _generate_all_exp_gazebo_core(exp_def)

    # Setup gazebo visualization
    _generate_all_exp_gazebo_vis(exp_def)

    return exp_def


def _generate_all_exp_gazebo_core(exp_def: definition.BaseExpDef) -> None:
    """
    Generate XML tag changes to setup Gazebo core experiment parameters.

    Does not write generated changes to the run definition pickle
    file.
    """
    _logger.debug("Generating Gazebo experiment changes (all runs)")

    # Start Gazebo/ROS in debug mode to make post-mortem analysis easier.
    exp_def.element_add("./master/include", "arg", {"name": "verbose", "value": "true"})

    # Terminate Gazebo server whenever the launch script that invoked it
    # exits.
    exp_def.element_add(
        "./master/include", "arg", {"name": "server_required", "value": "true"}
    )

    # Don't record stuff
    exp_def.element_remove("./master/include", "arg/[@name='headless']")
    exp_def.element_remove("./master/include", "arg/[@name='recording']")

    # Don't start paused
    exp_def.element_remove("./master/include", "arg/[@name='paused']")

    # Don't start gazebo under gdb
    exp_def.element_remove("./master/include", "arg/[@name='debug']")


def _generate_all_exp_gazebo_vis(exp_def: definition.BaseExpDef) -> None:
    """
    Generate XML changes to configure Gazebo visualizations.

    Does not write generated changes to the simulation definition pickle
    file.
    """
    exp_def.element_remove_all("./master/include", "arg/[@name='gui']")
    exp_def.element_add("./master/include", "arg", {"name": "gui", "value": "false"})


def for_single_exp_run(*args, **kwargs) -> None:
    """Generate XML changes unique to each experimental run.

    Wraps :py:func:`sierra.core.ros1.generators.for_single_exp_run`.
    """
    return ros1.generators.for_single_exp_run(*args, **kwargs)


__all__ = ["for_all_exp", "for_single_exp_run"]
