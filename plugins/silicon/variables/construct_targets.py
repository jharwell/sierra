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
Construction target classes for defining the volumetric extent of one or more structures to be built
during simulation.

Definition:
    class.AxBxC@D,E

    - class - {ramp|rectprism}. ``ramp`` is a sloped structure that robots can drive
      up. ``rectprism`` is a rectangular prism which robots cannot (yet) drive up.

    - AxBxC - The X,Y,Z dimensions of the bounding box for the chosen structure (this defines its
              size).

    - D,E - The X,Y location in the arena of the anchor/origin of the structure (lower left corner
      of structure by convention).

Examples:
    - ``ramp.8x8x4@4,4``: A square ramp structure 4 units tall anchored on its lower left corner at
      4,4.

Note that this variable does NOT currently allow specification of the structure orientation.

"""

import re
import typing as tp

from core.variables.base_variable import BaseVariable


class BaseConstructTarget(BaseVariable):
    """
    Base Construction target class defining one or more 3D structures to be built.

    Attributes:
        structure: Dictionary of (key,value) pairs defining the structure, as returned by
                   :class:`~plugins.silicon.variables.construct_targets.ConstructTargetParser`.

        orientation: ``X`` or ``Y``, defining the axis in the arena to use as the X axis for
                     structure generation.

        target_id: Numerical UUID for the structure.

    """

    def __init__(self,
                 structure: dict,
                 orientation: str,
                 target_id: int):

        self.structure = structure
        self.orientation = orientation
        self.target_id = target_id

    def gen_attr_changelist(self):
        """
        Does nothing because all tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self):
        """
        Always remove the ``<construct_targets>`` tag if it exists so we are starting from a clean
        slate each time. Obviously you *must* call this function BEFORE adding new
        definitions. Because both robots and loop functions need the full structure definition, we
        remove it from each.
        """
        return [set([(".//params", "./construct_targets"),
                     (".//loop_functions", "./construct_targets")])]

    def gen_tag_addlist(self):
        return self.gen_target_and_subtargets(self.structure, self.target_id)

    def gen_target_and_subtargets(self,
                                  structure: tp.Tuple[str, tuple, tuple],
                                  target_id: int):
        """
        Generate definitions for the specified # of construct subtargets for the specified
        construction target.

        Arguments:
            structure: The structure to generate definitions for.
            target_id: Numerical UUID for the structure type.
        """

        target_name = structure['type'] + str(target_id)

        loop_adds = self.gen_target('loop_functions',
                                    target_name,
                                    self.orientation,
                                    structure['bb'],
                                    structure['anchor'])

        controller_adds = self.gen_target('params',
                                          target_name,
                                          self.orientation,
                                          structure['bb'],
                                          structure['anchor'])
        return [loop_adds, controller_adds]


