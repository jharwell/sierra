# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""
ARGoS headless QT rendering configuration.
"""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.experiment import definition
import sierra.core.config
from sierra.core import types

import sierra.plugins.engine.argos.variables.exp_setup as exp


@implements.implements(IBaseVariable)
class ARGoSQTHeadlessRendering:
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
        self.element_adds = []  # type: tp.List[definition.ElementAddList]

    def gen_attr_changelist(self) -> tp.List[definition.AttrChangeSet]:
        """
        No effect.

        All tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self) -> tp.List[definition.ElementRmList]:
        """Remove the ``<qt_opengl>`` tag if it exists.

        Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [
            definition.ElementRmList(
                definition.ElementRm("./visualization", "qt-opengl")
            )
        ]

    def gen_element_addlist(self) -> tp.List[definition.ElementAddList]:
        if not self.element_adds:
            self.element_adds = [
                definition.ElementAddList(
                    definition.ElementAdd(".", "visualization", {}, False),
                    definition.ElementAdd(
                        "./visualization", "qt-opengl", {"autoplay": "true"}, False
                    ),
                    definition.ElementAdd(
                        "./visualization/qt-opengl",
                        "frame_grabbing",
                        {
                            "directory": "frames",
                            "base_name": "frame_",
                            "format": sierra.core.config.kImageType,
                            "headless_grabbing": "true",
                            "headless_frame_size": "{0}".format(self.kFrameSize),
                            "headless_frame_rate": "{0}".format(self.kFRAME_RATE),
                        },
                        False,
                    ),
                    definition.ElementAdd(
                        "visualization/qt-opengl",
                        "user_functions",
                        {"label": "__EMPTY__"},
                        False,
                    ),
                )
            ]

        return self.element_adds

    def gen_files(self) -> None:
        pass


def factory(cmdopts: types.Cmdopts) -> ARGoSQTHeadlessRendering:
    """Set up QT headless rendering for the specified experimental setup."""

    return ARGoSQTHeadlessRendering(exp.factory(cmdopts["exp_setup"]))


__all__ = [
    "ARGoSQTHeadlessRendering",
]
