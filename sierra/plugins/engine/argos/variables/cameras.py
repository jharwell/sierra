# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

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
from sierra.core.experiment import definition
from sierra.core import types
from sierra.core.vector import Vector3D
import sierra.plugins.engine.argos.variables.exp_setup as exp


@implements.implements(IBaseVariable)
class QTCameraTimeline:
    """Defines when/how to switch between camera perspectives within ARGoS.

    Attributes:
        interpolate: Should we interpolate between camera positions on our
                      timeline ?

        setup: Simulation experiment definitions.

        extents: List of (X,Y,Zs) tuple of dimensions of arena areas to generate
                 camera definitions for.

    """

    # If this default changes in ARGoS, it will need to be updated here too.
    N_CAMERAS = 12

    def __init__(
        self, setup: exp.ExpSetup, cmdline: str, extents: list[ArenaExtent]
    ) -> None:
        self.cmdline = cmdline
        self.extents = extents
        self.setup = setup
        self.element_adds = []  # type: tp.List[definition.ElementAddList]

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        """
        No effect.

        All tags/attributes are either deleted or added.
        """
        return []

    def gen_tag_rmlist(self) -> list[definition.ElementRmList]:
        """Remove the ``<camera>`` tag if it exists.

        Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [
            definition.ElementRmList(
                definition.ElementRm("./visualization/qt-opengl", "camera")
            )
        ]

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        if not self.element_adds:
            adds = definition.ElementAddList(
                definition.ElementAdd("./visualization/qt-opengl", "camera", {}, False),
                definition.ElementAdd(
                    "./visualization/qt-opengl/camera", "placements", {}, False
                ),
            )

            in_ticks = self.setup.n_secs_per_run * self.setup.n_ticks_per_sec
            adds.append(
                definition.ElementAdd(
                    ".//qt-opengl/camera", "timeline", {"loop": str(in_ticks)}, False
                )
            )

            for ext in self.extents:
                # generate keyframes for switching between camera perspectives
                self._gen_keyframes(adds, self.N_CAMERAS, in_ticks)

                info = [
                    self._gen_camera_config(ext, c, self.N_CAMERAS)
                    for c in range(0, self.N_CAMERAS)
                ]

                for index, up, look_at, pos in info:
                    camera = definition.ElementAdd(
                        ".//camera/placements",
                        "placement",
                        {
                            "index": f"{index}",
                            "up": f"{up.x},{up.y},{up.z}",
                            "position": f"{pos.x},{pos.y},{pos.z}",
                            "look_at": f"{look_at.x},{look_at.y},{look_at.z}",
                        },
                        True,
                    )
                    adds.append(camera)

            self.element_adds = [adds]

        return self.element_adds

    def gen_files(self) -> None:
        pass

    def _gen_keyframes(
        self, adds: definition.ElementAddList, n_cameras: int, cycle_length: int
    ) -> None:
        for c in range(0, n_cameras):
            index = c % n_cameras
            adds.append(
                definition.ElementAdd(
                    ".//qt-opengl/camera/timeline",
                    "keyframe",
                    {
                        "placement": str(index),
                        "step": str(int(cycle_length / n_cameras * c)),
                    },
                    True,
                )
            )
            if "interp" in self.cmdline and c < n_cameras:
                adds.append(
                    definition.ElementAdd(
                        ".//qt-opengl/camera/timeline", "interpolate", {}, True
                    )
                )

    def _gen_camera_config(self, ext: ArenaExtent, index: int, n_cameras) -> tuple:
        angle = (index % n_cameras) * (2.0 * math.pi / n_cameras)
        look_at = Vector3D(ext.xsize() / 2.0, ext.ysize() / 2.0, 0.0)
        hyp = math.sqrt(2 * max(look_at.x, look_at.y) ** 2)

        pos_x = hyp * math.cos(angle) + look_at.x
        pos_y = hyp * math.sin(angle) + look_at.y
        pos_z = max(ext.xsize(), ext.ysize()) * 0.50
        pos = Vector3D(pos_x, pos_y, pos_z)

        # This is what the ARGoS source does for the up vector for the default
        # camera configuration
        up = Vector3D(0, 0, 1)

        return index, up, look_at, pos


@implements.implements(IBaseVariable)
class QTCameraOverhead:
    """Defines a single overhead camera perspective within ARGoS.

    Attributes:
        extents: List of (X,Y,Z) tuple of dimensions of arena areas to generate
                 camera definitions for.

    """

    def __init__(self, extents: list[ArenaExtent]) -> None:
        self.extents = extents
        self.element_adds = []  # type: tp.List[definition.ElementAddList]

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        """No effect.

        All tags/attributes are either deleted or added.

        """
        return []

    def gen_tag_rmlist(self) -> list[definition.ElementRmList]:
        """Remove the ``<camera>`` tag if it exists.

        Obviously you *must* call this function BEFORE adding new definitions.

        """
        return [
            definition.ElementRmList(
                definition.ElementRm("./visualization/qt-opengl", "camera")
            )
        ]

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        if not self.element_adds:
            adds = definition.ElementAddList(
                definition.ElementAdd("./visualization/qt-opengl", "camera", {}, False),
                definition.ElementAdd(
                    "./visualization/qt-opengl/camera", "placements", {}, False
                ),
            )

            for ext in self.extents:
                height = max(ext.xsize(), ext.ysize()) * 0.75
                camera = definition.ElementAdd(
                    ".//camera/placements",
                    "placement",
                    {
                        "index": "0",
                        "position": "{}, {}, {}".format(
                            ext.xsize() / 2.0, ext.ysize() / 2.0, height
                        ),
                        "look_at": "{}, {}, 0".format(
                            ext.xsize() / 2.0, ext.ysize() / 2.0
                        ),
                    },
                    True,
                )
                adds.append(camera)
            self.element_adds = [adds]

        return self.element_adds

    def gen_files(self) -> None:
        pass


def factory(cmdopts: types.Cmdopts, extents: list[ArenaExtent]):
    """Create cameras for a list of arena extents."""
    if cmdopts["camera_config"] == "overhead":
        return QTCameraOverhead(extents)

    return QTCameraTimeline(
        exp.factory(cmdopts["exp_setup"]), cmdopts["camera_config"], extents
    )


__all__ = [
    "QTCameraOverhead",
    "QTCameraTimeline",
]