class RampConstructTarget(BaseConstructTarget):
    """
    Construction target class for 3D ramps.
    """

    """
    The ratio between the length of cube blocks and ramp blocks.
    """
    kRAMP_LENGTH_RATIO = 2

    def __init__(self, *args, **kwargs):
        BaseConstructTarget.__init__(self, *args, **kwargs)
        self.__structure_sanity_checks(self.structure)

    def __structure_sanity_checks(self, structure: dict):
        bb = structure['bb']
        anchor = structure['anchor']

        if self.orientation == 'X':
            assert (bb[0] - anchor[0]) % RampConstructTarget.kRAMP_LENGTH_RATIO == 0,\
                "FATAL: X size {0} not a multiple for ramp block length ratio {1}".format(bb[0] - anchor[0],
                                                                                          RampConstructTarget.kRAMP_LENGTH_RATIO)
        else:
            assert (bb[1] - anchor[1]) % RampConstructTarget.kRAMP_LENGTH_RATIO == 0,\
                "FATAL: Y size {0} not a multiple for ramp block length ratio {1}".format(bb[1] - anchor[1],
                                                                                          RampConstructTarget.kRAMP_LENGTH_RATIO)

    def gen_target(self,
                   xml_parent: str,
                   target_name: str,
                   orientation: str,
                   bb: tp.Tuple[int, int, int],
                   anchor: tp.Tuple[int, int]):
        """
        Generate the lists of cube and ramp blocks that comprise the ramp structure, and add them to
        the XML definitions for the construction target.
        """
        adds = [('.//{0}'.format(xml_parent), 'construct_targets', {})]

        adds.append(('.//{0}/construct_targets'.format(xml_parent),
                     'ramp',
                     {'id': target_name,
                      'bounding_box': "{0},{1},{2}".format(bb[0], bb[1], bb[2]),
                      'anchor': "{0},{1},0".format(anchor[0], anchor[1]),
                      'orientation': orientation}))
        adds.append((".//{0}/construct_targets/*[@id='{1}'".format(xml_parent, target_name) + "]",
                     "ramp_blocks",
                     {}))
        adds.append((".//{0}/construct_targets/*[@id='{1}'".format(xml_parent, target_name) + "]",
                     "cube_blocks",
                     {}))

        # First, construct the list of ramp blocks.
        ramp_list = RampConstructTarget.__gen_ramp_blocks(orientation, bb)
        for i, block in enumerate(ramp_list):
            adds.append((".//{0}/construct_targets/*[@id='{1}'".format(xml_parent,
                                                                       target_name) + "]/ramp_blocks",
                         "ramp_block",
                         {'cell': '{0},{1},{2}'.format(block[0],
                                                       block[1],
                                                       block[2])}))
        # Next, construct the list of cube blocks
        cube_list = RampConstructTarget.__gen_cube_blocks(orientation, bb)
        for i, block in enumerate(cube_list):
            adds.append((".//{0}/construct_targets/*[@id='{1}'".format(xml_parent,
                                                                       target_name) + "]/cube_blocks",
                         "cube_block",
                         {'cell': '{0},{1},{2}'.format(block[0],
                                                       block[1],
                                                       block[2])}))
        return adds

    @staticmethod
    def __gen_ramp_blocks(orientation: str,
                          bb: tp.Tuple[int, int, int]):
        """
        Return the list of ramp blocks that will be part of the ramp construction target, given its
        bounding box and location in the arena.
        """
        ramp_list = []
        ratio = RampConstructTarget.kRAMP_LENGTH_RATIO

        if orientation == "X":
            for x in range(0, bb[0], ratio):
                zval = int(-x / ratio + bb[2])
                for y in range(0, bb[1]):
                    # -1 is for the height of the ramp block; the zval eqn gives the value of the
                    # bottom left corner
                    ramp_list.append((x, y, zval - 1))
        else:
            for y in range(0, bb[1], ratio):
                zval = int(-y / ratio + bb[2])

                for x in range(0, bb[0]):
                    # -1 is for the height of the ramp block; the zval eqn gives the value of the
                    # bottom left corner
                    ramp_list.append((x, y, zval - 1))
        return ramp_list

    @staticmethod
    def __gen_cube_blocks(orientation: str,
                          bb: tp.Tuple[int, int, int]):
        """
        Return the list of cube blocks that will be part of the ramp construction target, given its
        bounding box and location in the arena.
        """
        cube_list = []
        ratio = RampConstructTarget.kRAMP_LENGTH_RATIO

        if orientation == "X":
            for x in range(0, int(bb[0])):
                # The height in z UNDER a ramp block of a specified L is the same for all X
                # underneath it, BUT only one of the cells under the ramp block will have an X that
                # will interspect the Z = mx + b line of the ramp slope at an integer. We obtain
                # this value and use it to calculate the necessary height in Z for all X under the
                # block; the Z = mx + b equation does not (easily) work with rounding fractional
                # values if you try to plug EACH X into the equation.
                #
                # The -1 is for the height of the ramp block.
                eff_x = int(int(x / ratio) * ratio)
                zval = int(-eff_x / ratio + bb[2]) - 1
                for z in range(0, zval):
                    for y in range(0, bb[1]):
                        cube_list.append((x, y, z))
        else:
            for y in range(0, bb[1]):
                # The height in z UNDER a ramp block of a specified L is the same for all Y
                # underneath it, BUT only one of the cells under the ramp block will have an Y that
                # will interspect the Z = mx + b line of the ramp slope at an integer. We obtain
                # this value and use it to calculate the necessary height in Z for all Y under the
                # block; the Z = mx + b equation does not (easily) work with rounding fractional
                # values if you try to plug EACH Y into the equation.
                #
                # The -1 is for the height of the ramp block.
                eff_y = int(int(y / ratio) * ratio)
                zval = int(-eff_y / ratio + bb[2]) - 1

                # -1 is for the height of the ramp block; the zval eqn gives the value of the
                # bottom left corner
                for z in range(0, zval):
                    for x in range(0, bb[0]):
                        cube_list.append((x, y, z))

        return cube_list


