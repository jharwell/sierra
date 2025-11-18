# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Classes for generating XML changes common to all :term:`ROS1` engines.

I.e., changes which are engine-specific, but applicable to all projects using
ROS1.

"""
# Core packages
import logging
import pathlib

# 3rd party packages

# Project packages
from sierra.core.experiment import definition
from sierra.core.experiment import spec as expspec
import sierra.core.utils as scutils
from sierra.core import types, config
import sierra.core.ros1.variables.exp_setup as exp
from sierra.core import plugin as pm

_logger = logging.getLogger(__name__)


def for_all_exp(
    spec: expspec.ExperimentSpec,
    controller: str,
    cmdopts: types.Cmdopts,
    expdef_template_fpath: pathlib.Path,
) -> definition.BaseExpDef:
    """Generate XML changes to input files that common to all ROS experiments.

    ROS1 requires up to 2 input files per run:

        - The launch file containing robot definitions, world definitions (for
          simulations only).

        - The parameter file for project code (optional).

    Putting everything in 1 file would require extensively using the ROS1
    parameter server which does NOT accept parameters specified in XML--only
    YAML.  So requiring some conventions on the .launch input file seemed more
    reasonable.
    """
    module = pm.pipeline.get_plugin_module(cmdopts["expdef"])

    exp_def = module.ExpDef(input_fpath=expdef_template_fpath, write_config=None)

    wr_config = definition.WriterConfig([])

    if exp_def.has_element("./params"):
        _logger.debug("Using shared XML parameter file")
        wr_config.add(
            {
                "src_parent": ".",
                "src_tag": "params",
                "opath_leaf": config.ROS["param_file_ext"],
                "new_children": None,
                "new_children_parent": None,
                "rename_to": None,
            }
        )

    exp_def.write_config_set(wr_config)

    # Add <master> tag
    if not exp_def.has_element("./master"):
        exp_def.element_add(".", "master", {})
    if not exp_def.has_element("./master/group/[@ns='sierra']"):
        exp_def.element_add("./master", "group", {"ns": "sierra"})
    # Add <robot> tag
    if not exp_def.has_element("./robot"):
        exp_def.element_add(".", "robot", {})
    if not exp_def.has_element("./robot/group/[@ns='sierra']"):
        exp_def.element_add("./robot", "group", {"ns": "sierra"})

    # Generate core experiment definitions
    _generate_all_exp_experiment(exp_def, spec, cmdopts)

    return exp_def


def _generate_all_exp_experiment(
    exp_def: definition.BaseExpDef, spec: expspec.ExperimentSpec, cmdopts: types.Cmdopts
) -> None:
    """
    Generate XML tag changes to setup basic experiment parameters.

    Writes generated changes to the simulation definition pickle file.
    """
    _logger.debug("Applying exp_setup=%s", cmdopts["exp_setup"])
    robots_need_timekeeper = "ros1robot" in cmdopts["engine"]

    # Barrier start not needed in simulation
    use_barrier_start = (
        "ros1robot" in cmdopts["engine"] and not cmdopts["no_master_node"]
    )

    setup = exp.factory(cmdopts["exp_setup"], use_barrier_start, robots_need_timekeeper)
    _, adds, chgs = scutils.apply_to_expdef(setup, exp_def)

    # Write setup info to file for later retrieval
    scutils.pickle_modifications(adds, chgs, spec.exp_def_fpath)


def for_single_exp_run(
    exp_def: definition.BaseExpDef,
    run_num: int,
    run_output_path: pathlib.Path,
    launch_stem_path: pathlib.Path,
    random_seed: int,
    cmdopts: types.Cmdopts,
) -> None:
    """
    Generate XML changes unique to a experimental runs for ROS experiments.

    These include:

    - Random seeds for each: term: `Experimental Run`.

    - Unique parameter file for each: term: `Experimental Run`.
    """
    _generate_single_exp_run_random(
        exp_def, run_num, run_output_path, launch_stem_path, random_seed, cmdopts
    )

    _generate_single_exp_run_paramfile(
        exp_def, run_num, run_output_path, launch_stem_path, random_seed, cmdopts
    )


def _generate_single_exp_run_random(
    exp_def: definition.BaseExpDef,
    run_num: int,
    run_output_path: pathlib.Path,
    launch_stem_path: pathlib.Path,
    random_seed: int,
    cmdopts: types.Cmdopts,
) -> None:
    """Generate XML changes for random seeding for an experimental run."""
    _logger.trace("Generating random seed changes for run%s", run_num)

    # Master gets the random seed
    exp_def.element_add(
        "./master/group/[@ns='sierra']",
        "param",
        {"name": "experiment/random_seed", "value": str(random_seed)},
    )

    # Each robot gets the random seed
    exp_def.element_add(
        "./robot/group/[@ns='sierra']",
        "param",
        {"name": "experiment/random_seed", "value": str(random_seed)},
    )


def _generate_single_exp_run_paramfile(
    exp_def: definition.BaseExpDef,
    run_num: int,
    run_output_path: pathlib.Path,
    launch_stem_path: pathlib.Path,
    random_seed: int,
    cmdopts: types.Cmdopts,
) -> None:
    """Generate XML changes for the parameter file for an experimental run."""
    _logger.trace("Generating parameter file changes for run%s", run_num)

    param_file = launch_stem_path.with_suffix(config.ROS["param_file_ext"])

    # Master node gets a copy of the parameter file
    exp_def.element_add(
        "./master/group/[@ns='sierra']",
        "param",
        {"name": "experiment/param_file", "value": str(param_file)},
    )

    # Each robot gets a copy of the parameter file
    if not exp_def.has_element("./robot/group/[@ns='sierra']"):
        exp_def.element_add(
            "./robot",
            "group",
            {
                "ns": "sierra",
            },
        )
    exp_def.element_add(
        "./robot/group/[@ns='sierra']",
        "param",
        {"name": "experiment/param_file", "value": str(param_file)},
    )


__all__ = ["for_all_exp", "for_single_exp_run"]
