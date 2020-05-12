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


import core.generators.scenario_generator as sg
import plugins.fordyca.generators.common as gc
from core.utils import ArenaExtent as ArenaExtent


class SSGenerator(sg.SSGenerator):
    """
    FORDYCA extensions to the single source foraging generator
    :class:`~core.generators.scenario_generator.SSGenerator`.

    This includes:

    - Static caches
    - Dynamic caches

    """

    def __init__(self, *args, **kwargs):
        sg.SSGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()
        arena_dim = self.cmdopts['arena_dim']

        if "depth1" in self.controller:
            gc.generate_static_cache(exp_def, ArenaExtent(dims=arena_dim), self.cmdopts)
        if "depth2" in self.controller:
            gc.generate_dynamic_cache(exp_def, ArenaExtent(dims=arena_dim))

        self.generate_physics(exp_def,
                              self.cmdopts,
                              self.cmdopts['physics_engine_type2D'],
                              self.cmdopts['physics_n_engines'],
                              [ArenaExtent(dims=arena_dim)])

        gc.generate_nest_pose(exp_def, ArenaExtent(dims=arena_dim), "single_source")

        return exp_def


class DSGenerator(sg.DSGenerator):
    """
    FORDYCA extensions to the single source foraging generator
    :class:`~core.generators.single_source.DSGenerator`.

    This includes:

    - Static caches
    - Dynamic caches

    """

    def __init__(self, *args, **kwargs):
        sg.DSGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()
        arena_dim = self.cmdopts['arena_dim']

        if "depth1" in self.controller:
            gc.generate_static_cache(exp_def, ArenaExtent(dims=arena_dim), self.cmdopts)
        if "depth2" in self.controller:
            gc.generate_dynamic_cache(exp_def, ArenaExtent(dims=arena_dim))

        self.generate_physics(exp_def,
                              self.cmdopts,
                              self.cmdopts['physics_engine_type2D'],
                              self.cmdopts['physics_n_engines'],
                              [ArenaExtent(dims=arena_dim)])

        gc.generate_nest_pose(exp_def, ArenaExtent(dims=arena_dim), "dual_source")

        return exp_def


class QSGenerator(sg.QSGenerator):
    """
    FORDYCA extensions to the single source foraging generator
    :class:`~core.generators.scenario_generator.QSGenerator`.

    This includes:

    - Static caches
    - Dynamic caches

    """

    def __init__(self, *args, **kwargs):
        sg.QSGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()
        arena_dim = self.cmdopts['arena_dim']

        if "depth1" in self.controller:
            gc.generate_static_cache(exp_def, ArenaExtent(dims=arena_dim), self.cmdopts)
        if "depth2" in self.controller:
            gc.generate_dynamic_cache(exp_def, ArenaExtent(dims=arena_dim))

        self.generate_physics(exp_def,
                              self.cmdopts,
                              self.cmdopts['physics_engine_type2D'],
                              self.cmdopts['physics_n_engines'],
                              [ArenaExtent(dims=arena_dim)])

        gc.generate_nest_pose(exp_def, ArenaExtent(dims=arena_dim), "quad_source")

        return exp_def


class RNGenerator(sg.RNGenerator):
    """
    FORDYCA extensions to the single source foraging generator
    :class:`~core.generators.scenario_generator.RNGenerator`.

    This includes:

    - Static caches
    - Dynamic caches

    """

    def __init__(self, *args, **kwargs):
        sg.RNGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()
        arena_dim = self.cmdopts['arena_dim']

        if "depth1" in self.controller:
            gc.generate_static_cache(exp_def, ArenaExtent(dims=arena_dim), self.cmdopts)
        if "depth2" in self.controller:
            gc.generate_dynamic_cache(exp_def, ArenaExtent(dims=arena_dim))

        self.generate_physics(exp_def,
                              self.cmdopts,
                              self.cmdopts['physics_engine_type2D'],
                              self.cmdopts['physics_n_engines'],
                              [ArenaExtent(dims=arena_dim)])

        gc.generate_nest_pose(exp_def, ArenaExtent(dims=arena_dim), "random")

        return exp_def


class PLGenerator(sg.PLGenerator):
    """
    FORDYCA extensions to the single source foraging generator
    :class:`~core.generators.scenario_generator.PLGenerator`.

    This includes:

    - Static caches
    - Dynamic caches

    """

    def __init__(self, *args, **kwargs):
        sg.PLGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()
        arena_dim = self.cmdopts['arena_dim']

        if "depth1" in self.controller:
            gc.generate_static_cache(exp_def, ArenaExtent(dims=arena_dim), self.cmdopts)
        if "depth2" in self.controller:
            gc.generate_dynamic_cache(exp_def, ArenaExtent(dims=arena_dim))

        self.generate_physics(exp_def,
                              self.cmdopts,
                              self.cmdopts['physics_engine_type2D'],
                              self.cmdopts['physics_n_engines'],
                              [ArenaExtent(dims=arena_dim)])

        gc.generate_nest_pose(exp_def, ArenaExtent(dims=arena_dim), "powerlaw")

        return exp_def
