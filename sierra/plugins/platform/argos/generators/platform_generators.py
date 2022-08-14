# Copyright 2021 John Harwell, All rights reserved.
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
"""Classes for generating common XML modifications for :term:`ARGoS`.

I.e., changes which are platform-specific, but applicable to all projects using
the platform.

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
from sierra.core.experiment import spec, definition, xml
from sierra.core import types, config, utils
import sierra.core.plugin_manager as pm

from sierra.plugins.platform.argos.variables import arena_shape
from sierra.plugins.platform.argos.variables import population_size
from sierra.plugins.platform.argos.variables import physics_engines
from sierra.plugins.platform.argos.variables import cameras
from sierra.plugins.platform.argos.variables import rendering
import sierra.plugins.platform.argos.variables.exp_setup as exp


class PlatformExpDefGenerator():
    """
    Init the object.

    Attributes:

        controller: The controller used for the experiment.

        cmdopts: Dictionary of parsed cmdline parameters.
    """

    def __init__(self,
                 exp_spec: spec.ExperimentSpec,
                 controller: str,
                 cmdopts: types.Cmdopts,
                 **kwargs) -> None:
        self.controller = controller
        self.spec = exp_spec
        self.cmdopts = cmdopts
        self.template_input_file = kwargs['template_input_file']
        self.kwargs = kwargs
        self.logger = logging.getLogger(__name__)

    def generate(self) -> definition.XMLExpDef:
        """Generate XML modifications common to all ARGoS experiments.

        """
        # ARGoS uses a single input file
        wr_config = xml.WriterConfig([{'src_parent': None,
                                       'src_tag': '.',
                                       'opath_leaf': config.kARGoS['launch_file_ext'],
                                       'create_tags': None,
                                       'dest_parent': None,
                                       'rename_to': None
                                       }])
        exp_def = definition.XMLExpDef(input_fpath=self.template_input_file,
                                       write_config=wr_config)

        # Generate # robots
        self._generate_n_robots(exp_def)

        # Setup library
        self._generate_library(exp_def)

        # Setup simulation visualizations
        self._generate_visualization(exp_def)

        # Setup threading
        self._generate_threading(exp_def)

        # Setup robot sensors/actuators
        self._generate_saa(exp_def)

        # Setup simulation time parameters
        self._generate_time(exp_def)

        return exp_def

    def generate_physics(self,
                         exp_def: definition.XMLExpDef,
                         cmdopts: types.Cmdopts,
                         engine_type: str,
                         n_engines: int,
                         extents: tp.List[ArenaExtent],
                         remove_defs: bool = True) -> None:
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
            self.logger.warning("0 engines of type %s specified", engine_type)
            return

        self.logger.trace(("Generating changes for %d '%s' "   # type: ignore
                           "physics engines (all runs)"),
                          n_engines,
                          engine_type)
        if cmdopts['physics_spatial_hash2D']:
            assert hasattr(self.spec.criteria, 'n_robots'),\
                ("When using the 2D spatial hash, the batch "
                 "criteria must implement bc.IQueryableBatchCriteria")
            n_robots = self.spec.criteria.n_robots(self.spec.exp_num)
        else:
            n_robots = None

        module = pm.pipeline.get_plugin_module(cmdopts['platform'])
        robot_type = module.robot_type_from_def(exp_def)
        pe = physics_engines.factory(engine_type,
                                     n_engines,
                                     n_robots,
                                     robot_type,
                                     cmdopts,
                                     extents)

        utils.apply_to_expdef(pe, exp_def)

    def generate_arena_shape(self,
                             exp_def: definition.XMLExpDef,
                             shape: arena_shape.ArenaShape) -> None:
        """
        Generate XML changes for the specified arena shape.

        Writes generated changes to the simulation definition pickle file.
        """
        self.logger.trace(("Generating changes for arena "    # type: ignore
                           "share (all runs)"))
        _, adds, chgs = utils.apply_to_expdef(shape, exp_def)
        utils.pickle_modifications(adds, chgs, self.spec.exp_def_fpath)

    def _generate_n_robots(self, exp_def: definition.XMLExpDef) -> None:
        """
        Generate XML changes to setup # robots (if specified on cmdline).

        Writes generated changes to the simulation definition pickle file.
        """
        if self.cmdopts['n_robots'] is None:
            return

        self.logger.trace(("Generating changes for # robots "   # type: ignore
                           "(all runs)"))
        chgs = population_size.PopulationSize.gen_attr_changelist_from_list(
            [self.cmdopts['n_robots']])
        for a in chgs[0]:
            exp_def.attr_change(a.path, a.attr, a.value, True)

        # Write # robots info to file for later retrieval
        chgs[0].pickle(self.spec.exp_def_fpath)

    def _generate_saa(self, exp_def: definition.XMLExpDef) -> None:
        """Generate XML changes to disable selected sensors/actuators.

        Some sensors and actuators are computationally expensive in large
        populations, but not that costly if the # robots is small.

        Does not write generated changes to the simulation definition pickle
        file.

        """
        self.logger.trace(("Generating changes for SAA "   # type: ignore
                           "(all runs)"))

        if not self.cmdopts["with_robot_rab"]:
            exp_def.tag_remove(".//media", "range_and_bearing", noprint=True)
            exp_def.tag_remove(".//actuators",
                               "range_and_bearing",
                               noprint=True)
            exp_def.tag_remove(".//sensors", "range_and_bearing", noprint=True)

        if not self.cmdopts["with_robot_leds"]:
            exp_def.tag_remove(".//actuators", "leds", noprint=True)
            exp_def.tag_remove(".//sensors",
                               "colored_blob_omnidirectional_camera",
                               noprint=True)
            exp_def.tag_remove(".//media", "led", noprint=True)

        if not self.cmdopts["with_robot_battery"]:
            exp_def.tag_remove(".//sensors", "battery", noprint=True)
            exp_def.tag_remove(".//entity/*", "battery", noprint=True)

    def _generate_time(self, exp_def: definition.XMLExpDef) -> None:
        """
        Generate XML changes to setup simulation time parameters.

        Writes generated changes to the simulation definition pickle file.
        """
        self.logger.debug("Using exp_setup=%s", self.cmdopts['exp_setup'])

        setup = exp.factory(self.cmdopts["exp_setup"])()
        rms, adds, chgs = utils.apply_to_expdef(setup, exp_def)

        # Write time setup info to file for later retrieval
        utils.pickle_modifications(adds, chgs, self.spec.exp_def_fpath)

    def _generate_threading(self, exp_def: definition.XMLExpDef) -> None:
        """Generate XML changes to set the # of cores for a simulation to use.

        This may be less than the total # available on the system, depending on
        the experiment definition and user preferences.

        Does not write generated changes to the simulation definition pickle
        file.

        """
        self.logger.trace(   # type: ignore
            "Generating changes for threading (all runs)")
        exp_def.attr_change(".//system",
                            "threads",
                            str(self.cmdopts["physics_n_engines"]))

        # Only valid on linux, per ARGoS, so we ely on the user to add this
        # attribute to the input file if it is applicable.
        if not exp_def.attr_get(".//system", "pin_threads_to_cores"):
            return

        if sys.platform != "linux":
            self.logger.critical((".//system/pin_threads_to_cores only "
                                  "valid on linux--configuration error?"))
            return

        # If you don't do this, you will get runtime errors in ARGoS when you
        # attempt to set thread affinity to a core that does not exist. This is
        # better than modifying ARGoS source to only pin threads to cores that
        # exist, because it implies a configuration error by the user, and
        # SIERRA should fail as a result (correctness by construction).
        if self.cmdopts['physics_n_engines'] > psutil.cpu_count():
            self.logger.warning(("Disabling pinning threads to cores: "
                                 "mores threads than cores! %s > %s"),
                                self.cmdopts['physics_n_engines'],
                                psutil.cpu_count())
            exp_def.attr_change(".//system",
                                "pin_threads_to_cores",
                                "false")

        else:
            exp_def.attr_change(".//system",
                                "pin_threads_to_cores",
                                "true")

    def _generate_library(self, exp_def: definition.XMLExpDef) -> None:
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
        self.logger.trace(  # type: ignore
            "Generating changes for library (all runs)")
        run_config = self.spec.criteria.main_config['sierra']['run']
        lib_name = run_config.get('library_name',
                                  'lib' + self.cmdopts['project'])
        exp_def.attr_change(".//loop_functions",
                            "library",
                            lib_name)
        exp_def.attr_change(".//__CONTROLLER__",
                            "library",
                            lib_name)

    def _generate_visualization(self, exp_def: definition.XMLExpDef) -> None:
        """Generate XML changes to remove visualization elements from input file.

        This depends on cmdline parameters, as visualization definitions should
        be left in if ARGoS should output simulation frames for video creation.

        Does not write generated changes to the simulation definition pickle
        file.

        """
        self.logger.trace(("Generating changes for "  # type: ignore
                           "visualization (all runs)"))

        if not self.cmdopts["platform_vc"]:
            # ARGoS visualizations
            exp_def.tag_remove(".", "./visualization", noprint=True)
        else:
            self.logger.debug('Frame grabbing enabled')
            # Rendering must be processing before cameras, because it deletes
            # the <qt_opengl> tag if it exists, and then re-adds it.
            render = rendering.factory(self.cmdopts)
            utils.apply_to_expdef(render, exp_def)

            cams = cameras.factory(self.cmdopts, [self.spec.arena_dim])
            utils.apply_to_expdef(cams, exp_def)


class PlatformExpRunDefUniqueGenerator:
    """Generate XML changes unique to each experimental run.

    These include:

    - Random seeds for each simulation.

    Attributes:

        run_num: The runulation # in the experiment.

        run_output_path: Path to simulation output directory within experiment
                         root.

        cmdopts: Dictionary containing parsed cmdline options.

    """

    def __init__(self,
                 run_num: int,
                 run_output_path: pathlib.Path,
                 launch_stem_path: pathlib.Path,
                 random_seed: int,
                 cmdopts: types.Cmdopts) -> None:

        self.run_output_path = run_output_path
        self.launch_stem_path = launch_stem_path
        self.cmdopts = cmdopts
        self.run_num = run_num
        self.random_seed = random_seed
        self.logger = logging.getLogger(__name__)

    def __generate_random(self, exp_def) -> None:
        """
        Generate XML changes for random seeding for a specific simulation.
        """
        self.logger.trace("Generating random seed changes for run%s",  # type: ignore
                          self.run_num)

        # Set the random seed in the input file
        exp_def.attr_change(".//experiment",
                            "random_seed",
                            str(self.random_seed))

    def generate(self, exp_def: definition.XMLExpDef):
        # Setup simulation random seed
        self.__generate_random(exp_def)

        # Setup simulation visualization output
        self.__generate_visualization(exp_def)

    def __generate_visualization(self, exp_def: definition.XMLExpDef):
        """
        Generate XML changes for setting up rendering for a specific simulation.
        """
        self.logger.trace("Generating visualization changes for run%s",  # type: ignore
                          self.run_num)

        if self.cmdopts['platform_vc']:
            argos = config.kRendering['argos']
            frames_fpath = self.run_output_path / argos['frames_leaf']
            exp_def.attr_change(".//qt-opengl/frame_grabbing",
                                "directory",
                                str(frames_fpath))  # probably will not be present


__api__ = [
    'PlatformExpDefGenerator',
    'PlatformExpRunDefUniqueGenerator'
]
