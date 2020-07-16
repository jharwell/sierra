# Copyright 2018 John Harwell, All rights reserved.
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
Miscellaneous classes/functions used in mutiple places but that don't really fit anywhere.
"""

import pickle
import os
import logging
import numpy as np


class ArenaExtent():
    """Representation of a 2D or 3D section/chunk/volume of the arena."""

    def __init__(self,
                 dims: tuple,
                 offset: tuple = (0, 0, 0)) -> None:
        self.offset = offset
        self.dims = dims

        self.xmin = int(offset[0])
        self.ymin = int(offset[1])
        self.zmin = int(offset[2])

        self.xmax = offset[0] + int(dims[0])
        self.ymax = offset[1] + int(dims[1])
        self.zmax = offset[2] + int(dims[2])

    def x(self):
        return self.dims[0]

    def y(self):
        return self.dims[1]

    def z(self):
        return self.dims[2]

    def __str__(self) -> str:
        return str(self.dims) + '@' + str(self.offset)


class Sigmoid():
    """
    Sigmoid activation function.

    .. math::
       f(x) = \frac{1}{1+e^{-x}}

    """

    def __init__(self, x: float):
        self.x = x

    def __call__(self):
        if self.x < 0:
            # Equivalent, and numerically stable for large negative exponents. If you don't case the
            # sigmoid, you get overflow errors at runtime.
            return 1.0 - 1.0 / (1 + np.exp(self.x))
        else:
            return 1.0 / (1 + np.exp(-self.x))


class ReLu():
    """
    REctified Linear Unit activation function.

    .. math::
       \begin{equation}
           \begin{aligned}
               f(x) = max(0,x) &= x \textit{if} x > 0
                               &= 0 \textit{else}
           \end{aligned}
       \end{equation}
    """


def unpickle_exp_def(exp_def_fpath):
    """
    Read in all the different sets of parameter changes that were pickled to make
    crucial parts of the experiment definition easily accessible. I don't know how
    many there are, so go until you get an exception.
    """
    try:
        with open(exp_def_fpath, 'rb') as f:
            exp_def = set()
            while True:
                exp_def = exp_def | pickle.load(f)
    except EOFError:
        pass
    return exp_def


def dir_create_checked(path: str, exist_ok: bool):
    try:
        os.makedirs(path, exist_ok=exist_ok)
    except FileExistsError:
        logging.fatal("%s already exists! Not overwriting", path)
        raise


__api__ = [
    'ArenaExtent',
    'unpickle_exp_def'
]
