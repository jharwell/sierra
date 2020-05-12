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

import core.generators.scenario_generator as sg
import plugins.silicon.generators.common as gc
import plugins.silicon.variables.construct_targets as ct


class SSGenerator(sg.SSGenerator):
    """
    SILICON extensions to the single source foraging generator
    :class:`~core.generators.scenario_generator.SSGenerator`.

    This includes:

    - Ramp construction targets
    - Rectprism construction targets

    """

    def __init__(self, *args, **kwargs):
        sg.SSGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()

        # Construction targets
        max_z = 0.0
        for t in self.cmdopts['construct_targets']:
            target = ct.factory(self.cmdopts, t, self.cmdopts['construct_targets'].index(t))
            max_z = max(max_z, target.structure['bb'][2])
            [exp_def.tag_remove(a[0], a[1]) for a in target.gen_tag_rmlist()[0]]
            [exp_def.tag_add(a[0], a[1], a[2])
             for addset in target.gen_tag_addlist() for a in addset]

            # Nest
            gc.generate_nest_pose(exp_def, target.extent)

        # Mixed 2D/3D physics
        gc.generate_mixed_physics(exp_def, self.cmdopts, max_z, 'single_source')

        return exp_def


class DSGenerator(sg.DSGenerator):
    """
    SILICON extensions to the single source foraging generator
    :class:`~core.generators.single_source.DSGenerator`.

    This includes:

    - Ramp construction targets
    - Rectprism construction targets

    """

    def __init__(self, *args, **kwargs):
        sg.DSGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()

        # Construction targets
        max_z = 0.0
        for t in self.cmdopts['construct_targets']:
            target = ct.factory(self.cmdopts, t, self.cmdopts['construct_targets'].index(t))
            max_z = max(max_z, target.structure['bb'][2])
            [exp_def.tag_remove(a[0], a[1]) for a in target.gen_tag_rmlist()[0]]
            [exp_def.tag_add(a[0], a[1], a[2])
             for addset in target.gen_tag_addlist() for a in addset]

            # Nest
            gc.generate_nest_pose(exp_def, target.extent)

        # Mixed 2D/3D physics
        gc.generate_mixed_physics(exp_def, self.cmdopts, max_z, 'dual_source')

        return exp_def


class QSGenerator(sg.QSGenerator):
    """
    SILICON extensions to the single source foraging generator
    :class:`~core.generators.scenario_generator.QSGenerator`.

    This includes:

    - Ramp construction targets
    - Rectprism construction targets

    """

    def __init__(self, *args, **kwargs):
        sg.QSGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()

        # Construction targets
        max_z = 0.0
        for t in self.cmdopts['construct_targets']:
            target = ct.factory(self.cmdopts, t, self.cmdopts['construct_targets'].index(t))
            max_z = max(max_z, target.structure['bb'][2])
            [exp_def.tag_remove(a[0], a[1]) for a in target.gen_tag_rmlist()[0]]
            [exp_def.tag_add(a[0], a[1], a[2])
             for addset in target.gen_tag_addlist() for a in addset]

            # Nest
            gc.generate_nest_pose(exp_def, target.extent)

        # Mixed 2D/3D physics
        gc.generate_mixed_physics(exp_def, self.cmdopts, max_z, 'quad_source')

        return exp_def


class RNGenerator(sg.RNGenerator):
    """
    SILICON extensions to the single source foraging generator
    :class:`~core.generators.scenario_generator.RNGenerator`.

    This includes:

    - Ramp construction targets
    - Rectprism construction targets

    """

    def __init__(self, *args, **kwargs):
        sg.RNGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()

        # Construction targets
        max_z = 0.0
        for t in self.cmdopts['construct_targets']:
            target = ct.factory(self.cmdopts, t, self.cmdopts['construct_targets'].index(t))
            max_z = max(max_z, target.structure['bb'][2])
            [exp_def.tag_remove(a[0], a[1]) for a in target.gen_tag_rmlist()[0]]
            [exp_def.tag_add(a[0], a[1], a[2])
             for addset in target.gen_tag_addlist() for a in addset]

            # Nest
            gc.generate_nest_pose(exp_def, target.extent)

        # Mixed 2D/3D physics
        gc.generate_mixed_physics(exp_def, self.cmdopts, max_z, 'random')

        return exp_def


class PLGenerator(sg.PLGenerator):
    """
    SILICON extensions to the single source foraging generator
    :class:`~core.generators.scenario_generator.PLGenerator`.

    This includes:

    - Ramp construction targets
    - Rectprism construction targets

    """

    def __init__(self, *args, **kwargs):
        sg.PLGenerator.__init__(self, *args, **kwargs)

    def generate(self):

        exp_def = super().generate()

        # Construction targets
        max_z = 0.0
        for t in self.cmdopts['construct_targets']:
            target = ct.factory(self.cmdopts, t, self.cmdopts['construct_targets'].index(t))
            max_z = max(max_z, target.structure['bb'][2])
            [exp_def.tag_remove(a[0], a[1]) for a in target.gen_tag_rmlist()[0]]
            [exp_def.tag_add(a[0], a[1], a[2])
             for addset in target.gen_tag_addlist() for a in addset]

            # Nest
            gc.generate_nest_pose(exp_def, target.extent)

        # Mixed 2D/3D physics
        gc.generate_mixed_physics(exp_def, self.cmdopts, max_z, 'powerlaw')

        return exp_def
