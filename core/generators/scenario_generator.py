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

from core.variables import block_distribution, arena_shape
from core.variables import population_size
from core.xml_luigi import XMLLuigi
from core.generators import exp_generator
from core.variables import physics_engines
from core.utils import ArenaExtent as ArenaExtent


class BaseScenarioGenerator():
    """
    Base class containing common functionality for generating XML changes for scenarios
    definitions.

    Attributes:
        controller: The controller used for the experiment.
        exp_def_fpath: Path to the pickle file to write generated XML changes to as needed for
                       later retrieval.
        cmdopts: Dictionary of parsed cmdline parameters.
    """

    def __init__(self,
                 exp_def_fpath: str,
                 controller: str,
                 cmdopts: dict,
                 **kwargs) -> None:
        self.controller = controller
        self.exp_def_fpath = exp_def_fpath
        self.cmdopts = cmdopts
        self.common_defs = exp_generator.ExpDefCommonGenerator(exp_def_fpath=exp_def_fpath,
                                                               cmdopts=cmdopts,
                                                               **kwargs)

    @staticmethod
    def generate_block_dist(exp_def: XMLLuigi,
                            block_dist: block_distribution.BaseDistribution):
        """
        Generate XML changes for the specified block distribution.

        Does not write generated changes to the simulation definition pickle file.
        """
        [exp_def.attr_change(a[0], a[1], a[2]) for a in block_dist.gen_attr_changelist()[0]]

        rms = block_dist.gen_tag_rmlist()
        if rms:  # non-empty
            [exp_def.tag_remove(a[0], a[1]) for a in rms[0]]

    def generate_arena_shape(self, exp_def: XMLLuigi, shape: arena_shape.RectangularArena):
        """
        Generate XML changes for the specified arena shape.

        Writes generated changes to the simulation definition pickle file.
        """
        # We check for attributes before modification because if we are not rendering video, then we
        # get a bunch of spurious warnings about deleted tags/attributes.
        for a in shape.gen_attr_changelist()[0]:
            if exp_def.has_tag(a[0]):
                exp_def.attr_change(a[0], a[1], a[2])

        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(shape.gen_attr_changelist()[0], f)

        rms = shape.gen_tag_rmlist()
        if rms:  # non-empty
            [exp_def.tag_remove(a[0], a[1]) for a in rms[0]]

    def generate_block_count(self, exp_def: XMLLuigi):
        """
        Generates XML changes for # blocks in the simulation. If specified on the cmdline, that
        quantity is used. Otherwise, the # blocks specified in the manifest in the template input
        file is used, and split evenly between ramp and cube blocks.

        Writes generated changes to the simulation definition pickle file.
        """
        if self.cmdopts['n_blocks'] is not None:
            n_blocks = self.cmdopts['n_blocks']
        else:
            n_blocks = int(exp_def.attr_get('.//manifest', 'n_cube')) + \
                int(exp_def.attr_get('.//manifest', 'n_ramp'))

        bd = block_distribution.Quantity([n_blocks])

        [exp_def.attr_change(a[0], a[1], a[2]) for a in bd.gen_attr_changelist()[0]]
        rms = bd.gen_tag_rmlist()

        if rms:  # non-empty
            [exp_def.tag_remove(a[0], a[1]) for a in rms[0]]

        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(bd.gen_attr_changelist()[0], f)

    def generate_n_robots(self, xml_luigi: XMLLuigi):
        """
        Generate XML changes to setup # robots.

        Writes generated changes to the simulation definition pickle file.
        """
        if self.cmdopts['n_robots'] is None:
            return

        chgs = population_size.PopulationSize.gen_attr_changelist_from_list(
            [self.cmdopts['n_robots']])
        for a in chgs[0]:
            xml_luigi.attr_change(a[0], a[1], a[2], True)

        # Write time setup info to file for later retrieval
        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(chgs[0], f)

    @staticmethod
    def generate_physics(exp_def: XMLLuigi,
                         cmdopts: dict,
                         engine_type: str,
                         n_engines: int,
                         extents: tp.List[ArenaExtent],
                         remove_defs: bool = True):
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
            logging.warning("0 engines of type %s specified", engine_type)
            return

        pe = physics_engines.factory(engine_type, n_engines, cmdopts, extents)

        if remove_defs:
            [exp_def.tag_remove(a[0], a[1]) for a in pe.gen_tag_rmlist()[0]]
        [exp_def.tag_add(a[0], a[1], a[2]) for a in pe.gen_tag_addlist()[0]]


class SSGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for single source foraging.

    This includes:

    - Rectangular 2x1 arena
    - Single source block distribution
    """

    def __init__(self, *args, **kwargs) -> None:
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim.x() == 2 * arena_dim.y(),\
            "FATAL: SS distribution requires a 2x1 arena: xdim={0},ydim={1}".format(arena_dim.x(),
                                                                                    arena_dim.y())

        self.generate_arena_shape(exp_def,
                                  arena_shape.RectangularArenaTwoByOne(x_range=[arena_dim.x()],
                                                                       y_range=[arena_dim.y()]))

        # Generate and apply block distribution type definitions
        super().generate_block_dist(exp_def, block_distribution.SingleSourceDistribution())

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        # Generate and apply robot count definitions
        self.generate_n_robots(exp_def)

        return exp_def


class DSGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for dual source foraging.

    This includes:

    - Rectangular 2x1 arena
    - Dual source block distribution

    """

    def __init__(self, *args, **kwargs) -> None:
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim.x() == 2 * arena_dim.y(),\
            "FATAL: DS distribution requires a 2x1 arena: xdim={0},ydim={1}".format(arena_dim.x(),
                                                                                    arena_dim.y())

        self.generate_arena_shape(exp_def,
                                  arena_shape.RectangularArenaTwoByOne(x_range=[arena_dim.x()],
                                                                       y_range=[arena_dim.y()]))

        # Generate and apply block distribution type definitions
        super().generate_block_dist(exp_def, block_distribution.DualSourceDistribution())

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        # Generate and apply robot count definitions
        self.generate_n_robots(exp_def)

        return exp_def


class QSGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for quad source foraging.

    This includes:

    - Square arena
    - Quad source block distribution

    """

    def __init__(self, *args, **kwargs) -> None:
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim.x() == arena_dim.y(),\
            "FATAL: QS distribution requires a square arena: xdim={0},ydim={1}".format(arena_dim.x(),
                                                                                       arena_dim.y())

        self.generate_arena_shape(exp_def, arena_shape.SquareArena(sqrange=[arena_dim.x()]))

        # Generate and apply block distribution type definitions
        source = block_distribution.QuadSourceDistribution()
        super().generate_block_dist(exp_def, source)

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        # Generate and apply robot count definitions
        self.generate_n_robots(exp_def)

        return exp_def


class PLGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for powerlaw source foraging.

    This includes:

    - Square arena
    - Powerlaw block distribution

    Changes are *NOT* generated for the following:

    - # robots

    """

    def __init__(self, *args, **kwargs) -> None:
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim.x() == arena_dim.y(),\
            "FATAL: PL distribution requires a square arena: xdim={0},ydim={1}".format(arena_dim.x(),
                                                                                       arena_dim.y())

        self.generate_arena_shape(exp_def, arena_shape.SquareArena(sqrange=[arena_dim.x()]))

        # Generate and apply block distribution type definitions
        super().generate_block_dist(exp_def, block_distribution.PowerLawDistribution(arena_dim))

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        return exp_def


class RNGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for random foraging.

    This includes:

    - Square arena
    - Random block distribution

    """

    def __init__(self, *args, **kwargs) -> None:
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim.x() == arena_dim.y(),\
            "FATAL: RN distribution requires a square arena: xdim={0},ydim={1}".format(arena_dim.x(),
                                                                                       arena_dim.y())

        self.generate_arena_shape(exp_def, arena_shape.SquareArena(sqrange=[arena_dim.x()]))

        # Generate and apply block distribution type definitions
        super().generate_block_dist(exp_def, block_distribution.RandomDistribution())

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        # Generate and apply robot count definitions
        self.generate_n_robots(exp_def)

        return exp_def


__api__ = [
    'BaseScenarioGenerator',
    'SSGenerator',
    'DSGenerator',
    'QSGenerator',
    'PLGenerator',
    'RNGenerator',
]
