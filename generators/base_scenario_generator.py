# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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
import variables as ev
from variables import block_distribution, dynamic_cache, static_cache
from xml_luigi import XMLLuigi
from generators import exp_generator


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
    def generate_block_dist(xml_luigi: XMLLuigi, block_dist: ev.block_distribution.Type):
        """
        Generate XML changes for the specified block distribution.

        Does not write generated changes to the simulation definition pickle file.
        """
        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in block_dist.gen_attr_changelist()[0]]

        rms = block_dist.gen_tag_rmlist()
        if rms:  # non-empty
            [xml_luigi.tag_remove(a) for a in rms[0]]

    @staticmethod
    def generate_dynamic_cache(xml_luigi: XMLLuigi, arena_dim: tp.Tuple[int, int, int]):
        """
        Generate XML changes for dynamic cache usage (depth2 simulations only).

        Does not write generated changes to the simulation definition pickle file.
        """
        cache = dynamic_cache.DynamicCache([arena_dim])

        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in cache.gen_attr_changelist()[0]]
        rms = cache.gen_tag_rmlist()
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
        nest_pose = ev.nest_pose.NestPose(dist_type, [arena_dim])
        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in nest_pose.gen_attr_changelist()[0]]
        rms = nest_pose.gen_tag_rmlist()
        if rms:  # non-empty
            [xml_luigi.tag_remove(a) for a in rms[0]]

    def generate_arena_shape(self, xml_luigi: XMLLuigi, shape: ev.arena_shape.RectangularArena):
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

    def generate_static_cache(self, xml_luigi: XMLLuigi, arena_dim: tp.Tuple[int, int, int]):
        """
        Generate XML changes for static cache usage (depth1 simulations only).

        Does not write generated changes to the simulation definition pickle file.
        """

        # If they specified how many blocks to use for static cache respawn, use that.
        # Otherwise use the floor of 2.
        if self.cmdopts['static_cache_blocks'] is None:
            cache = static_cache.StaticCache([2], [arena_dim])
        else:
            cache = static_cache.StaticCache([self.cmdopts['static_cache_blocks']],
                                             [arena_dim])

        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in cache.gen_attr_changelist()[0]]
        rms = cache.gen_tag_rmlist()
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
