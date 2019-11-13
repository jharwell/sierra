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

"""
2D and 3D physics engine classes mapping a volumetric extent (does not have to be the whole arena)
to a set of physics engines arranged in some fashion within the volumetric extent to cover it
without overlap.

"""

import typing as tp
from variables.base_variable import BaseVariable


class PhysicsEngines(BaseVariable):
    """
    Base physics engine class doing most of the work.

    Attributes:
        engine_type: The type of physics engine to use (one supported by ARGoS).
        n_engines: # of engines. Can be one of [1,4,8,16,24].
        iter_per_tick: # of iterations physics engines should perform per tick.
        layout: Engine arrangement method. Can be one of:

                - ``uniform_grid2D``: Arrange the engines in a uniform 2D grid that extends up to
                  the maximum height in Z. For 2D engines, this is the maximum height of objects
                  that can be present in the arena (I think).

        extents: List of (X,Y,Z) tuples of extents onto which physics engines should be mapped.
    """

    def __init__(self,
                 engine_type: str,
                 n_engines: int,
                 iter_per_tick: int,
                 layout: str,
                 extents: tp.List[tp.Tuple[int, int, int]]):

        self.engine_type = engine_type
        self.n_engines = n_engines
        self.iter_per_tick = iter_per_tick
        self.layout = layout
        self.extents = extents

        assert self.layout == 'uniform_grid2D',\
            "FATAL: Only uniform_grid2D physics engine layout currently supported"

    def gen_attr_changelist(self):
        """
        Does nothing because all tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self):
        """
        Always remove the physics_engines tag if it exists so we are starting from a clean slate
        each time. Obviously you *must* call this function BEFORE adding new definitions.
        """
        return [set([(".", "./physics_engines")])]

    def gen_tag_addlist(self):
        if self.n_engines == 1:
            return [self.__gen1_engines(s) for s in self.extents]
        elif self.n_engines == 4:
            return [self.__gen4_engines(s) for s in self.extents]
        elif self.n_engines == 8:
            return [self.__gen8_engines(s) for s in self.extents]
        elif self.n_engines == 16:
            return [self.__gen16_engines(s) for s in self.extents]
        elif self.n_engines == 24:
            return [self.__gen24_engines(s) for s in self.extents]

        raise RuntimeError

    def __gen_engines(self,
                      dims: tp.Tuple[int, int, int],
                      n_engines_x: int,
                      n_engines_y: int,
                      forward_engines: tp.List[int]):
        """
        Generate definitions for the specified # of 3D physics engines for the specified pair of
        (X,Y) arena extents.

        dims: The arena extents.
        n_engines_x: # engines in the x direction.
        n_engines_y: # engines in the y direction.
        forward_engines: IDs of engines that are placed in increasing order in X when layed out
                         L->R.

        Volume is *NOT* divided equally among engines, but rather each of the engines is extended up
        to some maximum height in Z, forming a set of "silos".
        """
        adds = [('.', 'physics_engines', {})]

        size_x = dims[0] / n_engines_x
        size_y = dims[1] / n_engines_y
        size_z = dims[2]

        if self.engine_type == 'dynamics3d':
            name_stem = 'dyn3d'
        else:
            name_stem = 'dyn2d'

        for i in range(0, self.n_engines):
            name = name_stem + str(i)
            adds.append(('.//physics_engines',
                         self.engine_type, {'id': name,
                                            'iterations': str(self.iter_per_tick)}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]",
                         "boundaries", {}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "top", {'height': str(size_z)}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "bottom", {'height': '0.0'}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries",
                         "sides", {}))

            # Engine lower X coord increasing as engine id increases
            if i in forward_engines:
                ll_x = size_x * (i % n_engines_x)
                lr_x = size_x * ((i % n_engines_x) + 1)

            else:  # Engine lower X coord increasing as engine id DECREASES
                ll_x = size_x * (n_engines_x - (i % n_engines_x) - 1)
                lr_x = size_x * ((n_engines_x - (i % n_engines_x) - 1) + 1)

            ur_x = lr_x
            ul_x = ll_x

            # We use the max of # engines in X/Y to get the nice numbering/layout of engines.
            ll_y = size_y * (int(i / max(n_engines_x, n_engines_y)))
            ul_y = size_y * (int(i / max(n_engines_x, n_engines_y)) + 1)

            lr_y = ll_y
            ur_y = ul_y

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ll_x, ll_y)}))
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(lr_x, lr_y)}))

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ur_x, ur_y)}))

            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(ul_x, ul_y)}))
        return adds

    def __gen1_engines(self, dims: tp.Tuple[int, int]):
        """
        Generate definitions for 1 2D or 3D physics engine for the specified pair of (X,Y) arena
        extents.

        """

        if self.engine_type == 'dynamics3d':
            name = 'dyn3d'
        else:
            name = 'dyn2d'

        return [('.', 'physics_engines', {}),
                (".//physics_engines", self.engine_type, {'id': name})]

    def __gen4_engines(self, dims: tp.Tuple[int, int]):
        """
        Generate definitions for 4 2D or 3D physics engine for the specified pair of (X,Y) arena
        extents.

        The 2D layout is:

         3 2
         0 1

        Volume is *NOT* divided equally among engines, but rather each of the engines is extended up
        to some maximum height in Z, forming a set of "silos".
        """
        return self.__gen_engines(dims,
                                  n_engines_x=2,
                                  n_engines_y=2,
                                  forward_engines=[0, 1])

    def __gen8_engines(self, dims: tp.Tuple[int, int]):
        """
        Generate definitions for 8 2D or 3D physics engine for the specified pair of (X,Y) arena
        extents with a uniform grid layout.

        The 2D layout is:

        7 6 5 4
        0 1 2 3

        Volume is *NOT* divided equally among engines, but rather each of the engines is extended up
        to some maximum height in Z, forming a set of "silos".
        """
        return self.__gen_engines(dims,
                                  n_engines_x=4,
                                  n_engines_y=2,
                                  forward_engines=[0, 1, 2, 3])

    def __gen16_engines(self, dims: tp.Tuple[int, int]):
        """
        Generate definitions for 16 2D or 3D physics engine for the specified pair of (X,Y) arena
        extents with a uniform grid layout.

        The 2D layout is:

        15 14 13 12
        8  9  10 11
        7  6  5  4
        0  1  2  3

        Volume is *NOT* divided equally among engines, but rather each of the engines is extended up
        to some maximum height in Z, forming a set of "silos".
        """
        return self.__gen_engines(dims,
                                  n_engines_x=4,
                                  n_engines_y=4,
                                  forward_engines=[0, 1, 2, 3, 8, 9, 10, 11])

    def __gen24_engines(self, dims: tp.Tuple[int, int]):
        """
        Generate definitions for 16 2D or 3D physics engine for the specified pair of (X,Y) arena
        extents with a uniform grid layout.

        The 2D layout is:

        23  22 21  20 19 18
        12  13 14  15 16 17
        11  10  9  8  7  6
        0   1   2  3  4  5

        Volume is *NOT* divided equally among engines, but rather each of the engines is extended up
        to some maximum height in Z, forming a set of "silos".
        """
        return self.__gen_engines(dims,
                                  n_engines_x=6,
                                  n_engines_y=4,
                                  forward_engines=[0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17])


class PhysicsEngines2D(PhysicsEngines):
    """
    Specialization of :class:`PhysicsEngines` for 2D.
    """

    def __init__(self, *args):
        PhysicsEngines.__init__(self, *args)


class PhysicsEngines3D(PhysicsEngines):
    """
    Specialization of :class:`PhysicsEngines` for 3D.
    """

    def __init__(self, *args):
        PhysicsEngines.__init__(self, *args)


def Factory(cmdopts: tp.Dict[str, str],
            extents: tp.List[tp.Tuple[int, int, int]]):
    """
    Create a physics engine mapping onto an arena extent for 2D and 3D.
    """
    # Right now the 2D and 3D variants are the same, but that is unlikely to remain so in the
    # future, so we employ a factory function to make implementation of diverging functionality
    # easier later.
    if '2d' in cmdopts['physics_engine_type']:
        return PhysicsEngines2D(cmdopts['physics_engine_type'],
                                cmdopts['physics_n_engines'],
                                cmdopts['physics_iter_per_tick'],
                                'uniform_grid2D',
                                extents)
    else:
        return PhysicsEngines3D(cmdopts['physics_engine_type'],
                                cmdopts['physics_n_engines'],
                                cmdopts['physics_iter_per_tick'],
                                'uniform_grid2D',
                                extents)
