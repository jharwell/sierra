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

import pickle
import logging
import typing as tp

from core.variables import arena_shape
from core.variables import population_size
from core.xml_luigi import XMLLuigi
from core.generators import exp_generator
from core.variables import physics_engines
from core.utils import ArenaExtent as ArenaExtent
from core.experiment_spec import ExperimentSpec


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
        self.kwargs = kwargs
        self.logger = logging.getLogger(__name__)

    def generate(self) -> XMLLuigi:
        return exp_generator.ARGoSExpDefGenerator(spec=self.spec,
                                                  cmdopts=self.cmdopts,
                                                  **self.kwargs).generate()

    def generate_arena_shape(self, exp_def: XMLLuigi, shape: arena_shape.ArenaShape) -> None:
        """
        Generate XML changes for the specified arena shape.

        Writes generated changes to the simulation definition pickle file.
        """
        # We check for attributes before modification because if we are not rendering video, then we
        # get a bunch of spurious warnings about deleted tags/attributes.
        for a in shape.gen_attr_changelist()[0]:
            if exp_def.has_tag(a.path):
                exp_def.attr_change(a.path, a.attr, a.value)

        shape.gen_attr_changelist()[0].pickle(self.spec.exp_def_fpath)

        rms = shape.gen_tag_rmlist()
        if rms:  # non-empty
            for r in rms[0]:
                exp_def.tag_remove(r.path, r.tag)

    def generate_n_robots(self, xml_luigi: XMLLuigi) -> None:
        """
        Generate XML changes to setup # robots if it was specified on the cmdline.

        Writes generated changes to the simulation definition pickle file.
        """
        if self.cmdopts['n_robots'] is None:
            return

        chgs = population_size.PopulationSize.gen_attr_changelist_from_list(
            [self.cmdopts['n_robots']])
        for a in chgs[0]:
            xml_luigi.attr_change(a.path, a.attr, a.value, True)

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

        if remove_defs:
            for a in pe.gen_tag_rmlist()[0]:
                exp_def.tag_remove(a.path, a.tag)

        for r in pe.gen_tag_addlist()[0]:
            exp_def.tag_add(r.path, r.tag, r.attr)


__api__ = [
    'ARGoSScenarioGenerator',
]
