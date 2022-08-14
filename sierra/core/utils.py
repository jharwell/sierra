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

"""Miscellaneous bits used in mutiple places but that don't fit anywhere else.

"""

# Core packages
import typing as tp
import time
import logging
import pickle
import functools
import pathlib

# 3rd party packages
import numpy as np
import pandas as pd
from retry import retry

# Project packages
from sierra.core.vector import Vector3D
from sierra.core.experiment import xml, definition
from sierra.core import types, config
from sierra.core import plugin_manager as pm


class ArenaExtent():
    """Representation of a 2D or 3D section/chunk/volume of the arena."""
    @staticmethod
    def from_corners(ll: Vector3D, ur: Vector3D) -> 'ArenaExtent':
        """Initialize an extent via LL and UR corners.

        As opposed to an origin and a set of dimensions.

        """
        return ArenaExtent(ur - ll, ll)

    def __init__(self, dims: Vector3D, origin: Vector3D = Vector3D()) -> None:
        self._origin = origin
        self.dims = dims
        self.ll = origin
        self.ur = origin + dims

        self.center = origin + dims / 2.0

    def contains(self, pt: Vector3D) -> bool:
        return pt >= self.ll and pt <= self.ur

    def area(self) -> float:
        return self.dims.x * self.dims.y

    def xsize(self) -> int:
        return self.dims.x

    def ysize(self) -> int:
        return self.dims.y

    def zsize(self) -> int:
        return self.dims.z

    def origin(self) -> Vector3D:
        return self._origin

    def __str__(self) -> str:
        return str(self.dims) + '@' + str(self._origin)


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
            # Equivalent, and numerically stable for large negative
            # exponents. If you don't case the sigmoid, you get overflow errors
            # at runtime.
            return 1.0 - 1.0 / (1 + np.exp(self.x))  # type: ignore
        else:
            return 1.0 / (1 + np.exp(-self.x))  # type: ignore


class ReLu():
    r"""
    Rectified Linear Unit (ReLU) activation function.

    .. math::

       \begin{aligned}
            f(x) = max(0,x) &= x \textit{if} x > 0
                            &= 0 \textit{else}
       \end{aligned}
    """

    def __init__(self, x: float):
        self.x = x

    def __call__(self):
        return max(0, self.x)


def scale_minmax(minval: float, maxval: float, val: float) -> float:
    """
    Scale values from range [minval, maxval] -> [-1,1].

    .. math::
       -1 + (value - minval) * (1 - \frac{-1}{maxval - minval})
    """
    return -1.0 + (val - minval) * (1 - (-1)) / (maxval - minval)


def dir_create_checked(path: tp.Union[pathlib.Path, str],
                       exist_ok: bool) -> None:
    """Create a directory idempotently.

    If the directory exists and it shouldn't, raise an error.

    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    try:
        path.mkdir(exist_ok=exist_ok, parents=True)
    except FileExistsError:
        logging.fatal("%s already exists! Not overwriting", str(path))
        raise


def path_exists(path: tp.Union[pathlib.Path, str]) -> bool:
    """
    Check if a path exists, trying multiple times.

    This is necessary for working on HPC systems where if a given
    directory/filesystem is under heavy pressure the first check or two might
    time out as the FS goes and executes the query over the network.
    """
    res = []

    if not isinstance(path, pathlib.Path):
        path = pathlib.Path(path)

    for _ in range(0, 10):
        if path.exists():
            res.append(True)
        else:
            res.append(False)
            time.sleep(0.001)

    return max(set(res), key=res.count)


def get_primary_axis(criteria,
                     primary_axis_bc: tp.List,
                     cmdopts: types.Cmdopts) -> int:
    """
    Determine axis in a bivariate batch criteria is the primary axis.

    This is obtained on a per-query basis depending on the query context, or can
    be overriden on the cmdline.
    """
    if cmdopts['plot_primary_axis'] == 0:
        return 0

    if cmdopts['plot_primary_axis'] == 1:
        return 1

    if any(isinstance(criteria.criteria1, elt) for elt in primary_axis_bc):
        return 0

    return 1


def exp_range_calc(cmdopts: types.Cmdopts,
                   root_dir: pathlib.Path,
                   criteria) -> types.PathList:
    """
    Get the range of experiments to run/do stuff with. SUPER USEFUL.
    """
    exp_all = [root_dir / d for d in criteria.gen_exp_names(cmdopts)]

    exp_range = cmdopts['exp_range']

    if cmdopts['exp_range'] is not None:
        min_exp = int(exp_range.split(':')[0])
        max_exp = int(exp_range.split(':')[1])
        assert min_exp <= max_exp, \
            f"Min batch exp >= max batch exp({min_exp} vs. {max_exp})"

        return exp_all[min_exp: max_exp + 1]

    return exp_all


def exp_include_filter(inc_spec: tp.Optional[str],
                       target: tp.List,
                       n_exps: int):
    """Calculate which experiments to include in a calculation for something.

    Take a input list of experiment numbers to include, and returns the sublist
    specified by the inc_spec (of the form [x:y]). inc_spec is an `absolute`
    specification; if a given performance measure excludes exp0 then that case
    is handled internally so that array/list shapes work out when generating
    graphs if this function is used consistently everywhere.

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


