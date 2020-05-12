# Copyright 2020 John Harwell, All rights reserved.
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
Extensions to :class:`core.generators.BaseScenarioGenerator` common to all SILICON scenarios.
"""

import logging
import typing as tp

from core.utils import ArenaExtent
from core.xml_luigi import XMLLuigi
import core.generators.scenario_generator as sg

from plugins.silicon.variables import nest_pose


def generate_mixed_physics(exp_def: XMLLuigi,
                           cmdopts: tp.Dict[str, str],
                           zmax: int,
                           block_dist: str):
    """
    Generate mixed 2D/3D physics engine definitions for the arena, according to the specified block
    distribution configuration, maximum structure height, and # physics engines.
    """
    arena_dim = cmdopts['arena_dim']
    if cmdopts['physics_n_engines'] == 1:
        logging.warning("Cannot mix 2D/3D engines with only 1 engine: using 1 3D engine")
        n_engines_2D = 0
        n_engines_3D = 1
        extents_3D = [ArenaExtent(dims=arena_dim)]
        extents_2D = [None]

    else:
        n_engines_2D = int(cmdopts['physics_n_engines'] / 2.0)
        n_engines_3D = int(cmdopts['physics_n_engines'] / 2.0)

        if block_dist == 'single_source':
            # Construction area needs 3D physics, 2D OK for everything else. Allocating the first
            # 25% of the arena in X is more than is needed, but it is a reasonable first attempt at
            # mixing 2D/3D engines.
            extents_3D = [ArenaExtent(dims=(arena_dim[0] * 0.25,
                                            arena_dim[1],
                                            zmax))]
            extents_2D = [ArenaExtent(dims=(arena_dim[0] * 0.75,
                                            arena_dim[1],
                                            zmax),
                                      offset=(arena_dim[0] * 0.25, 0, 0))]
        elif block_dist == 'dual_source':
            # Construction area needs 3D physics, 2D OK for everything else. Allocating the middle
            # 26% of the arena in X is more than is needed, but it is a reasonable first attempt at
            # mixing 2D/3D engines. 26% rather than 25% because the 3D portion is in the middle of
            # the arena, with 74 / 2 = 37.5 %  of the arena with 2D physics on either side.
            extents_3D = [ArenaExtent(dims=(arena_dim[0] * 0.26,
                                            arena_dim[1],
                                            zmax),
                                      offset=(arena_dim[0] * 0.37,
                                              0.0,
                                              0.0))]

            extent_2D1 = ArenaExtent(dims=(arena_dim[0] * 0.37,
                                           arena_dim[1],
                                           zmax))
            extent_2D2 = ArenaExtent(dims=(arena_dim[0] * 0.37,
                                           arena_dim[1],
                                           zmax),
                                     offset=(arena_dim[0] * 0.63, 0.0, 0.0))
            extents_2D = [extent_2D1, extent_2D2]
        else:
            # The square arenas will with the nest in the center will be trickier to divide up so
            # that the 2D/3D split is as efficient as possible, so punting for now.
            raise NotImplementedError

    sg.BaseScenarioGenerator.generate_physics(exp_def,
                                              cmdopts,
                                              cmdopts['physics_engine_type3D'],
                                              n_engines_3D,
                                              extents_3D,
                                              True)
    sg.BaseScenarioGenerator.generate_physics(exp_def,
                                              cmdopts,
                                              cmdopts['physics_engine_type2D'],
                                              n_engines_2D,
                                              extents_2D,
                                              False)


def generate_nest_pose(exp_def: XMLLuigi, extent: ArenaExtent):
    """
    Generate XML changes for the specified target extent to properly place the nest under the
    construction target.

    Does not write generated changes to the simulation definition pickle file.
    """
    np = nest_pose.NestPose([extent])

    rms = np.gen_tag_rmlist()
    if rms:  # non-empty
        [exp_def.tag_remove(a[0], a[1]) for a in rms[0]]

    adds = np.gen_tag_addlist()
    if adds:  # non-empty
        [exp_def.tag_add(a[0], a[1], a[2]) for a in adds[0]]

    changes = np.gen_attr_changelist()
    if changes:  # non-empty
        [exp_def.attr_change(a[0], a[1], a[2]) for a in changes[0]]
