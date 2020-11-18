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

# Core packages
import math

# 3rd party packages

# Project packages


class Vector:
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __len__(self):
        return int(self.length())

    def __add__(self, o):
        return Vector3D((self.x + o.x), (self.y + o.y), (self.z + o.z))

    def __sub__(self, o):
        return Vector3D((self.x - o.x), (self.y - o.y), (self.z - o.z))

    def __mul__(self, o):
        return Vector3D((self.x * o.x) + (self.y * o.y) + (self.z * o.z))

    def __truediv__(self, o):
        if isinstance(o, float) or isinstance(o, int):
            return Vector3D((self.x / o), (self.y / o), (self.z / o))
        else:
            raise NotImplementedError

    def __iadd__(self, o):
        self.x += o.x
        self.y += o.y
        self.z += o.z
        return self

    def __isub__(self, o):
        self.x -= o.x
        self.y -= o.y
        self.z -= o.z
        return self

    def __ge__(self, other):
        return self.x >= other.x and self.y >= other.y and self.z >= other.z

    def __le__(self, other):
        return self.x <= other.x and self.y <= other.y and self.z <= other.z

    def __neg__(self):
        return Vector3D(-self.x, -self.y, -self.z)

    def __str__(self):
        return '({0},{1},{2})'.format(self.x, self.y, self.z)

    def length(self):
        return math.sqrt((self.x * self.x) + (self.y * self.y) + (self.z * self.z))

    def normalize(self):
        length = self.length()
        return Vector3D((self.x / length), (self.y / length), (self.z / length))


class Vector2D(Vector):
    def __init__(self, x: float = 0, y: float = 0):
        super().__init__(x, y)


class Vector3D(Vector):
    pass
