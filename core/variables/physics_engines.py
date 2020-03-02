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
import logging

from core.variables.base_variable import BaseVariable
from core.utils import ArenaExtent as ArenaExtent


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

        extents: List of (X,Y,Zs) tuple of dimensions of area to assign to engines of the specified
                 type.
    """

    def __init__(self,
                 engine_type: str,
                 n_engines: int,
                 iter_per_tick: int,
                 layout: str,
                 extents: tp.List[ArenaExtent]):

        self.engine_type = engine_type
        self.n_engines = n_engines
        self.iter_per_tick = iter_per_tick
        self.layout = layout
        self.extents = extents

        # If we are given multiple extents to map, we need to divide the specified # of engines
        # among them.
        self.n_engines = int(self.n_engines / float(len(self.extents)))
        assert self.layout == 'uniform_grid2D',\
            "FATAL: Only uniform_grid2D physics engine layout currently supported"

    def gen_attr_changelist(self):
        """
        Does nothing because all tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self):
        """
        Removing the ``<physics_engines>`` tag if it exists may be desirable so an option is
        provided to do so. Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [set([(".", "./physics_engines")])]

    def gen_tag_addlist(self):
        logging.debug("Mapping %s physics engines of type %s to extents=%s",
                      self.n_engines,
                      self.engine_type,
                      self.extents)
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
        else:
            raise RuntimeError("Bad # of physics engines specified: {0}".format(self.n_engines))

    def __gen_all_engines(self,
                          extent: ArenaExtent,
                          n_engines_x: int,
                          n_engines_y: int,
                          forward_engines: tp.List[int]):
        """
        Generate definitions for the specified # of 2D/3D physics engines for the specified arena
        extent.
        """
        adds = [('.', 'physics_engines', {})]

        for i in range(0, self.n_engines):
            adds.extend(self.__gen_single_engine(i,
                                                 extent,
                                                 n_engines_x,
                                                 n_engines_y,
                                                 forward_engines))

        return adds

    def __gen_single_engine(self,
                            engine_id: int,
                            extent: ArenaExtent,
                            n_engines_x: int,
                            n_engines_y: int,
                            forward_engines: tp.List[int]):
        """
        Generate definitions for a specific 2D/3D engine as a member of the mapping of the specified
        arena extent to one or more engines.

        Volume is *NOT* divided equally among engines, but rather each of the engines is extended up
        to some maximum height in Z, forming a set of "silos".

        Arguments:
            engine_id: Numerical UUID for the engine.
            extent: The mapped extent for ALL physics engines.
            exceptions: List of lists of points defining polygons which should NOT be managed by
                        any of the engines currently being processed.
            n_engines_x: # engines in the x direction.
            n_engines_y: # engines in the y direction.
            forward_engines: IDs of engines that are placed in increasing order in X when layed out
                             L->R.
        """

        adds = []

        size_x = extent.dims[0] / n_engines_x
        size_y = extent.dims[1] / n_engines_y
        size_z = extent.dims[2]

        name = self.__gen_engine_name(engine_id)

        adds.append(('.//physics_engines', self.engine_type, {'id': name,
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
        if engine_id in forward_engines:
            ll_x = extent.xmin + size_x * (engine_id % n_engines_x)
            lr_x = extent.xmin + size_x * ((engine_id % n_engines_x) + 1)

        else:  # Engine lower X coord increasing as engine id DECREASES
            ll_x = extent.offset[0] + size_x * (n_engines_x - (engine_id % n_engines_x) - 1)
            lr_x = extent.offset[0] + size_x * ((n_engines_x - (engine_id % n_engines_x) - 1) + 1)

        ur_x = lr_x
        ul_x = ll_x

        # We use the max of # engines in X/Y to get the nice numbering/layout of engines.
        ll_y = extent.ymin + size_y * (int(engine_id / max(n_engines_x, n_engines_y)))
        ul_y = extent.ymin + size_y * (int(engine_id / max(n_engines_x, n_engines_y)) + 1)

        lr_y = ll_y
        ur_y = ul_y

        # Adjust vertex list to account for any overlap with entries on the exception list
        vertices = [(ll_x, ll_y), (lr_x, lr_y), (ur_x, ur_y), (ul_x, ul_y)]

        for v in vertices:
            adds.append((".//physics_engines/*[@id='{0}'".format(name) + "]/boundaries/sides",
                         "vertex", {"point": "{0}, {1}".format(v[0], v[1])}))
        return adds

    def __gen1_engines(self, extent: ArenaExtent):
        """
        Generate definitions for 1 2D or 3D physics engine for the specified extents.

        """

        name = self.__gen_engine_name(0)

        return [('.', 'physics_engines', {}),
                (".//physics_engines", self.engine_type, {'id': name})]

    def __gen4_engines(self, extent: ArenaExtent):
        """
        Generate definitions for 4 2D or 3D physics engine for the specified extent.

        Engines are layed out as follows in 2D, regardless if they are 2D or 3D engines:

         3 2
         0 1

        Volume is *NOT* divided equally among engines, but rather each of the engines is extended up
        to some maximum height in Z, forming a set of "silos".
        """
        return self.__gen_all_engines(extent,
                                      n_engines_x=2,
                                      n_engines_y=2,
                                      forward_engines=[0, 1])

    def __gen8_engines(self, extent: tp.Tuple[int, int]):
        """
        Generate definitions for 8 2D or 3D physics engine for the specified pair of (X,Y) arena
        extents with a uniform grid layout.

        The 2D layout is:

        7 6 5 4
        0 1 2 3

        Volume is *NOT* divided equally among engines, but rather each of the engines is extended up
        to some maximum height in Z, forming a set of "silos".
        """
        return self.__gen_all_engines(extent,
                                      n_engines_x=4,
                                      n_engines_y=2,
                                      forward_engines=[0, 1, 2, 3])

    def __gen16_engines(self, extent: ArenaExtent):
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
        return self.__gen_all_engines(extent,
                                      n_engines_x=4,
                                      n_engines_y=4,
                                      forward_engines=[0, 1, 2, 3, 8, 9, 10, 11])

    def __gen24_engines(self, extent: ArenaExtent):
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
        return self.__gen_all_engines(extent,
                                      n_engines_x=6,
                                      n_engines_y=4,
                                      forward_engines=[0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17])

    def __gen_engine_name(self, engine_id: int):
        """
        Generate the unique string for an engine comprised of a type + numeric identifier of the
        engine.
        """
        return self.__gen_engine_name_stem() + str(engine_id)

    def __gen_engine_name_stem(self):
        """
        Generate the name stem for the specified engine type.
        """
        if self.engine_type == 'dynamics3d':
            return 'dyn3d'
        elif self.engine_type == 'pointmass3d':
            return 'pm3d'
        elif self.engine_type == 'dynamics2d':
            return 'dyn2d'


class PhysicsEngines2D(PhysicsEngines):
    """
    Specialization of :class:`PhysicsEngines` for 2D.
    """

    def __init__(self,
                 engine_type,
                 n_engines: int,
                 iter_per_tick: int,
                 layout: str,
                 extents: tp.List[tp.Tuple[int, int, int]]):
        PhysicsEngines.__init__(self,
                                engine_type,
                                n_engines,
                                iter_per_tick,
                                layout,
                                extents)


class PhysicsEngines3D(PhysicsEngines):
    """
    Specialization of :class:`PhysicsEngines` for 3D.
    """

    def __init__(self,
                 engine_type,
                 n_engines: int,
                 iter_per_tick: int,
                 layout: str,
                 extents: tp.List[tp.Tuple[int, int, int]]):
        PhysicsEngines.__init__(self,
                                engine_type,
                                n_engines,
                                iter_per_tick,
                                layout,
                                extents)


def factory(engine_type: str,
            n_engines: int,
            cmdopts: tp.Dict[str, str],
            extents: tp.List[ArenaExtent]):
    """
    Create a physics engine mapping onto a list of arena extents for 2D or 3D
    """
    # Right now the 2D and 3D variants are the same, but that is unlikely to remain so in the
    # future, so we employ a factory function to make implementation of diverging functionality
    # easier later.
    if '2d' in engine_type:
        return PhysicsEngines2D(engine_type,
                                n_engines,
                                cmdopts['physics_iter_per_tick'],
                                'uniform_grid2D',
                                extents)
    else:
        return PhysicsEngines3D(engine_type,
                                n_engines,
                                cmdopts['physics_iter_per_tick'],
                                'uniform_grid2D',
                                extents)