def bivar_exp_labels_calc(exp_dirs: types.PathList) -> tp.Tuple[tp.List[str],
                                                                tp.List[str]]:
    """
    Calculate the labels for bivariant experiment graphs.
    """
    # Because sets are used, if a sub-range of experiments are selected for
    # collation, the selected range has to be an even multiple of the # of
    # experiments in the second batch criteria, or inter-experiment graph
    # generation won't work (the final CSV is always an MxN grid).
    xlabels_set = set()
    ylabels_set = set()
    for e in exp_dirs:
        pair = e.name.split('+')
        xlabels_set.add(pair[0])
        ylabels_set.add(pair[1])

    xlabels = sorted(list(xlabels_set))
    ylabels = sorted(list(ylabels_set))

    return (xlabels, ylabels)


def apply_to_expdef(var,
                    exp_def: definition.XMLExpDef) -> tp.Tuple[tp.Optional[xml.TagRmList],
                                                               tp.Optional[xml.TagAddList],
                                                               tp.Optional[xml.AttrChangeSet]]:
    """
    Apply a generated XML modifictions to an experiment definition.

    In this order:

    #. Remove existing XML tags
    #. Add new XML tags
    #. Change existing XML attributes
    """
    rmsl = var.gen_tag_rmlist()  # type: tp.List[xml.TagRmList]
    addsl = var.gen_tag_addlist()  # type: tp.List[xml.TagAddList]
    chgsl = var.gen_attr_changelist()  # type: tp.List[xml.AttrChangeSet]

    if rmsl:
        rms = rmsl[0]
        for r in rms:
            exp_def.tag_remove(r.path, r.tag)
    else:
        rms = None

    if addsl:
        adds = addsl[0]
        for a in adds:
            assert a.path is not None, "Can't add tag {a.tag} with no parent"
            exp_def.tag_add(a.path, a.tag, a.attr, a.allow_dup)
    else:
        adds = None

    if chgsl:
        chgs = chgsl[0]
        for c in chgs:
            exp_def.attr_change(c.path, c.attr, c.value)
    else:
        chgs = None

    return rms, adds, chgs


def pickle_modifications(adds: tp.Optional[xml.TagAddList],
                         chgs: tp.Optional[xml.AttrChangeSet],
                         path: pathlib.Path) -> None:
    """
    After applying XML modifications, pickle changes for later retrieval.
    """
    if adds is not None:
        adds.pickle(path)

    if chgs is not None:
        chgs.pickle(path)


def exp_template_path(cmdopts: types.Cmdopts,
                      batch_input_root: pathlib.Path,
                      dirname: str) -> pathlib.Path:
    """Calculate the path to the template input file in the batch experiment root.

     The file at this path will be Used as the de-facto template for generating
     per-run input files.

    """
    template = pathlib.Path(cmdopts['template_input_file'])
    return batch_input_root / dirname / template.stem


def get_n_robots(main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts,
                 exp_input_root: pathlib.Path,
                 exp_def: definition.XMLExpDef) -> int:
    """
    Get the # robots used for a specific :term:`Experiment`.
    """
    module = pm.pipeline.get_plugin_module(cmdopts['platform'])

    # Get # robots to send to shell cmds generator. We try:
    #
    # 1. Getting it from the current experiment definition, which contains all
    #    changes to the template input file EXCEPT those from batch criteria,
    #    which have already been written and pickled at this point.
    #
    # 2. Getting it from the pickled experiment definition (i.e., from the
    #    batch criteria which was used for this experiment).
    n_robots = module.population_size_from_def(exp_def,
                                               main_config,
                                               cmdopts)
    if n_robots <= 0:
        pkl_def = definition.unpickle(exp_input_root / config.kPickleLeaf)
        n_robots = module.population_size_from_pickle(pkl_def,
                                                      main_config,
                                                      cmdopts)

    assert n_robots > 0, "n_robots must be > 0"

    return n_robots


def df_fill(df: pd.DataFrame, policy: str) -> pd.DataFrame:
    """
    Fill missing cells in a dataframe according to the specified fill policy.
    """
    if policy == 'none':
        return df
    elif policy == 'pad':
        return df.fillna(method='pad')
    elif policy == 'zero':
        return df.fillna(value=0)
    else:
        raise RuntimeError(f"Bad fill policy {policy}")


@retry(OSError, tries=10, delay=0.100, backoff=1.1)  # type:ignore
def pickle_dump(obj: object, f: tp.IO) -> None:
    pickle.dump(obj, f)


def gen_scenario_spec(cmdopts: types.Cmdopts, **kwargs) -> tp.Dict[str, tp.Any]:
    # scenario is passed in kwargs during stage 5 (can't be passed via
    # --scenario in general )
    scenario = kwargs.get('scenario', cmdopts['scenario'])

    sgp = pm.module_load_tiered(project=cmdopts['project'],
                                path='generators.scenario_generator_parser')
    kw = sgp.ScenarioGeneratorParser().to_dict(scenario)

    return kw


def sphinx_ref(ref: str) -> str:
    try:
        # This is kind of a hack...
        if __sphinx_build_man__:  # type: ignore
            parts = ref.split('.')
            stripped = parts[-1]
            return stripped[:-1]

    except NameError:
        pass

    return ref


utf8open = functools.partial(open, encoding='UTF-8')
"""
Explictly specify that the type of file being opened is UTF-8, which is should
be for almost everything in SIERRA.
"""

__api__ = [
    'ArenaExtent',
    'Sigmoid',
    'ReLu',
    'dir_create_checked',
    'path_exists',
    'get_primary_axis',
    'exp_range_calc',
    'exp_include_filter',
    'apply_to_expdef',
    'pickle_modifications',
    'exp_template_path',
    'get_n_robots',
    'df_fill',
    'utf8open',
]
