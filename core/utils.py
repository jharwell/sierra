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

# Core packages
import os
import logging
import typing as tp
import time

# 3rd party packages
import numpy as np
import pandas as pd
from retry import retry

# Project packages
from core.vector import Vector3D


class ArenaExtent():
    """Representation of a 2D or 3D section/chunk/volume of the arena."""
    @staticmethod
    def from_corners(ll: Vector3D, ur: Vector3D) -> 'ArenaExtent':
        return ArenaExtent(ur - ll, ll)

    def __init__(self, dims: Vector3D, origin: Vector3D = Vector3D()) -> None:
        self.origin = origin
        self.dims = dims
        self.ll = origin
        self.ur = origin + dims

        self.center = origin + dims / 2.0

    def contains(self, pt: Vector3D) -> bool:
        return pt >= self.ll and pt <= self.ur

    def area(self) -> float:
        return self.dims.x * self.dims.y

    def xsize(self):
        return self.dims.x

    def ysize(self):
        return self.dims.y

    def zsize(self):
        return self.dims.z

    def __str__(self) -> str:
        return str(self.dims) + '@' + str(self.origin)


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
    r"""
    REctified Linear Unit activation function.

    .. math::
       \begin{equation}
           \begin{aligned}
               f(x) = max(0,x) &= x \textit{if} x > 0
                               &= 0 \textit{else}
           \end{aligned}
       \end{equation}
    """

    def __init__(self, x: float):
        self.x = x

    def __call__(self):
        return max(0, self.x)


def extract_arena_dims(exp_def) -> ArenaExtent:
    for path, attr, value in exp_def:
        if path == ".//arena" and attr == "size":
            x, y, z = value.split(',')
            dims = Vector3D(float(x), float(y), float(z))
            return ArenaExtent(dims)

    return None  # type: ignore


def scale_minmax(minval: float, maxval: float, val: float) -> float:
    """
    Scale values from range [minval, maxval] -> [-1,1]

    .. math::
       -1 + (value - minval) * (1 - \frac{-1}{maxval - minval})
    """
    return -1.0 + (val - minval) * (1 - (-1)) / (maxval - minval)


def dir_create_checked(path: str, exist_ok: bool) -> None:
    try:
        os.makedirs(path, exist_ok=exist_ok)
    except FileExistsError:
        logging.fatal("%s already exists! Not overwriting", path)
        raise


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=0.100)  # type:ignore
def pd_csv_read(path: str, **kwargs) -> pd.DataFrame:
    # Always specify the datatype so pandas does not have to infer it--much faster.
    return pd.read_csv(path, sep=';', float_precision='high', **kwargs)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=0.100)  # type:ignore
def pd_pickle_read(path: str) -> pd.DataFrame:
    return pd.read_pickle(path)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=0.100)  # type:ignore
def pd_csv_write(df: pd.DataFrame, path: str, **kwargs) -> None:
    df.to_csv(path, sep=';', float_format='%.8f', **kwargs)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=0.100)  # type:ignore
def pd_pickle_write(df: pd.DataFrame, path: str) -> None:
    df.to_pickle(path)


def path_exists(path: str) -> bool:
    res = []
    for i in range(0, 10):
        if os.path.exists(path):
            res.append(True)
        else:
            res.append(False)
            time.sleep(0.001)

    return max(set(res), key=res.count)


def get_primary_axis(criteria, primary_axis_bc: tp.List, cmdopts: dict) -> int:
    if cmdopts['plot_primary_axis'] == '0':
        return 0
    if cmdopts['plot_primary_axis'] == '1':
        return 1

    if any([isinstance(criteria.criteria1, elt) for elt in primary_axis_bc]):
        return 0

    return 1


def exp_range_calc(cmdopts: dict, root_dir: str, criteria) -> tp.List[str]:
    exp_all = [os.path.join(root_dir, d)
               for d in criteria.gen_exp_dirnames(cmdopts)]

    exp_range = cmdopts['exp_range']
    if cmdopts['exp_range'] is not None:
        min_exp = int(exp_range.split(':')[0])
        max_exp = int(exp_range.split(':')[1])
        assert min_exp <= max_exp, "FATAL: Min batch exp >= max batch exp({0} vs. {1})".format(
            min_exp, max_exp)

        return exp_all[min_exp: max_exp + 1]

    return exp_all


def module_exists(name: str):
    try:
        mod = __import__(name)
    except ImportError:
        return False
    else:
        return True


__api__ = [
    'ArenaExtent',
]
