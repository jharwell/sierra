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
import math

# 3rd party packages

# Project packages
from sierra.core.vector import Vector3D


def test_init() -> None:
    v1 = Vector3D(1, 2, 3)

    assert v1.x == 1
    assert v1.y == 2
    assert v1.z == 3

    v2 = Vector3D.from_str("1,2,3")

    assert v2 == v1
    assert v1 == v2


def test_ops() -> None:
    v1 = Vector3D(0, 1, 2)
    v2 = Vector3D(2, 0, 1)
    v3 = v1

    # +/-
    assert v1 + v2 == Vector3D(2, 1, 3)
    assert v2 + v1 == Vector3D(2, 1, 3)
    assert v1 - v2 == Vector3D(-2, 1, 1)
    assert v2 - v1 == Vector3D(2, -1, -1)
    v3 += v2
    assert v3 == Vector3D(2, 1, 3)
    v3 -= v2
    assert v3 == v1
    assert -v1 == Vector3D(0, -1, -2)

    # Multiplication
    assert v1 * 0 == Vector3D(0, 0, 0)
    assert v1 * 1 == v1
    assert v1 * 2 == Vector3D(0, 2, 4)

    # Division
    assert v1 / 0.5 == Vector3D(0, 2, 4)

    # Comparisons
    v4 = Vector3D(2, 3, 4)
    assert v4 > v1
    assert v4 >= v1
    assert v1 < v4
    assert not v4 <= v1


def test_funcs() -> None:
    v1 = Vector3D(0, 1, 2)
    v2 = Vector3D(2, 0, 1)

    # length
    assert v1.length() == math.sqrt(5)
    assert v2.length() == math.sqrt(5)

    # dot product
    assert v1.dot(v2) == 2
    assert v2.dot(v1) == 2

    # cross product
    assert v1.cross(v2) == Vector3D(1, 4, -2)
    assert v2.cross(v1) == Vector3D(-1, -4, 2)

    # normalize
    assert math.isclose(v1.normalize().length(), 1)

    # perpendicularize
    v3 = Vector3D(0, 1, 0)
    v4 = v3.perpendicularize()

    assert v3.dot(v4) == 0
    assert v4.dot(v3) == 0
