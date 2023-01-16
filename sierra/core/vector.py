# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Representation of vectors in 3D space and operations on them..
"""
# Core packages
import math
import typing as tp

# 3rd party packages

# Project packages


class Vector3D:
    """Represents a point in 3D space and/or a directional vector in 3D space.

    """

    @staticmethod
    def from_str(s: str, astype=int) -> 'Vector3D':
        return Vector3D(*tuple(map(astype, s.split(','))))

    @staticmethod
    def d2norm(lhs: 'Vector3D', rhs: 'Vector3D') -> float:
        return math.sqrt((lhs.x - rhs.x) ** 2 + (lhs.y - rhs.y) ** 2)

    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector3D):
            raise NotImplementedError

        return self.x == other.x and self.y == other.y and self.z == other.z

    def __hash__(self) -> int:
        return hash((self.x, self.y, self.z))

    def __len__(self) -> int:
        return int(self.length())

    def __add__(self, o: 'Vector3D') -> 'Vector3D':
        return Vector3D((self.x + o.x), (self.y + o.y), (self.z + o.z))

    def __sub__(self, o: 'Vector3D') -> 'Vector3D':
        return Vector3D((self.x - o.x), (self.y - o.y), (self.z - o.z))

    def __mul__(self, o: tp.Union[float, int]) -> 'Vector3D':
        return Vector3D(self.x * o, self.y * o, self.z * o)

    def __truediv__(self, o: tp.Union[float, int]) -> 'Vector3D':
        if isinstance(o, (float, int)):
            return Vector3D((self.x / o), (self.y / o), (self.z / o))
        else:
            raise NotImplementedError

    def __iadd__(self, o: 'Vector3D') -> 'Vector3D':
        self.x += o.x
        self.y += o.y
        self.z += o.z
        return self

    def __isub__(self, o: 'Vector3D') -> 'Vector3D':
        self.x -= o.x
        self.y -= o.y
        self.z -= o.z
        return self

    def __ge__(self, other: 'Vector3D') -> bool:
        return self.x >= other.x and self.y >= other.y and self.z >= other.z

    def __le__(self, other: 'Vector3D') -> bool:
        return self.x <= other.x and self.y <= other.y and self.z <= other.z

    def __lt__(self, other: 'Vector3D') -> bool:
        """
        Determine if one vector is less than another by coordinate comparison.
        """
        return ((self.x < other.x) or
                ((self.x == other.x) and (self.y < other.y)) or
                ((self.x == other.x) and (self.y == other.y) and (self.z < other.z)))

    def __neg__(self) -> 'Vector3D':
        return Vector3D(-self.x, -self.y, -self.z)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f'({self.x},{self.y},{self.z})'

    def length(self) -> float:
        return math.sqrt((self.x * self.x) + (self.y * self.y) + (self.z * self.z))

    def cross(self, rhs: 'Vector3D') -> 'Vector3D':
        return Vector3D(self.y * rhs.z - self.z * rhs.y,
                        self.z * rhs.x - self.x * rhs.z,
                        self.x * rhs.y - self.y * rhs.x)

    def dot(self, rhs: 'Vector3D') -> 'Vector3D':
        return self.x * rhs.x + self.y * rhs.y + self.z * rhs.z

    def normalize(self) -> 'Vector3D':
        length = self.length()
        self.x /= length
        self.y /= length
        self.z /= length

        return self

    def perpendicularize(self: 'Vector3D') -> 'Vector3D':
        # From
        # https://math.stackexchange.com/questions/137362/how-to-find-perpendicular-vector-to-another-vector
        choice1 = Vector3D(0, self.z, -self.y)
        choice2 = Vector3D(-self.z, 0, self.x)
        choice3 = Vector3D(-self.y, self.x, 0)
        m = max([choice1, choice2, choice3], key=lambda v: v.length())
        return m


__api__ = ['Vector3D']
