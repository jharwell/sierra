# Copyright 2022 John Harwell, All rights reserved.
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
