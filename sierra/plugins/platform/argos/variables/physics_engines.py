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

"""Classes mapping an extent to a set of non-overlapping ARGoS physics engines.

Extent does not have to be the whole arena. 2D and 3D engines.

"""

# Core packages
import typing as tp
import logging

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.utils import ArenaExtent
from sierra.core.experiment import xml
from sierra.core import types, config


@implements.implements(IBaseVariable)
class PhysicsEngines():
    """Defines 2D/3D physics engines within ARGoS and how they are laid out.

    Attributes:

        engine_type: The type of physics engine to use (one supported by ARGoS).

        n_engines: # of engines. Can be one of [1,4,8,16,24].

        iter_per_tick: # of iterations physics engines should perform per tick.
                       layout: Engine arrangement method. Can be one of:

                       - ``uniform_grid2D``: Arrange the engines in a uniform 2D
                         grid that extends up to the maximum height in Z. For 2D
                         engines, this is the maximum height of objects that can
                         be present in the arena (I think).

        extents: List of (X,Y,Zs) tuple of dimensions of area to assign to
                 engines of the specified type.

    """

    def __init__(self,
                 engine_type: str,
                 n_engines: int,
                 iter_per_tick: int,
                 layout: str,
                 extents: tp.List[ArenaExtent]) -> None:

        self.engine_type = engine_type
        self.n_engines = n_engines
        self.iter_per_tick = iter_per_tick
        self.layout = layout
        self.extents = extents
        self.tag_adds = []  # type: tp.List[xml.TagAddList]

        # If we are given multiple extents to map, we need to divide the
        # specified # of engines among them.
        self.n_engines = int(self.n_engines / float(len(self.extents)))
        assert self.layout == 'uniform_grid2D',\
            "Only uniform_grid2D physics engine layout currently supported"

        self.logger = logging.getLogger(__name__)

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        """
        No effect.

        All tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self) -> tp.List[xml.TagRmList]:
        """Remove the ``<physics_engines>`` tag if it exists may be desirable.

        Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [xml.TagRmList(xml.TagRm(".", "./physics_engines"))]

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        self.logger.debug("Mapping %s physics engines of type %s to extents=%s",
                          self.n_engines,
                          self.engine_type,
                          [str(s) for s in self.extents])
        if not self.tag_adds:
            if self.n_engines == 1:
                self.tag_adds = [self._gen1_engines()]
            elif self.n_engines == 2:
                self.tag_adds = [self._gen2_engines(s) for s in self.extents]
            elif self.n_engines == 4:
                self.tag_adds = [self._gen4_engines(s) for s in self.extents]
            elif self.n_engines == 6:
                self.tag_adds = [self._gen6_engines(s) for s in self.extents]
            elif self.n_engines == 8:
                self.tag_adds = [self._gen8_engines(s) for s in self.extents]
            elif self.n_engines == 12:
                self.tag_adds = [self._gen12_engines(s) for s in self.extents]
            elif self.n_engines == 16:
                self.tag_adds = [self._gen16_engines(s) for s in self.extents]
            elif self.n_engines == 24:
                self.tag_adds = [self._gen24_engines(s) for s in self.extents]
            else:
                raise RuntimeError(
                    "Bad # of physics engines specified: {0}".format(self.n_engines))

        return self.tag_adds

    def gen_files(self) -> None:
        pass

    def _gen_all_engines(self,
                         extent: ArenaExtent,
                         n_engines_x: int,
                         n_engines_y: int,
                         forward_engines: tp.List[int]) -> xml.TagAddList:
        """Generate definitions for the specified # of engines for the extent.

        """
        adds = xml.TagAddList(xml.TagAdd('.', 'physics_engines', {}, False))

        for i in range(0, self.n_engines):
            adds.extend(self.gen_single_engine(i,
                                               extent,
                                               n_engines_x,
                                               n_engines_y,
                                               forward_engines))

        return adds

    def gen_single_engine(self,
                          engine_id: int,
                          extent: ArenaExtent,
                          n_engines_x: int,
                          n_engines_y: int,
                          forward_engines: tp.List[int]) -> xml.TagAddList:
        """
        Generate definitions for a specific 2D/3D engine.

        Volume is *NOT* divided equally among engines, but rather each of the
        engines is extended up to some maximum height in Z, forming a set of
        "silos".

        Arguments:

            engine_id: Numerical UUID for the engine.

            extent: The mapped extent for ALL physics engines.

            exceptions: List of lists of points defining polygons which should
                        NOT be managed by any of the engines currently being
                        processed.

            n_engines_x: # engines in the x direction.

            n_engines_y: # engines in the y direction.

            forward_engines: IDs of engines that are placed in increasing order
                             in X when layed out L->R.

        """

        adds = xml.TagAddList()

        size_x = extent.xsize() / n_engines_x
        size_y = extent.ysize() / n_engines_y
        size_z = extent.zsize()

        name = self._gen_engine_name(engine_id)

        adds.append(xml.TagAdd('.//physics_engines',
                               self.engine_type,
                               {
                                   'id': name,
                                   'iterations': str(self.iter_per_tick)
                               },
                               True))
        adds.append(xml.TagAdd(f".//physics_engines/*[@id='{name}']",
                               "boundaries",
                               {},
                               True))
        adds.append(xml.TagAdd(f".//physics_engines/*[@id='{name}']/boundaries",
                               "top",
                               {
                                   'height': str(size_z)
                               },
                               True))
        adds.append(xml.TagAdd(f".//physics_engines/*[@id='{name}']/boundaries",
                               "bottom",
                               {
                                   'height': '0.0'
                               },
                               True))
        adds.append(xml.TagAdd(f".//physics_engines/*[@id='{name}']/boundaries",
                               "sides",
                               {},
                               True))

        # Engine lower X coord increasing as engine id increases
        if engine_id in forward_engines:
            ll_x = extent.ll.x + size_x * (engine_id % n_engines_x)
            lr_x = extent.ll.x + size_x * ((engine_id % n_engines_x) + 1)

        else:  # Engine lower X coord increasing as engine id DECREASES
            ll_x = extent.ll.x + size_x * \
                (n_engines_x - (engine_id % n_engines_x) - 1)
            lr_x = extent.ll.x + size_x * \
                ((n_engines_x - (engine_id % n_engines_x) - 1) + 1)

        ur_x = lr_x
        ul_x = ll_x

        # We use the max of # engines in X/Y to get the nice numbering/layout of
        # engines.
        ll_y = extent.ll.y + size_y * \
            (int(engine_id / max(n_engines_x, n_engines_y)))
        ul_y = extent.ll.y + size_y * \
            (int(engine_id / max(n_engines_x, n_engines_y)) + 1)

        lr_y = ll_y
        ur_y = ul_y

        # Adjust vertex list to account for any overlap with entries on the
        # exception list
        vertices = [(ll_x, ll_y), (lr_x, lr_y), (ur_x, ur_y), (ul_x, ul_y)]

        for v in vertices:
            adds.append(xml.TagAdd(f".//physics_engines/*[@id='{name}']/boundaries/sides",
                                   "vertex",
                                   {
                                       "point": "{0}, {1}".format(v[0], v[1])
                                   },
                                   True))
        return adds

    def _gen1_engines(self) -> xml.TagAddList:
        """Generate definitions for 1 physics engine for the specified extent.

        """

        name = self._gen_engine_name(0)

        return xml.TagAddList(xml.TagAdd('.', 'physics_engines', {}, False),
                              xml.TagAdd(".//physics_engines",
                                         self.engine_type,
                                         {
                                             'id': name
                                         },
                                         True))

    def _gen2_engines(self, extent: ArenaExtent) -> xml.TagAddList:
        """Generate definitions for 2 physics engines for the specified extents.

        Engines are layed out as follows in 2D, regardless if they are 2D or 3D
        engines:

         0 1

        Volume is *NOT* divided equally among 3D engines, but rather each of the
        engines is extended up to some maximum height in Z, forming a set of
        "silos".

        """
        return self._gen_all_engines(extent,
                                     n_engines_x=2,
                                     n_engines_y=1,
                                     forward_engines=[])

    def _gen4_engines(self, extent: ArenaExtent) -> xml.TagAddList:
        """Generate definitions for 4 physics engines for the specified extent.

        Engines are layed out as follows in 2D, regardless if they are 2D or 3D
        engines:

         3 2
         0 1

        Volume is *NOT* divided equally among 3D engines, but rather each of the
        engines is extended up to some maximum height in Z, forming a set of
        "silos".

        """
        return self._gen_all_engines(extent,
                                     n_engines_x=2,
                                     n_engines_y=2,
                                     forward_engines=[0, 1])

    def _gen6_engines(self, extent: ArenaExtent) -> xml.TagAddList:
        """Generate definitions for 6 physics engines for the specified extent.

        Engines are layed out as follows in 2D, regardless if they are 2D or 3D
        engines:

         5 4 3
         0 1 2

        Volume is *NOT* divided equally among 3D engines, but rather each of the
        engines is extended up to some maximum height in Z, forming a set of
        "silos".

        """
        return self._gen_all_engines(extent,
                                     n_engines_x=3,
                                     n_engines_y=2,
                                     forward_engines=[0, 1, 2])

    def _gen8_engines(self, extent: ArenaExtent) -> xml.TagAddList:
        """Generate definitions for 8 physics engines for the specified extent.

        The 2D layout is:

        7 6 5 4
        0 1 2 3

        Volume is *NOT* divided equally among 3D engines, but rather each of the
        engines is extended up to some maximum height in Z, forming a set of
        "silos".

        """
        return self._gen_all_engines(extent,
                                     n_engines_x=4,
                                     n_engines_y=2,
                                     forward_engines=[0, 1, 2, 3])

    def _gen12_engines(self, extent: ArenaExtent) -> xml.TagAddList:
        """Generate definitions for 12 physics engines for the specified extent.

        The 2D layout is:

        8  9  10 11
        7  6  5  4
        0  1  2  3

        Volume is *NOT* divided equally among 3D engines, but rather each of the
        engines is extended up to some maximum height in Z, forming a set of
        "silos".

        """
        return self._gen_all_engines(extent,
                                     n_engines_x=4,
                                     n_engines_y=3,
                                     forward_engines=[0, 1, 2, 3, 8, 9, 10, 11])

    def _gen16_engines(self, extent: ArenaExtent) -> xml.TagAddList:
        """Generate definitions for 16 physics engines for the specified extent.

        The 2D layout is:

        15 14 13 12
        8  9  10 11
        7  6  5  4
        0  1  2  3

        Volume is *NOT* divided equally among 3D engines, but rather each of the
        engines is extended up to some maximum height in Z, forming a set of
        "silos".

        """
        return self._gen_all_engines(extent,
                                     n_engines_x=4,
                                     n_engines_y=4,
                                     forward_engines=[0, 1, 2, 3, 8, 9, 10, 11])

    def _gen24_engines(self, extent: ArenaExtent) -> xml.TagAddList:
        """Generate definitions for 16 physics engines for the specified extent.

        The 2D layout is:

        23  22 21  20 19 18
        12  13 14  15 16 17
        11  10  9  8  7  6
        0   1   2  3  4  5

        Volume is *NOT* divided equally among 3D engines, but rather each of the
        engines is extended up to some maximum height in Z, forming a set of
        "silos".

        """
        return self._gen_all_engines(extent,
                                     n_engines_x=6,
                                     n_engines_y=4,
                                     forward_engines=[0, 1, 2, 3, 4, 5, 12, 13, 14, 15, 16, 17])

    def _gen_engine_name(self, engine_id: int) -> str:
        """Generate the unique ID for an engine.

        ID is comprised of a type + numeric identifier of the engine.

        """
        return self._gen_engine_name_stem() + str(engine_id)

    def _gen_engine_name_stem(self) -> str:
        """
        Generate the name stem for the specified engine type.
        """
        if self.engine_type == 'dynamics3d':
            return 'dyn3d'
        elif self.engine_type == 'pointmass3d':
            return 'pm3d'
        elif self.engine_type == 'dynamics2d':
            return 'dyn2d'
        else:
            raise NotImplementedError


