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
Camera timeline and interpolation for manipulating ARGoS rendering perspective.
"""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from core.variables.base_variable import IBaseVariable
from core.utils import ArenaExtent
import core.variables.time_setup as time_setup
from core.xml_luigi import XMLAttrChange, XMLAttrChangeSet, XMLTagRmList, XMLTagAddList, XMLTagRm, XMLTagAdd


@implements.implements(IBaseVariable)
class CameraTimeline():
    """
    Defines when/how to switch between different camera perspectives withoun ARGoS.

    Attributes:
        tsetup: Simulation time definitions.
        extents: List of (X,Y,Zs) tuple of dimensions of area to assign to engines of the specified
                 type.
    """

    # If this default changes in ARGoS, it will need to be updated here too.
    kARGOS_N_CAMERAS = 12

    def __init__(self, tsetup: time_setup.TimeSetup, extents: tp.List[ArenaExtent]) -> None:
        self.extents = extents
        self.tsetup = tsetup

        self.tag_adds = None

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
        adds = XMLTagAddList(XMLTagAdd('./visualization/qt-opengl', 'camera', {}),
                             XMLTagAdd("./visualization/qt-opengl/camera", "placements", {}))

        in_ticks = self.tsetup.sim_duration * time_setup.kTICKS_PER_SECOND
        adds.append(XMLTagAdd('.//qt-opengl/camera', 'timeline', {'loop': str(in_ticks)}))

        for c in range(0, self.kARGOS_N_CAMERAS):
            adds.append(XMLTagAdd('.//qt-opengl/camera/timeline',
                                  'keyframe',
                                  {
                                      'placement': str(c),
                                      'step': str(in_ticks / self.kARGOS_N_CAMERAS * c)
                                  }
                                  ))
            if c < self.kARGOS_N_CAMERAS - 1:
                adds.append(XMLTagAdd('.//qt-opengl/camera/timeline', 'interpolate', {}))
        return [adds]


def factory(cmdopts: dict, extents: tp.List[ArenaExtent]) -> CameraTimeline:
    """
    Create cameras for a list of arena extents.
    """
    return CameraTimeline(time_setup.factory(cmdopts["time_setup"]), extents)


__api__ = [
    'CameraTimeline',
]
