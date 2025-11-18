# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Classes for generating common XML modifications for :term:`ARGoS`.

I.e., changes which are engine-specific, but applicable to all projects using
the engine.

"""
# Core packages
import typing as tp
import logging
import sys
import pathlib

# 3rd party packages
import psutil

# Project packages
from sierra.core.utils import ArenaExtent
from sierra.core.experiment import definition
from sierra.core.experiment import spec as expspec
from sierra.core import types, config, utils
import sierra.core.plugin as pm

from sierra.plugins.engine.argos.variables import arena_shape
from sierra.plugins.engine.argos.variables import population_size
from sierra.plugins.engine.argos.variables import physics_engines
from sierra.plugins.engine.argos.variables import cameras
from sierra.plugins.engine.argos.variables import rendering
import sierra.plugins.engine.argos.variables.exp_setup as exp

_logger = logging.getLogger(__name__)


def generate_physics(
    exp_def: definition.BaseExpDef,
    spec: expspec.ExperimentSpec,
    cmdopts: types.Cmdopts,
    engine_type: str,
    n_engines: int,
    extents: list[ArenaExtent],
    remove_defs: bool = True,
) -> None:
    """
    Generate XML changes for the specified physics engines configuration.

    Physics engine definition removal is optional, because when mixing 2D/3D
    engine definitions, you only want to remove the existing definitions
    BEFORE you have adding first of the mixed definitions. Doing so every
    time results in only the LAST of the mixed definitions being present in
    the input file.

    Does not write generated changes to the simulation definition pickle
    file.
    """
    # Valid to have 0 engines here if 2D/3D were mixed but only 1 engine was
    # specified for the whole simulation.
    if n_engines == 0:
        _logger.warning("0 engines of type %s specified", engine_type)
        return

    _logger.trace(
        ("Generating changes for %d '%s' " "physics engines (all runs)"),
        n_engines,
        engine_type,
    )
    if cmdopts["physics_spatial_hash2D"]:
        assert hasattr(spec.criteria, "n_agents"), (
            "When using the 2D spatial hash, the batch "
            "criteria must implement bc.IQueryableBatchCriteria"
        )
        n_agents = spec.criteria.n_agents(spec.exp_num)
    else:
        n_agents = None

    module = pm.pipeline.get_plugin_module(cmdopts["engine"])
    robot_type = module.robot_type_from_def(exp_def)
    pe = physics_engines.factory(
        engine_type, n_engines, n_agents, robot_type, cmdopts, extents
    )

    utils.apply_to_expdef(pe, exp_def)


def generate_arena_shape(
    exp_def: definition.BaseExpDef,
    spec: expspec.ExperimentSpec,
    shape: arena_shape.ArenaShape,
) -> None:
    """
    Generate XML changes for the specified arena shape.

    Writes generated changes to the simulation definition pickle file.
    """
    _logger.trace("Generating changes for arena " "share (all runs)")
    _, adds, chgs = utils.apply_to_expdef(shape, exp_def)
    utils.pickle_modifications(adds, chgs, spec.exp_def_fpath)


def for_all_exp(
    spec: expspec.ExperimentSpec,
    controller: str,
    cmdopts: types.Cmdopts,
    expdef_template_fpath: pathlib.Path,
) -> definition.BaseExpDef:
    """Generate XML modifications common to all ARGoS experiments."""
    # ARGoS uses a single input file
    wr_config = definition.WriterConfig(
        [
            {
                "src_parent": None,
                "src_tag": ".",
                "opath_leaf": config.ARGOS["launch_file_ext"],
                "new_children": None,
                "new_children_parent": None,
                "rename_to": None,
            }
        ]
    )
    module = pm.pipeline.get_plugin_module(cmdopts["expdef"])

    exp_def = module.ExpDef(input_fpath=expdef_template_fpath, write_config=wr_config)

    # Generate # robots
    _generate_all_exp_n_agents(exp_def, spec, cmdopts)

    # Setup library
    _generate_all_exp_library(exp_def, spec, cmdopts)

    # Setup simulation visualizations
    _generate_all_exp_visualization(exp_def, spec, cmdopts)

    # Setup threading
    _generate_all_exp_threading(exp_def, cmdopts)

    # Setup robot sensors/actuators
    _generate_all_exp_saa(exp_def, spec, cmdopts)

    # Setup simulation time parameters
    _generate_all_exp_time(exp_def, spec, cmdopts)

    return exp_def


def for_single_exp_run(
    exp_def: definition.BaseExpDef,
    run_num: int,
    run_output_path: pathlib.Path,
    launch_stem_path: pathlib.Path,
    random_seed: int,
    cmdopts: types.Cmdopts,
) -> definition.BaseExpDef:
    """Generate XML changes unique to each experimental run.

    These include:

    - Random seeds for each simulation.

    - Visualization changes, if visualization is enabled.
    """
    # Setup simulation random seed
    _generate_single_exp_run_random_seed(exp_def, run_num, random_seed)

    # Setup simulation visualization output
    _generate_single_exp_run_visualization(exp_def, run_num, run_output_path, cmdopts)

    return exp_def


def _generate_single_exp_run_random_seed(
    exp_def: definition.BaseExpDef, run_num: int, random_seed: int
) -> None:
    """Generate XML changes for random seeding for a specific simulation."""
    _logger.trace("Generating random seed changes for run%s", run_num)

    # Set the random seed in the input file
    exp_def.attr_change(".//experiment", "random_seed", str(random_seed))


def _generate_single_exp_run_visualization(
    exp_def: definition.BaseExpDef,
    run_num: int,
    run_output_path: pathlib.Path,
    cmdopts: types.Cmdopts,
):
    """Generate XML changes for visualization for a specific simulation."""
    _logger.trace("Generating visualization changes for run%s", run_num)

    if cmdopts["engine_vc"]:
        frames_fpath = run_output_path / config.ARGOS["frames_leaf"]
        exp_def.attr_change(
            ".//qt-opengl/frame_grabbing", "directory", str(frames_fpath)
        )  # probably will not be present


def _generate_all_exp_n_agents(
    exp_def: definition.BaseExpDef, spec: expspec.ExperimentSpec, cmdopts: types.Cmdopts
) -> None:
    """
    Generate XML changes to setup # robots (if specified on cmdline).

    Writes generated changes to the simulation definition pickle file.
    """
    if cmdopts["n_agents"] is None:
        return

    _logger.trace("Generating changes for # robots (all runs)")
    chgs = population_size.PopulationSize.gen_attr_changelist_from_list(
        [cmdopts["n_agents"]]
    )
    for a in chgs[0]:
        exp_def.attr_change(a.path, a.attr, a.value, True)

    # Write # robots info to file for later retrieval
    chgs[0].pickle(spec.exp_def_fpath)


def _generate_all_exp_saa(
    exp_def: definition.BaseExpDef,
    exp_spec: expspec.ExperimentSpec,
    cmdopts: types.Cmdopts,
) -> None:
    """Generate XML changes to disable selected sensors/actuators.

    Some sensors and actuators are computationally expensive in large
    populations, but not that costly if the # robots is small.

    Does not write generated changes to the simulation definition pickle
    file.

    """
    _logger.trace("Generating changes for SAA (all runs)")

    if not cmdopts["with_robot_rab"]:
        exp_def.element_remove(".//media", "range_and_bearing", noprint=True)
        exp_def.element_remove(".//actuators", "range_and_bearing", noprint=True)
        exp_def.element_remove(".//sensors", "range_and_bearing", noprint=True)

    if not cmdopts["with_robot_leds"]:
        exp_def.element_remove(".//actuators", "leds", noprint=True)
        exp_def.element_remove(
            ".//sensors", "colored_blob_omnidirectional_camera", noprint=True
        )
        exp_def.element_remove(".//media", "led", noprint=True)

    if not cmdopts["with_robot_battery"]:
        exp_def.element_remove(".//sensors", "battery", noprint=True)
        exp_def.element_remove(".//entity/*", "battery", noprint=True)


def _generate_all_exp_time(
    exp_def: definition.BaseExpDef, spec: expspec.ExperimentSpec, cmdopts: types.Cmdopts
) -> None:
    """
    Generate XML changes to setup simulation time parameters.

    Writes generated changes to the simulation definition pickle file.
    """
    _logger.debug("Using exp_setup=%s", cmdopts["exp_setup"])

    setup = exp.factory(cmdopts["exp_setup"])
    _, adds, chgs = utils.apply_to_expdef(setup, exp_def)

    # Write time setup info to file for later retrieval
    utils.pickle_modifications(adds, chgs, spec.exp_def_fpath)


def _generate_all_exp_threading(
    exp_def: definition.BaseExpDef, cmdopts: types.Cmdopts
) -> None:
    """Generate XML changes to set the # of cores for a simulation to use.

    This may be less than the total # available on the system, depending on
    the experiment definition and user preferences.

    Does not write generated changes to the simulation definition pickle
    file.

    """
    _logger.trace("Generating changes for threading (all runs)")
    exp_def.attr_change(".//system", "threads", str(cmdopts["physics_n_engines"]))

    # Only valid on linux, per ARGoS, so we ely on the user to add this
    # attribute to the input file if it is applicable.
    if not exp_def.attr_get(".//system", "pin_threads_to_cores"):
        return

    if sys.platform != "linux":
        _logger.critical(
            ".//system/pin_threads_to_cores only "
            "valid on linux--configuration error?"
        )
        return

    # If you don't do this, you will get runtime errors in ARGoS when you
    # attempt to set thread affinity to a core that does not exist. This is
    # better than modifying ARGoS source to only pin threads to cores that
    # exist, because it implies a configuration error by the user, and
    # SIERRA should fail as a result (correctness by construction).
    if cmdopts["physics_n_engines"] > psutil.cpu_count():
        _logger.warning(
            (
                "Disabling pinning threads to cores: "
                "mores threads than cores! %s > %s"
            ),
            cmdopts["physics_n_engines"],
            psutil.cpu_count(),
        )
        exp_def.attr_change(".//system", "pin_threads_to_cores", "false")

    else:
        exp_def.attr_change(".//system", "pin_threads_to_cores", "true")


def _generate_all_exp_library(
    exp_def: definition.BaseExpDef, spec: expspec.ExperimentSpec, cmdopts: types.Cmdopts
) -> None:
    """Generate XML changes for ARGoS search paths for controller,loop functions.

    Set to the name of the plugin passed on the cmdline, unless overriden in
    configuration. The ``__CONTROLLER__`` tag is changed during stage 1, but
    since this function is called as part of common def generation, it
    happens BEFORE that, and so this is OK. If, for some reason that
    assumption becomes invalid, a warning will be issued about a
    non-existent XML path, so it won't be a silent error.

    Does not write generated changes to the simulation definition pickle
    file.

    """
    _logger.trace("Generating changes for library (all runs)")

    run_config = spec.criteria.main_config["sierra"]["run"]
    lib_name = run_config.get("library_name", "lib" + cmdopts["project"])
    exp_def.attr_change(".//loop_functions", "library", lib_name)
    exp_def.attr_change(".//__CONTROLLER__", "library", lib_name)


def _generate_all_exp_visualization(
    exp_def: definition.BaseExpDef, spec: expspec.ExperimentSpec, cmdopts: types.Cmdopts
) -> None:
    """Generate XML changes to remove visualization elements from input file.

    This depends on cmdline parameters, as visualization definitions should
    be left in if ARGoS should output simulation frames for video creation.

    Does not write generated changes to the simulation definition pickle
    file.

    """
    _logger.trace("Generating changes for visualization (all runs)")

    if not cmdopts["engine_vc"]:
        # ARGoS visualizations
        exp_def.element_remove(".", "./visualization", noprint=True)
    else:
        _logger.debug("Frame grabbing enabled")
        # Rendering must be processing before cameras, because it deletes
        # the <qt_opengl> tag if it exists, and then re-adds it.
        render = rendering.factory(cmdopts)
        utils.apply_to_expdef(render, exp_def)

        cams = cameras.factory(cmdopts, [spec.arena_dim])
        utils.apply_to_expdef(cams, exp_def)


__all__ = ["for_all_exp", "for_single_exp_run"]