class PhysicsEngines2D(PhysicsEngines):
    """
    Specialization of :class:`PhysicsEngines` for 2D.
    """

    def __init__(self,
                 engine_type: str,
                 n_engines: int,
                 spatial_hash_info: tp.Optional[tp.Dict[str, tp.Any]],
                 iter_per_tick: int,
                 layout: str,
                 extents: tp.List[ArenaExtent]) -> None:
        PhysicsEngines.__init__(self,
                                engine_type,
                                n_engines,
                                iter_per_tick,
                                layout,
                                extents)

        self.spatial_hash_info = spatial_hash_info

    def gen_single_engine(self,
                          engine_id: int,
                          extent: ArenaExtent,
                          n_engines_x: int,
                          n_engines_y: int,
                          forward_engines: tp.List[int]) -> xml.TagAddList:
        adds = super().gen_single_engine(engine_id,
                                         extent,
                                         n_engines_x,
                                         n_engines_y,
                                         forward_engines)
        if self.engine_type == 'dynamics2d' and self.spatial_hash_info is not None:
            name = self._gen_engine_name(engine_id)
            adds.append(xml.TagAdd(f".//physics_engines/*[@id='{name}']",
                                   "spatial_hash",
                                   {
                                       'cell_size': str(self.spatial_hash_info['cell_size']),
                                       'cell_num': str(self.spatial_hash_info['cell_num'])
                                   },
                                   True))
        return adds


