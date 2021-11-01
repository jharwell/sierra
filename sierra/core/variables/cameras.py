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
Classes for specifying ARGoS camera positions, timeline, and interpolation, for manipulation the
frame capture/rendering perspective.
"""

# Core packages
import typing as tp
import math

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.utils import ArenaExtent
import sierra.core.variables.time_setup as ts
from sierra.core.xml import XMLAttrChangeSet, XMLTagRmList, XMLTagAddList, XMLTagRm, XMLTagAdd
import sierra.core.config
from sierra.core import types


@implements.implements(IBaseVariable)
class ARGoSQTCameraTimeline():
    """
    Defines when/how to switch between different camera perspectives within ARGoS.

    Attributes:
        interpolate: Should we interpolate between camera positions on our timeline ?
        tsetup: Simulation time definitions.
        extents: List of (X,Y,Zs) tuple of dimensions of arena areas to generate camera definitions
                 for.
    """

    # If this default changes in ARGoS, it will need to be updated here too.
    kARGOS_N_CAMERAS = 12

    def __init__(self,
                 tsetup: ts.ARGoSTimeSetup,
                 cameras: str,
                 extents: tp.List[ArenaExtent]) -> None:
        self.interpolate = 'dynamic' in cameras

        if 'argos' in cameras:
            self.paradigm = 'argos'
        else:
            self.paradigm = 'sierra'

        self.extents = extents
        self.tsetup = tsetup
        self.tag_adds = []  # type: tp.List[XMLTagAddList]

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """
        Does nothing because all tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self) -> tp.List[XMLTagRmList]:
        """
        Removing the ``<camera>`` tag if it exists may be desirable so an option is provided to do
        so. Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [XMLTagRmList(XMLTagRm("./visualization/qt-opengl", "camera"))]

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        if not self.tag_adds:
            adds = XMLTagAddList(XMLTagAdd('./visualization/qt-opengl', 'camera', {}),
                                 XMLTagAdd("./visualization/qt-opengl/camera", "placements", {}))

            in_ticks = self.tsetup.duration * \
                sierra.core.config.kARGoS['ticks_per_second']
            adds.append(XMLTagAdd('.//qt-opengl/camera',
                                  'timeline', {'loop': str(in_ticks)}))

            for ext in self.extents:
                for c in range(0, self.kARGOS_N_CAMERAS + 1):
                    index = c % self.kARGOS_N_CAMERAS
                    adds.append(XMLTagAdd('.//qt-opengl/camera/timeline',
                                          'keyframe',
                                          {
                                              'placement': str(index),
                                              'step': str(int(in_ticks / self.kARGOS_N_CAMERAS * c))
                                          }
                                          ))
                    if self.interpolate and c < self.kARGOS_N_CAMERAS:
                        adds.append(
                            XMLTagAdd('.//qt-opengl/camera/timeline', 'interpolate', {}))

            if self.paradigm == 'sierra':
                for ext in self.extents:
                    center_x = ext.xsize() / 2.0
                    center_y = ext.ysize() / 2.0

                    pos_z = max(ext.xsize(), ext.ysize()) * 0.50
                    hyp = math.sqrt(2 * max(center_x, center_y) ** 2)
                    cameras = XMLTagAddList()
                    for c in range(0, self.kARGOS_N_CAMERAS):
                        angle = c * math.pi / 6.0
                        pos_x = hyp * math.cos(angle) + center_x
                        pos_y = hyp * math.sin(angle) + center_y
                        cameras.append(XMLTagAdd('.//camera/placements',
                                                 'placement',
                                                 {
                                                     'index': "{0}".format(c),
                                                              'position': "{0}, {1}, {2}".format(pos_x,
                                                                                                 pos_y,
                                                                                                 pos_z),
                                                              'look_at': "{0}, {1},0".format(center_x,
                                                                                             center_y)
                                                 })
                                       )
                adds.extend(cameras)

            self.tag_adds = [adds]

        return self.tag_adds

    def gen_files(self) -> None:
        pass


@implements.implements(IBaseVariable)
class ARGoSQTCameraOverhead():
    """
    Defines a single overhead camera perspective within ARGoS.

    Attributes:
        extents: List of (X,Y,Zs) tuple of dimensions of arena areas to generate camera definitions
                 for.
    """

    def __init__(self,
                 extents: tp.List[ArenaExtent]) -> None:
        self.extents = extents
        self.tag_adds = []  # type: tp.List[XMLTagAddList]

    def gen_attr_changelist(self) -> tp.List[XMLAttrChangeSet]:
        """
        Does nothing because all tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self) -> tp.List[XMLTagRmList]:
        """
        Removing the ``<camera>`` tag if it exists may be desirable so an option is provided to do
        so. Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [XMLTagRmList(XMLTagRm("./visualization/qt-opengl", "camera"))]

    def gen_tag_addlist(self) -> tp.List[XMLTagAddList]:
        if not self.tag_adds:
            adds = XMLTagAddList(XMLTagAdd('./visualization/qt-opengl', 'camera', {}),
                                 XMLTagAdd("./visualization/qt-opengl/camera", "placements", {}))

            for ext in self.extents:
                height = max(ext.xsize(), ext.ysize()) * 0.75
                adds.append(XMLTagAdd('.//camera/placements',
                                      'placement',
                                      {
                                          'index': '0',
                                                   'position': "{0}, {1}, {2}".format(ext.xsize() / 2.0,
                                                                                      ext.ysize() / 2.0,
                                                                                      height),
                                                   'look_at': "{0}, {1}, 0".format(ext.xsize() / 2.0,
                                                                                   ext.ysize() / 2.0),
                                      }))
            self.tag_adds = [adds]

        return self.tag_adds

    def gen_files(self) -> None:
        pass


def factory(cmdopts: types.Cmdopts, extents: tp.List[ArenaExtent]):
    """
    Create cameras for a list of arena extents.
    """
    if cmdopts['camera_config'] == 'overhead':
        return ARGoSQTCameraOverhead(extents)
    else:
        return ARGoSQTCameraTimeline(ts.factory(cmdopts["time_setup"])(),  # type: ignore
                                     cmdopts['camera_config'],
                                     extents)


__api__ = [
    'ARGoSQTCameraTimeline', 'ARGoSQTCameraOverhead',


]
