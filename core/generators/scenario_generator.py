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
import typing as tp
from core.variables import block_distribution, nest_pose, arena_shape
from core.xml_luigi import XMLLuigi
from core.generators import exp_generator


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
                 cmdopts: tp.Dict[str, str],
                 **kwargs):
        self.controller = controller
        self.exp_def_fpath = exp_def_fpath
        self.cmdopts = cmdopts
        self.common_defs = exp_generator.ExpDefCommonGenerator(exp_def_fpath=exp_def_fpath,
                                                               cmdopts=cmdopts,
                                                               **kwargs)

    @staticmethod
    def generate_block_dist(xml_luigi: XMLLuigi, block_dist: block_distribution.Type):
        """
        Generate XML changes for the specified block distribution.

        Does not write generated changes to the simulation definition pickle file.
        """
        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in block_dist.gen_attr_changelist()[0]]

        rms = block_dist.gen_tag_rmlist()
        if rms:  # non-empty
            [xml_luigi.tag_remove(a) for a in rms[0]]

    @staticmethod
    def generate_nest_pose(xml_luigi: XMLLuigi,
                           arena_dim: tp.Tuple[int, int, int],
                           dist_type: str):
        """
        Generate XML changes for the specified arena dimensions and block distribution type to
        properly place the nest.

        Does not write generated changes to the simulation definition pickle file.
        """
        np = nest_pose.NestPose(dist_type, [arena_dim])
        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in np.gen_attr_changelist()[0]]
        rms = np.gen_tag_rmlist()
        if rms:  # non-empty
            [xml_luigi.tag_remove(a) for a in rms[0]]

    def generate_arena_shape(self, xml_luigi: XMLLuigi, shape: arena_shape.RectangularArena):
        """
        Generate XML changes for the specified arena shape.

        Writes generated changes to the simulation definition pickle file.
        """
        # We check for attributes before modification because if we are not rendering video, then we
        # get a bunch of spurious warnings about deleted tags/attributes.
        for a in shape.gen_attr_changelist()[0]:
            if xml_luigi.has_tag(a[0]):
                xml_luigi.attr_change(a[0], a[1], a[2])

        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(shape.gen_attr_changelist()[0], f)

        rms = shape.gen_tag_rmlist()
        if rms:  # non-empty
            [xml_luigi.tag_remove(a) for a in rms[0]]

    def generate_block_count(self, xml_luigi: XMLLuigi):
        """
        Generates XML changes for # blocks in the simulation. If specified on the cmdline, that
        quantity is used. Otherwise, the # blocks specified in the manifest in the template input
        file is used, and split evenly between ramp and cube blocks.

        Writes generated changes to the simulation definition pickle file.
        """
        if self.cmdopts['n_blocks'] is not None:
            n_blocks = self.cmdopts['n_blocks']
        else:
            n_blocks = int(xml_luigi.attr_get('.//manifest', 'n_cube')) + \
                int(xml_luigi.attr_get('.//manifest', 'n_ramp'))

        bd = block_distribution.Quantity([n_blocks])

        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in bd.gen_attr_changelist()[0]]
        rms = bd.gen_tag_rmlist()

        if rms:  # non-empty
            [xml_luigi.tag_remove(a) for a in rms[0]]

        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(bd.gen_attr_changelist()[0], f)


class SSGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for single source foraging.

    This includes:

    - Rectangular 2x1 arena
    - Single source block distribution

    Changes are *NOT* generated for the following:

    - # robots

    """

    def __init__(self, *args, **kwargs):
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim[0] == 2 * arena_dim[1],\
            "FATAL: SS distribution requires a 2x1 arena: xdim={0},ydim={1}".format(arena_dim[0],
                                                                                    arena_dim[1])

        self.generate_arena_shape(exp_def,
                                  arena_shape.RectangularArenaTwoByOne(x_range=[arena_dim[0]],
                                                                       y_range=[arena_dim[1]]))

        # Generate and apply block distribution type definitions
        super().generate_block_dist(exp_def, block_distribution.TypeSingleSource())

        # Generate and apply nest definitions
        super().generate_nest_pose(exp_def, arena_dim, "single_source")

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        return exp_def


class DSGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for dual source foraging.

    This includes:

    - Rectangular 2x1 arena
    - Dual source block distribution

    Changes are *NOT* generated for the following:

    - # robots

    """

    def __init__(self, *args, **kwargs):
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim[0] == 2 * arena_dim[1],\
            "FATAL: DS distribution requires a 2x1 arena: xdim={0},ydim={1}".format(arena_dim[0],
                                                                                    arena_dim[1])

        self.generate_arena_shape(exp_def,
                                  arena_shape.RectangularArenaTwoByOne(x_range=[arena_dim[0]],
                                                                       y_range=[arena_dim[1]]))

        # Generate and apply block distribution type definitions
        super().generate_block_dist(exp_def, block_distribution.TypeDualSource())

        # Generate and apply nest definitions
        super().generate_nest_pose(exp_def, arena_dim, "dual_source")

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        return exp_def


class QSGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for quad source foraging.

    This includes:

    - Square arena
    - Quad source block distribution

    Changes are *NOT* generated for the following:

    - # robots

    """

    def __init__(self, *args, **kwargs):
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim[0] == arena_dim[1],\
            "FATAL: QS distribution requires a square arena: xdim={0},ydim={1}".format(arena_dim[0],
                                                                                       arena_dim[1])

        self.generate_arena_shape(exp_def, arena_shape.SquareArena(sqrange=[arena_dim[0]]))

        # Generate and apply block distribution type definitions
        source = block_distribution.TypeQuadSource()
        super().generate_block_dist(exp_def, source)

        # Generate and apply nest definitions
        super().generate_nest_pose(exp_def, arena_dim, "quad_source")

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

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

    def __init__(self, *args, **kwargs):
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim[0] == 2 * arena_dim[1],\
            "FATAL: PL distribution requires a square arena: xdim={0},ydim={1}".format(arena_dim[0],
                                                                                       arena_dim[1])

        self.generate_arena_shape(exp_def, arena_shape.SquareArena(sqrange=[arena_dim[0]]))

        # Generate and apply block distribution type definitions
        super().generate_block_dist(exp_def, block_distribution.TypePowerLaw())

        # Generate and apply nest definitions
        super().generate_nest_pose(exp_def, arena_dim, "powerlaw")

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        return exp_def


class RNGenerator(BaseScenarioGenerator):
    """
    Generates XML changes for random foraging.

    This includes:

    - Square arena
    - Random block distribution

    Changes are *NOT* generated for the following:

    - # robots

    """

    def __init__(self, *args, **kwargs):
        BaseScenarioGenerator.__init__(self, *args, **kwargs)

    def generate(self):
        exp_def = self.common_defs.generate()
        arena_dim = self.cmdopts["arena_dim"]

        assert arena_dim[0] == arena_dim[1],\
            "FATAL: RN distribution requires a square arena: xdim={0},ydim={1}".format(arena_dim[0],
                                                                                       arena_dim[1])

        self.generate_arena_shape(exp_def, arena_shape.SquareArena(sqrange=[arena_dim[0]]))

        # Generate and apply block distribution type definitions
        super().generate_block_dist(exp_def, block_distribution.TypeRandom())

        # Generate and apply nest definitions
        super().generate_nest_pose(exp_def, arena_dim, "random")

        # Generate and apply # blocks definitions
        self.generate_block_count(exp_def)

        return exp_def
