# Copyright 2022 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

# Core packages

# 3rd party packages

# Project packages
from sierra.core.utils import ArenaExtent
from sierra.core.vector import Vector3D


def test_funcs() -> None:
    origin = Vector3D(0, 0, 0)
    dims = Vector3D(3, 3, 3)
    e1 = ArenaExtent.from_corners(origin, dims)

    e2 = ArenaExtent(dims)

    assert e1.xsize() == e2.xsize()
    assert e1.ysize() == e2.ysize()
    assert e1.zsize() == e2.zsize()

    assert e1.origin() == e2.origin()

    assert e1.contains(origin)
    assert e1.contains(origin + dims)
    assert not e2.contains(origin + dims * 2)
    assert not e2.contains(origin - dims * 2)