class PhysicsEngines3D(PhysicsEngines):
    """
    Specialization of :class:`PhysicsEngines` for 3D.
    """

    def __init__(self,
                 engine_type: str,
                 n_engines: int,
                 iter_per_tick: int,
                 layout: str,
                 extents: tp.List[ArenaExtent]) -> None:
        PhysicsEngines.__init__(self,
                                engine_type,
                                n_engines,
                                iter_per_tick,
                                layout,
                                extents)


def factory(engine_type: str,
            n_engines: int,
            n_robots: tp.Optional[int],
            robot_type: str,
            cmdopts: types.Cmdopts,
            extents: tp.List[ArenaExtent]) -> PhysicsEngines:
    """
    Create a physics engine mapping onto a list of arena extents for 2D or 3D.
    """
    # Right now the 2D and 3D variants are the same, but that is unlikely to
    # remain so in the future, so we employ a factory function to make
    # implementation of diverging functionality easier later.
    if '2d' in engine_type:
        if n_robots and cmdopts['physics_spatial_hash2D']:
            spatial_hash = {
                # Per ARGoS documentation in 'argos3 -q dynamics2d'
                'cell_size': config.kARGoS['spatial_hash2D'][robot_type],
                'cell_num': n_robots / float(n_engines) * 10
            }
            logging.debug(("Using 2D spatial hash for physics engines: "
                           "cell_size=%f,cell_num=%d"),
                          spatial_hash['cell_size'],
                          spatial_hash['cell_num'])
        else:
            spatial_hash = None

        return PhysicsEngines2D(engine_type,
                                n_engines,
                                spatial_hash,
                                cmdopts['physics_iter_per_tick'],
                                'uniform_grid2D',
                                extents)
    else:
        return PhysicsEngines3D(engine_type,
                                n_engines,
                                cmdopts['physics_iter_per_tick'],
                                'uniform_grid2D',
                                extents)


__api__ = [
    'PhysicsEngines',
    'PhysicsEngines2D',
    'PhysicsEngines3D',
]
