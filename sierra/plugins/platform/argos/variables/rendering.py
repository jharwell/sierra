# Copyright 2021 John Harwell, All rights reserved.
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
# You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""
ARGoS headless QT rendering configuration.
"""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.experiment import xml
import sierra.core.config
from sierra.core import types

import sierra.plugins.platform.argos.variables.exp_setup as exp


@implements.implements(IBaseVariable)
class ARGoSQTHeadlessRendering():
    """
    Sets up ARGoS headless rendering with QT.

    Attributes:

        tsetup: Simulation time definitions.

        extents: List of (X,Y,Zs) tuple of dimensions of area to assign to
                 engines of the specified type.
    """

    kFrameSize = "1600x1200"
    kQUALITY = 100
    kFRAME_RATE = 10

    def __init__(self, setup: exp.ExpSetup) -> None:
        self.setup = setup
        self.tag_adds = []  # type: tp.List[xml.TagAddList]

    def gen_attr_changelist(self) -> tp.List[xml.AttrChangeSet]:
        """
        No effect.

        All tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self) -> tp.List[xml.TagRmList]:
        """Remove the ``<qt_opengl>`` tag if it exists.

        Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [xml.TagRmList(xml.TagRm("./visualization", "qt-opengl"))]

    def gen_tag_addlist(self) -> tp.List[xml.TagAddList]:
        if not self.tag_adds:
            self.tag_adds = [xml.TagAddList(xml.TagAdd('.',
                                                       'visualization',
                                                       {},
                                                       False),
                                            xml.TagAdd('./visualization',
                                                       'qt-opengl',
                                                       {'autoplay': "true"},
                                                       False
                                                       ),
                                            xml.TagAdd('./visualization/qt-opengl',
                                                       'frame_grabbing',
                                                       {
                                                           'directory': 'frames',
                                                           'base_name': 'frame_',
                                                           'format': sierra.core.config.kImageExt[1:],
                                                           'headless_grabbing': "true",
                                                           'headless_frame_size': "{0}".format(self.kFrameSize),
                                                           'headless_frame_rate': "{0}".format(self.kFRAME_RATE),
                                                       },
                                                       False),
                                            xml.TagAdd('visualization/qt-opengl',
                                                       'user_functions',
                                                       {'label': '__EMPTY__'},
                                                       False))]

        return self.tag_adds

    def gen_files(self) -> None:
        pass


def factory(cmdopts: types.Cmdopts) -> ARGoSQTHeadlessRendering:
    """Set up QT headless rendering for the specified experimental setup.

    """

    return ARGoSQTHeadlessRendering(exp.factory(cmdopts["exp_setup"]))


__api__ = [
    'ARGoSQTHeadlessRendering',
]
