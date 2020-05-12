# Copyright 2019 John Harwell, All rights reserved.
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

"""
Extensions to :class:`core.generators.BaseScenarioGenerator` common to all FORDYCA scenarios.
"""

import typing as tp

from core.utils import ArenaExtent as ArenaExtent
from plugins.fordyca.variables import dynamic_cache, static_cache, nest_pose
from core.xml_luigi import XMLLuigi


def generate_dynamic_cache(xml_luigi: XMLLuigi, extent: ArenaExtent):
    """
    Generate XML changes for dynamic cache usage (depth2 simulations only).

    Does not write generated changes to the simulation definition pickle file.
    """
    cache = dynamic_cache.DynamicCache([extent])

    [xml_luigi.attr_change(a[0], a[1], a[2]) for a in cache.gen_attr_changelist()[0]]
    rms = cache.gen_tag_rmlist()
    if rms:  # non-empty
        [xml_luigi.tag_remove(a) for a in rms[0]]


def generate_nest_pose(exp_def: XMLLuigi, extent: ArenaExtent, dist_type: str):
    """
    Generate XML changes for the specified arena dimensions and block distribution type to
    properly place the nest.

    Does not write generated changes to the simulation definition pickle file.
    """
    np = nest_pose.NestPose(dist_type, [extent])
    [exp_def.attr_change(a[0], a[1], a[2]) for a in np.gen_attr_changelist()[0]]
    rms = np.gen_tag_rmlist()
    if rms:  # non-empty
        [exp_def.tag_remove(a) for a in rms[0]]


def generate_static_cache(xml_luigi: XMLLuigi,
                          extent: ArenaExtent,
                          cmdopts: tp.Dict[str, str]):
    """
    Generate XML changes for static cache usage (depth1 simulations only).

    Does not write generated changes to the simulation definition pickle file.
    """

    # If they specified how many blocks to use for static cache respawn, use that.
    # Otherwise use the floor of 2.
    if cmdopts['static_cache_blocks'] is None:
        cache = static_cache.StaticCache([2], [extent])
    else:
        cache = static_cache.StaticCache([cmdopts['static_cache_blocks']],
                                         [extent])

    [xml_luigi.attr_change(a[0], a[1], a[2]) for a in cache.gen_attr_changelist()[0]]
    rms = cache.gen_tag_rmlist()
    if rms:  # non-empty
        [xml_luigi.tag_remove(a) for a in rms[0]]