class RectprismConstructTarget(BaseConstructTarget):
    """
    Construction target class for 3D rectangular prismatic structures.
    """

    def gen_target(self,
                   xml_parent: str,
                   target_name: str,
                   orientation: str,
                   bb: tp.Tuple[int, int, int],
                   anchor: tp.Tuple[int, int]):
        """
        Generate the lists of cube and ramp blocks that comprise the ramp structure, and add them to
        the XML definitions for the construction target.
        """
        adds = [('.//{0}'.format(xml_parent), 'construct_targets', {})]

        adds.append(('.//{0}/construct_targets'.format(xml_parent),
                     'rectprism',
                     {'id': target_name,
                      'bounding_box': "{0},{1},{2}".format(bb[0], bb[1], bb[2]),
                      'anchor': "{0},{1},0".format(anchor[0], anchor[1]),
                      'orientation': orientation}))
        adds.append((".//{0}/construct_targets/*[@id='{1}'".format(xml_parent, target_name) + "]",
                     "cube_blocks",
                     {}))

        # Construct the list of cube blocks
        cube_list = RectprismConstructTarget.__gen_cube_blocks(orientation, bb)
        for i, block in enumerate(cube_list):
            adds.append((".//{0}/construct_targets/*[@id='{1}'".format(xml_parent,
                                                                       target_name) + "]/cube_blocks",
                         "cube_block",
                         {'cell': '{0},{1},{2}'.format(block[0],
                                                       block[1],
                                                       block[2])}))
        return adds

    @staticmethod
    def __gen_cube_blocks(orientation: str, bb: tp.Tuple[int, int, int]):
        """
        Return the list of cube blocks that will be part of the prismatic construction target, given
        its bounding box and location in the arena.
        """
        cube_list = []

        if orientation == "X":
            for x in range(0, bb[0]):
                for y in range(0, bb[1]):
                    for z in range(0, bb[2]):
                        cube_list.append((x, y, z))
        else:
            for x in range(0, bb[1]):
                for y in range(0, bb[0]):
                    for z in range(0, bb[2]):
                        cube_list.append((x, y, z))

        return cube_list


class ConstructTargetParser():
    """
    Enforces the cmdline definition of the variable described in the module docstring.
    """

    def __call__(self, cmdline_str: str) -> dict:
        """
        Returns:
            Dictionary with keys:
                type: ramp|rectprism
                bb: (X,Y,Z)
                anchor: (X,Y)

        """
        ret = {}

        # Parse target type
        res = re.search(r"ramp|rectprism", cmdline_str)
        assert res is not None, "Bad target type specification in {0}".format(cmdline_str)
        ret['type'] = res.group(0)

        # Parse target bounding box
        res = re.search('[0-9]+x[0-9]+x[0-9]+', cmdline_str)
        assert res is not None, "Bad target bounding box specification in {0}".format(cmdline_str)
        ret['bb'] = tuple(int(x) for x in res.group(0).split('x'))

        # Parse target anchor
        res = re.search(r"@[0-9]+,[0-9]+", cmdline_str)
        assert res is not None, "Bad target anchor specification in {0}".format(cmdline_str)
        ret['anchor'] = tuple(int(x) for x in res.group(0)[1:].split(','))

        return ret


def factory(cmdopts: tp.Dict[str, str],
            cli_str: str,
            target_id: int):
    """
    Create XML definitions for a ramp for rectprism construction target.
    """
    target = ConstructTargetParser()(cli_str)

    if target['type'] == 'ramp':
        return RampConstructTarget(target,
                                   cmdopts['construct_orientation'],
                                   target_id)
    elif target['type'] == 'rectprism':
        return RectprismConstructTarget(target,
                                        cmdopts['construct_orientation'],
                                        target_id)
