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
from sierra.core.vector import Vector3D


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

    def __init__(self, x: float) -> None:
        self.x = x

    def __call__(self) -> float:
        if self.x < 0:
            # Equivalent, and numerically stable for large negative exponents. If you don't case the
            # sigmoid, you get overflow errors at runtime.
            return 1.0 - 1.0 / (1 + np.exp(self.x))  # type: ignore
        else:
            return 1.0 / (1 + np.exp(-self.x))  # type: ignore


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


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)  # type:ignore
def pd_csv_read(path: str, **kwargs) -> pd.DataFrame:
    # Always specify the datatype so pandas does not have to infer it--much faster.
    return pd.read_csv(path, sep=';', float_precision='high', **kwargs)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)  # type:ignore
def pd_csv_write(df: pd.DataFrame, path: str, **kwargs) -> None:
    df.to_csv(path, sep=';', float_format='%.8f', **kwargs)


@retry(pd.errors.ParserError, tries=10, delay=0.100, backoff=1.1)  # type:ignore
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


def get_primary_axis(criteria, primary_axis_bc: tp.List, cmdopts: tp.Dict[str, tp.Any]) -> int:
    if cmdopts['plot_primary_axis'] == 0:
        return 0

    if cmdopts['plot_primary_axis'] == 1:
        return 1

    if any([isinstance(criteria.criteria1, elt) for elt in primary_axis_bc]):
        return 0

    return 1


def exp_range_calc(cmdopts: tp.Dict[str, tp.Any], root_dir: str, criteria) -> tp.List[str]:
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


def exp_include_filter(inc_spec: str, target: tp.List, n_exps: int):
    """
    Takes a input list, and returns the sublist specified by the inc_spec (of the form
    [x:y]). inc_spec is an `absolute` specification; if a given performance measure excludes exp0
    then that case is handled internally so that array/list shapes work out when generating graphs
    if this function is used consistently everywhere.
    """
    if inc_spec is None:
        start = None
        end = None
    else:
        r = inc_spec.split(':')
        start = int(r[0])
        if r[1] == '':
            end = len(target)
        else:
            end = int(r[1])

        if len(target) < n_exps:  # Handle perf measures which exclude exp0 by default
            start -= 1

    return target[slice(start, end, None)]


def bivar_exp_labels_calc(exp_dirs: tp.List[str]) -> tp.Tuple[tp.List[str], tp.List[str]]:
    # Because sets are used, if a sub-range of experiments are selected for collation, the
    # selected range has to be an even multiple of the # of experiments in the second batch
    # criteria, or inter-experiment graph generation won't work (the final .csv is always an MxN
    # grid).
    xlabels_set = set()
    ylabels_set = set()
    for e in exp_dirs:
        pair = os.path.split(e)[1].split('+')
        xlabels_set.add(pair[0])
        ylabels_set.add(pair[1])

    xlabels = sorted(list(xlabels_set))
    ylabels = sorted(list(ylabels_set))

    return (xlabels, ylabels)


__api__ = [
    'ArenaExtent',
]
