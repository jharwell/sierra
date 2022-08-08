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

"""Classes for specifying ARGoS cameras.

Positions, timeline, and interpolation, for manipulating the frame
capture/rendering perspective.

"""

# Core packages
import typing as tp
import math

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.utils import ArenaExtent
from sierra.core.experiment import xml
from sierra.core import types, config
from sierra.core.vector import Vector3D
import sierra.plugins.platform.argos.variables.exp_setup as exp


@implements.implements(IBaseVariable)
class QTCameraTimeline():
    """Defines when/how to switch between camera perspectives within ARGoS.

    Attributes:

        interpolate: Should we interpolate between camera positions on our
                      timeline ?

        setup: Simulation experiment definitions.

        extents: List of (X,Y,Zs) tuple of dimensions of arena areas to generate
                 camera definitions for.

    """

    # If this default changes in ARGoS, it will need to be updated here too.
    kARGOS_N_CAMERAS = 12

    def __init__(self,
                 setup: exp.ExpSetup,
                 cmdline: str,
                 extents: tp.List[ArenaExtent]) -> None:
        self.interpolate = cmdline in ['argos.sw+interp',
                                       'sierra.sw+interp',
                                       'sierra.sw+interp+zoom']

        self.cmdline = cmdline
        self.extents = extents
        self.setup = setup
        self.tag_adds = []  # type: tp.List[xml.TagAddList]

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        """
        No effect.

        All tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self) -> tp.List[xml.TagRmList]:
        """Remove the ``<camera>`` tag if it exists.

        Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [xml.TagRmList(xml.TagRm("./visualization/qt-opengl", "camera"))]

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        if not self.tag_adds:
            adds = xml.TagAddList(xml.TagAdd('./visualization/qt-opengl',
                                             'camera',
                                             {},
                                             False),
                                  xml.TagAdd("./visualization/qt-opengl/camera",
                                             "placements",
                                             {},
                                             False))

            in_ticks = self.setup.n_secs_per_run * \
                int(config.kARGoS['n_ticks_per_sec'])
            adds.append(xml.TagAdd('.//qt-opengl/camera',
                                   'timeline',
                                   {
                                       'loop': str(in_ticks)
                                   },
                                   False))

            if self.cmdline in ['sierra.sw', 'sierra.sw+interp']:
                n_cameras = self.kARGOS_N_CAMERAS
            elif self.cmdline == 'sierra.sw+interp+zoom':
                n_cameras = self.kARGOS_N_CAMERAS * 3

            for ext in self.extents:
                # generate keyframes for switching between camera perspectives
                self._gen_keyframes(adds, n_cameras, in_ticks)

                info = []
                for c in range(0, n_cameras):
                    info.append(self._gen_camera_config(ext,
                                                        c,
                                                        n_cameras))

                for index, up, look_at, pos in info:
                    camera = xml.TagAdd('.//camera/placements',
                                        'placement',
                                        {
                                            'index': f"{index}",
                                            'up': f"{up.x},{up.y},{up.z}",
                                            'position': f"{pos.x},{pos.y},{pos.z}",
                                            'look_at': f"{look_at.x},{look_at.y},{look_at.z}",
                                        },
                                        True)
                    adds.append(camera)

            self.tag_adds = [adds]

        return self.tag_adds

    def gen_files(self) -> None:
        pass

    def _gen_keyframes(self,
                       adds: xml.TagAddList,
                       n_cameras: int,
                       cycle_length: int) -> None:
        for c in range(0, n_cameras):
            index = c % n_cameras
            adds.append(xml.TagAdd('.//qt-opengl/camera/timeline',
                                   'keyframe',
                                   {
                                       'placement': str(index),
                                       'step': str(int(cycle_length / n_cameras * c))
                                   },
                                   True
                                   ))
            if self.interpolate and c < n_cameras:
                adds.append(xml.TagAdd('.//qt-opengl/camera/timeline',
                                       'interpolate',
                                       {},
                                       True))

    def _gen_camera_config(self,
                           ext: ArenaExtent,
                           index: int,
                           n_cameras) -> tuple:
        angle = (index % n_cameras) * (2.0 * math.pi / n_cameras)
        look_at = Vector3D(ext.xsize() / 2.0,
                           ext.ysize() / 2.0,
                           0.0)
        hyp = math.sqrt(2 * max(look_at.x, look_at.y) ** 2)

        # As time proceeds and we interpolate between cameras, we want to slowly
        # be zooming in/moving the cameras closer to the arena center.
        if self.cmdline == 'sierra.sw+interp+zoom':
            factor = math.sqrt((n_cameras + index) / n_cameras)
        else:
            factor = 1.0

        pos_x = (hyp * math.cos(angle) + look_at.x) / factor
        pos_y = (hyp * math.sin(angle) + look_at.y) / factor
        pos_z = (max(ext.xsize(), ext.ysize()) * 0.50) / factor
        pos = Vector3D(pos_x, pos_y, pos_z)

        # This is what the ARGoS source does for the up vector for the default
        # camera configuration
        up = Vector3D(0, 0, 1)

        return index, up, look_at, pos


@implements.implements(IBaseVariable)
class QTCameraOverhead():
    """Defines a single overhead camera perspective within ARGoS.

    Attributes:

        extents: List of (X,Y,Zs) tuple of dimensions of arena areas to generate
                 camera definitions for.

    """

    def __init__(self,
                 extents: tp.List[ArenaExtent]) -> None:
        self.extents = extents
        self.tag_adds = []  # type: tp.List[xml.TagAddList]

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        """No effect.

        All tags/attributes are either deleted or added.

        """
        return []

    def gen_tag_rmlist(self) -> tp.List[xml.TagRmList]:
        """Remove the ``<camera>`` tag if it exists.

        Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [xml.TagRmList(xml.TagRm("./visualization/qt-opengl", "camera"))]

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        if not self.tag_adds:
            adds = xml.TagAddList(xml.TagAdd('./visualization/qt-opengl',
                                             'camera',
                                             {},
                                             False),
                                  xml.TagAdd("./visualization/qt-opengl/camera",
                                             "placements",
                                             {},
                                             False))

            for ext in self.extents:
                height = max(ext.xsize(), ext.ysize()) * 0.75
                camera = xml.TagAdd('.//camera/placements',
                                    'placement',
                                    {
                                        'index': '0',
                                        'position': "{0}, {1}, {2}".format(ext.xsize() / 2.0,
                                                                           ext.ysize() / 2.0,
                                                                           height),
                                        'look_at': "{0}, {1}, 0".format(ext.xsize() / 2.0,
                                                                        ext.ysize() / 2.0),
                                    },
                                    True)
                adds.append(camera)
            self.tag_adds = [adds]

        return self.tag_adds

    def gen_files(self) -> None:
        pass


def factory(cmdopts: types.Cmdopts, extents: tp.List[ArenaExtent]):
    """Create cameras for a list of arena extents.

    """
    if cmdopts['camera_config'] == 'overhead':
        return QTCameraOverhead(extents)
    else:
        return QTCameraTimeline(exp.factory(cmdopts["exp_setup"])(),  # type: ignore
                                cmdopts['camera_config'],
                                extents)


__api__ = [
    'QTCameraTimeline', 'QTCameraOverhead',


]
