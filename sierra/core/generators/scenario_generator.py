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
import logging
import typing as tp

# 3rd party packages

# Project packages
from sierra.core.variables import arena_shape
from sierra.core.variables import population_size
from sierra.core.xml import XMLLuigi
from sierra.core.variables import physics_engines
from sierra.core.utils import ArenaExtent as ArenaExtent
from sierra.core.experiment_spec import ExperimentSpec
import sierra.core.variables.rendering as rendering
import sierra.core.variables.time_setup as ts
import sierra.core.utils as scutils
from sierra.core.variables import cameras


class ARGoSScenarioGenerator():
    """
    Base class containing common functionality for generating XML changes to the XML that ARGoS
    defines independently of any project it is used with.

    Attributes:
        controller: The controller used for the experiment.
        cmdopts: Dictionary of parsed cmdline parameters.
    """

    def __init__(self,
                 spec: ExperimentSpec,
                 controller: str,
                 cmdopts: tp.Dict[str, tp.Any],
                 **kwargs) -> None:
        self.controller = controller
        self.spec = spec
        self.cmdopts = cmdopts
        self.template_input_file = kwargs['template_input_file']
        self.kwargs = kwargs
        self.logger = logging.getLogger(__name__)

    def generate(self) -> XMLLuigi:
        """
        Generates XML changes to simulation input files that are common to all experiments.
        """
        # create an object that will edit the XML file
        exp_def = XMLLuigi(self.template_input_file)

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

    def generate_arena_shape(self, exp_def: XMLLuigi, shape: arena_shape.ArenaShape) -> None:
        """
        Generate XML changes for the specified arena shape.

        Writes generated changes to the simulation definition pickle file.
        """
        _, adds, chgs = scutils.apply_to_expdef(shape, exp_def)

        scutils.pickle_modifications(adds, chgs, self.spec.exp_def_fpath)

    def generate_n_robots(self, xml: XMLLuigi) -> None:
        """
        Generate XML changes to setup # robots if it was specified on the cmdline.

        Writes generated changes to the simulation definition pickle file.
        """
        if self.cmdopts['n_robots'] is None:
            return

        chgs = population_size.PopulationSize.gen_attr_changelist_from_list(
            [self.cmdopts['n_robots']])
        for a in chgs[0]:
            xml.attr_change(a.path, a.attr, a.value, True)

        # Write # robots info to file for later retrieval
        chgs[0].pickle(self.spec.exp_def_fpath)

    def generate_physics(self,
                         exp_def: XMLLuigi,
                         cmdopts: tp.Dict[str, tp.Any],
                         engine_type: str,
                         n_engines: int,
                         extents: tp.List[ArenaExtent],
                         remove_defs: bool = True) -> None:
        """
        Generates XML changes for the specified physics engines configuration for the
        simulation.

        Physics engine definition removal is optional, because when mixing 2D/3D engine definitions,
        you only want to remove the existing definitions BEFORE you have adding first of the mixed
        definitions. Doing so every time results in only the LAST of the mixed definitions being
        present in the input file.

        Does not write generated changes to the simulation definition pickle file.
        """
        # Valid to have 0 engines here if 2D/3D were mixed but only 1 engine was specified for the
        # whole simulation.
        if n_engines == 0:
            self.logger.warning("0 engines of type %s specified", engine_type)
            return

        pe = physics_engines.factory(engine_type, n_engines, cmdopts, extents)

        scutils.apply_to_expdef(pe, exp_def)

    def _generate_saa(self, exp_def: XMLLuigi) -> None:
        """
        Generates XML changes to disable selected sensors/actuators, which are computationally
        expensive in large swarms, but not that costly if the # robots is small.

        Does not write generated changes to the simulation definition pickle file.
        """
        if not self.cmdopts["with_robot_rab"]:
            exp_def.tag_remove(".//media", "range_and_bearing", noprint=True)
            exp_def.tag_remove(".//actuators", "range_and_bearing", noprint=True)
            exp_def.tag_remove(".//sensors", "range_and_bearing", noprint=True)

        if not self.cmdopts["with_robot_leds"]:
            exp_def.tag_remove(".//actuators", "leds", noprint=True)
            exp_def.tag_remove(".//sensors", "colored_blob_omnidirectional_camera", noprint=True)
            exp_def.tag_remove(".//media", "led", noprint=True)

        if not self.cmdopts["with_robot_battery"]:
            exp_def.tag_remove(".//sensors", "battery", noprint=True)
            exp_def.tag_remove(".//entity/*", "battery", noprint=True)

    def _generate_time(self, exp_def: XMLLuigi) -> None:
        """
        Generate XML changes to setup simulation time parameters.

        Writes generated changes to the simulation definition pickle file.
        """
        tsetup = ts.factory(self.cmdopts["time_setup"])()

        _, adds, chgs = scutils.apply_to_expdef(tsetup, exp_def)

        # Write time setup info to file for later retrieval
        scutils.pickle_modifications(adds, chgs, self.spec.exp_def_fpath)

    def _generate_threading(self, exp_def: XMLLuigi) -> None:
        """
        Generates XML changes to set the # of cores for a simulation to use, which may be less than
        the total # available on the system, depending on the experiment definition and user
        preferences.

        Does not write generated changes to the simulation definition pickle file.
        """

        exp_def.attr_change(".//system",
                            "threads",
                            str(self.cmdopts["physics_n_engines"]))

    def _generate_library(self, exp_def: XMLLuigi) -> None:
        """
        Generates XML changes to set the library that controllers and loop functions are sourced
        from to the name of the plugin passed on the cmdline. The ``__controller__`` tag is changed
        during stage 1, but since this function is called as part of common def generation, it
        happens BEFORE that, and so this is OK. If, for some reason that assumption becomes invalid,
        a warning will be issued about a non-existent XML path, so it won't be a silent error.

        Does not write generated changes to the simulation definition pickle file.
        """
        exp_def.attr_change(".//loop_functions",
                            "library",
                            "lib" + self.cmdopts['project'])
        exp_def.attr_change(".//__controller__",
                            "library",
                            "lib" + self.cmdopts['project'])

    def _generate_visualization(self, exp_def: XMLLuigi) -> None:
        """
        Generates XML changes to remove visualization elements from input file, if configured to do
        so. This depends on cmdline parameters, as visualization definitions should be left in if
        ARGoS should output simulation frames for video creation.

        Does not write generated changes to the simulation definition pickle file.
        """

        if not self.cmdopts["argos_rendering"]:
            exp_def.tag_remove(".", "./visualization", noprint=True)  # ARGoS visualizations
        else:
            # Rendering must be processing before cameras, because it deletes the <qt_opengl>
            # tag if it exists, and then re-adds it.
            render = rendering.factory(self.cmdopts)
            scutils.apply_to_expdef(render, exp_def, True)

            cams = cameras.factory(self.cmdopts, [self.spec.arena_dim])
            scutils.apply_to_expdef(cams, exp_def, True)


__api__ = [
    'ARGoSScenarioGenerator',
]
