# Copyright 2018 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
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
Common calculations used by multiple performance measures.
"""

import os
import math
import copy
import typing as tp
import pandas as pd
import numpy as np

import core.utils
from core.variables.swarm_size import SwarmSize
from core.variables import batch_criteria as bc


class ProjectivePerformanceCalculatorUnivar:
    r"""
    Calculates the following measure for each experiment in a univariate batched experiment. The
    batch criteria must be derived from :class:`~variables.swarm_size.SwarmSize`, or this measure
    will (probably) not have much meaning.

    .. math::
        \frac{Performance(exp_i)}{Distance(exp_, exp{i}) * Performance(exp_{i})}

    Domain: [0, inf)

    If things are X amount better/worse (in terms of increasing/decreasing the swarm's potential for
    performance) than they were for exp0 (baseline for comparison), then we *should* see a
    corresponding increase/decrease in the level of observed performance.

    Only valid for exp i, i > 0 (you are comparing with a projected performance value of exp0 after
    all).
    """

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str, projection_type: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.projection_type = projection_type
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def __call__(self, batch_criteria: bc.BatchCriteria):
        path = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        perf_df = pd.read_csv(path, sep=';')
        exp_dirs = batch_criteria.gen_exp_dirnames(self.cmdopts)
        exp0_dir = exp_dirs[0]
        scale_cols = [c for c in perf_df.columns if c not in [exp0_dir]]
        proj_df = pd.DataFrame(columns=scale_cols, index=[0])

        xvals = batch_criteria.graph_xticks(self.cmdopts)

        for exp_num in range(1, len(scale_cols) + 1):
            exp_col = exp_dirs[exp_num]
            exp_prev_col = exp_dirs[exp_num - 1]

            obs = perf_df.tail(1)[exp_col].values[0]
            obs_prev = perf_df.tail(1)[exp_prev_col].values[0]
            similarity = float(xvals[exp_num]) / float(xvals[exp_num - 1])

            if self.projection_type == "positive":
                proj_df[exp_col] = ProjectivePerformanceCalculatorUnivar.__calc_positive(obs,
                                                                                         obs_prev,
                                                                                         similarity)
            elif self.projection_type == "negative":
                proj_df[exp_col] = ProjectivePerformanceCalculatorUnivar.__calc_negative(obs,
                                                                                         obs_prev,
                                                                                         similarity)
        return proj_df

    @staticmethod
    def __calc_positive(observed: float, exp0: float, similarity: float):
        return observed / (exp0 * similarity)

    @staticmethod
    def __calc_negative(observed: float, exp0: float, similarity: float):
        return observed / (exp0 * (1.0 - similarity))


class ProjectivePerformanceCalculatorBivar:
    r"""
    Calculates the following measure for each experiment in a bivariate batched experiment. One of
    the variables must be derived from :class:`~variables.swarm_size.SwarmSize`.

    .. math::
        \frac{Performance(exp_i)}{Distance(exp_i, exp_{i-1}) * Performance(exp_i)}

    Domain: [0, inf)

    If things are X amount better/worse (in terms of increasing/decreasing the swarm's potential for
    performance) than they were for exp0 (baseline for comparison), then we *should* see a
    corresponding increase/decrease in the level of observed performance.

    Only valid for exp i, i > 0 (you are comparing with a projected performance value of exp0 after
    all).
    """

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str, projection_type: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.projection_type = projection_type
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def __call__(self, batch_criteria: bc.BatchCriteria):
        path = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        perf_df = pd.read_csv(path, sep=';')

        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.
        if isinstance(batch_criteria.criteria1, SwarmSize):
            return self.__project_vals_row(perf_df, batch_criteria)
        else:
            return self.__project_vals_col(perf_df, batch_criteria)

    def __project_vals_col(self, perf_df: pd.DataFrame, batch_criteria: bc.BatchCriteria):
        proj_df = pd.DataFrame(columns=perf_df.columns[1:], index=perf_df.index)
        yvals = batch_criteria.graph_yticks(self.cmdopts)

        for i in range(0, len(proj_df.index)):
            for j in range(0, len(proj_df.columns)):
                similarity = float(yvals[j]) / float(yvals[j - 1])
                obs = csv_3D_value_iloc(perf_df, i, j, slice(-1, None))
                prev_obs = csv_3D_value_iloc(perf_df, i, j - 1, slice(-1, None))

                if self.projection_type == 'positive':
                    proj_df.iloc[i, j] = ProjectivePerformanceCalculatorBivar.__calc_positive(obs,
                                                                                              prev_obs,
                                                                                              similarity)
                elif self.projection_type == 'negative':
                    proj_df.iloc[i, j] = ProjectivePerformanceCalculatorBivar.__calc_negative(obs,
                                                                                              prev_obs,
                                                                                              similarity)
        return proj_df

    def __project_vals_row(self, perf_df: pd.DataFrame, batch_criteria: bc.BatchCriteria):
        proj_df = pd.DataFrame(columns=perf_df.columns, index=perf_df.index[1:])
        xvals = batch_criteria.graph_xticks(self.cmdopts)

        for i in range(0, len(proj_df.index)):
            for j in range(0, len(proj_df.columns)):
                similarity = float(xvals[i]) / float(xvals[i - 1])
                obs = csv_3D_value_iloc(perf_df, i, j, slice(-1, None))
                prev_obs = csv_3D_value_iloc(perf_df, i - 1, j, slice(-1, None))

                if self.projection_type == 'positive':
                    proj_df.iloc[i, j] = ProjectivePerformanceCalculatorBivar.__calc_positive(obs,
                                                                                              prev_obs,
                                                                                              similarity)
                elif self.projection_type == 'negative':
                    proj_df.iloc[i, j] = ProjectivePerformanceCalculatorBivar.__calc_negative(obs,
                                                                                              prev_obs,
                                                                                              similarity)

        return proj_df

    @staticmethod
    def __calc_positive(obs: float, prev_obs: float, similarity: float):
        return obs / (prev_obs * similarity)

    @staticmethod
    def __calc_negative(obs: float, prev_obs: float, similarity: float):
        return obs / (prev_obs * (1.0 - similarity))


class FractionalLosses:
    r"""
    Base class for calculating the fractional performance losses of a swarm across a range of swarm
    sizes. Performance losses are defined as follows for a swarm of size N of `interacting` robots,
    as oppopsed to a swarm of size N of `non-interacting` robots (taken from :xref:`Harwell2019`):

    .. math::
       \begin{equation}
         P_{lost}(N,\kappa,t) =
         \begin{cases}
           {P(1,\kappa,t)}{t_{lost}^{1}(t)} & \text{if N = 1}
           \\
           P(N,\kappa,t){t_{lost}^{N}(t)} - {N}{P_{lost}(1,\kappa,t)}& \text{if N  $>$ 1}
           \\
       \end{cases}
       \end{equation}

    Does not do any calculations, but contains functionality and definitions common to both
    :class:`~perf_measures.common.FractionalLossesUnivar` and
    :class:`~perf_measures.common.FractionalLossesBivar`.
    """

    def __init__(self,
                 cmdopts: tp.Dict[str, str],
                 inter_perf_csv: str,
                 ca_in_csv: str,
                 batch_criteria: bc.BatchCriteria):
        self.cmdopts = cmdopts
        self.batch_output_root = cmdopts["collate_root"]
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.ca_in_stem = ca_in_csv.split('.')[0]

        # Just need to get # timesteps per simulation which is the same for all
        # simulations/experiments, so we pick exp0 for simplicity to calculate
        exp_def = core.utils.unpickle_exp_def(os.path.join(cmdopts["generation_root"],
                                                           batch_criteria.gen_exp_dirnames(
            self.cmdopts)[0],
            "exp_def.pkl"))

        # Integers always seem to be pickled as floats, so you can't convert directly without an
        # exception.
        for path, attr, value in exp_def:
            if path == './/experiment' and attr == 'length':
                length = int(float(value))
            elif path == './/experiment' and attr == 'ticks_per_second':
                ticks = int(float(value))
        self.duration = length * ticks


class FractionalLossesUnivar(FractionalLosses):
    """
    Fractional losses calculation for univariate batch criteria.

    Does not require the variable to be swarm size, but the metric will (probably) not be of much
    value if that is not the case. Does not require swarm sizes to be powers of 2.

    """

    def calculate(self, batch_criteria: bc.BatchCriteria):
        ca_in_path = os.path.join(self.batch_output_root, self.ca_in_stem + '.csv')
        assert(os.path.exists(ca_in_path)), "FATAL: {0} does not exist".format(ca_in_path)
        ca_in_df = pd.read_csv(ca_in_path, sep=';')

        perf_path = os.path.join(self.batch_output_root, self.inter_perf_stem + '.csv')
        assert(os.path.exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = pd.read_csv(perf_path, sep=';')

        exp0_dirname = batch_criteria.gen_exp_dirnames(self.cmdopts)[0]
        scale_cols = [c for c in ca_in_df.columns if c not in [exp0_dirname]]

        # First calculate the time lost per timestep for a swarm of size N due to collision
        # avoidance interference
        plost_n = self.__calc_plost_n(ca_in_df, perf_df, batch_criteria)

        # Calculate fractional losses for all swarm sizes
        fl_df = FractionalLossesUnivar.__calc_fl(perf_df, plost_n, scale_cols)

        # By definition, no fractional losses with 1 robot
        fl_df.insert(0, exp0_dirname, 0.0)
        return fl_df

    def __calc_plost_n(self,
                       ca_in_df: pd.DataFrame,
                       perf_df: pd.DataFrame,
                       batch_criteria: bc.BatchCriteria):
        """
        Calculated as follows for all swarm sizes N in the batch:

        performance exp0 * tlost_1 (for exp0)

        performance exp0 * (tlost_N - N * tlost_1) / N (else)

        This gives how much MORE performance was lost in the entire simulation as a result of a
        swarm of size N, as opposed to a group of N robots that do not interact with each other,
        only the arena walls.
        """
        plost_n = pd.DataFrame(columns=perf_df.columns, index=[0])
        exp0_dir = perf_df.columns[0]
        scale_cols = [c for c in ca_in_df.columns if c not in [exp0_dir]]
        swarm_sizes = batch_criteria.swarm_sizes(self.cmdopts)
        plost_n[exp0_dir] = perf_df.tail(1)[exp0_dir] * (ca_in_df.tail(1)[exp0_dir])

        perf_taili = perf_df.index[-1]
        for c in scale_cols:
            n_robots = swarm_sizes[list(plost_n.columns).index(c)]

            if perf_df.loc[perf_taili, c] == 0:
                plost_n.loc[0, c] = math.inf
            else:
                plost_n.loc[0, c] = perf_df.loc[perf_taili, c] * (ca_in_df.loc[perf_taili, c] -
                                                                  ca_in_df.loc[perf_taili, exp0_dir] * n_robots) / n_robots
        return plost_n

    @staticmethod
    def __calc_fl(perf_df: pd.DataFrame,
                  plost_n: pd.DataFrame,
                  scale_cols: tp.List[str]):
        """
        Calculate fractional losses as:

        (performance lost with N robots / performance with N robots)

        """
        fl_df = pd.DataFrame(columns=scale_cols, index=[0])

        perf_taili = perf_df.index[-1]
        for c in scale_cols:
            if (perf_df.loc[perf_taili, c] == 0):
                fl_df.loc[0, c] = 1.0
            else:
                fl_df.loc[0, c] = round(plost_n.loc[0, c] / perf_df.loc[perf_taili, c], 4)

        return fl_df


class FractionalLossesBivar(FractionalLosses):
    """
    Fractional losses calculation for bivariate batch criteria.

    Does not require the variable to be swarm size, but the metric will (probably) not be of much
    value if that is not the case. Does not require swarm sizes to be powers of two.
    """

    def calculate(self, batch_criteria: bc.BatchCriteria):
        ca_in_path = os.path.join(self.batch_output_root, self.ca_in_stem + '.csv')
        assert(os.path.exists(ca_in_path)), "FATAL: {0} does not exist".format(ca_in_path)
        ca_in_df = pd.read_csv(ca_in_path, sep=';')

        perf_path = os.path.join(self.batch_output_root, self.inter_perf_stem + '.csv')
        assert(os.path.exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = pd.read_csv(perf_path, sep=';')

        # Calculate plost for all swarm sizes
        plost_n = self.__calc_plost_n(ca_in_df, perf_df, batch_criteria)

        # Calculate fractional losses for al swarm sizes
        fl_df = FractionalLossesBivar.__calc_fl(perf_df, plost_n)

        return fl_df

    def __calc_plost_n(self,
                       ca_in_df: pd.DataFrame,
                       perf_df: pd.DataFrame,
                       batch_criteria: bc.BatchCriteria):
        """
        Calculated as follows for all swarm sizes N in the batch:

        performance exp0 * tlost_1 (for exp0)

        performance exp0 * (tlost_N - N * tlost_1) / N (else)

        This gives how much MORE performance was lost in the entire simulation as a result of a
        swarm of size N, as opposed to a group of N robots that do not interact with each other,
        only the arena walls.
        """
        plost_n = pd.DataFrame(columns=perf_df.columns, index=perf_df.index)
        exp0_dir = perf_df.columns[0]
        swarm_sizes = batch_criteria.swarm_sizes(self.cmdopts)

        # Calc for exp(0,0)
        t_lost0 = csv_3D_value_loc(ca_in_df,
                                   0,  # exp0 = 1 robot
                                   exp0_dir,
                                   slice(-1, None))  # Last in temporal seq = cum avg
        perf0 = csv_3D_value_loc(perf_df,
                                 0,  # exp0 = 1 robot
                                 exp0_dir,
                                 slice(-1, None))  # Last in temporal seq = cum count

        plost_n.iloc[0, 0] = float(perf0) * float(t_lost0)

        # Calc for general case
        for i in range(0, len(plost_n.index)):
            for j in range(0, len(plost_n.columns)):
                if i == 0 and plost_n.columns[j] == exp0_dir:  # exp(0,0)
                    continue

                n_blocks = csv_3D_value_iloc(perf_df,
                                             i,
                                             j,
                                             slice(-1, None))

                if n_blocks == 0:
                    plost_n.iloc[i, j] = math.inf
                else:
                    t_lostN = csv_3D_value_iloc(ca_in_df,
                                                # Last row = N robots
                                                len(ca_in_df.index) - 1,
                                                j,
                                                slice(-1, None))  # Last in temporal seq = cum avg

                    # We need to know which of the 2 variables was swarm size, in order to determine
                    # the correct dimension along which to compute the metric, which depends on
                    # performance between adjacent swarm sizes.
                    if isinstance(batch_criteria.criteria1, SwarmSize):
                        n_robots = swarm_sizes[i]
                    else:
                        n_robots = swarm_sizes[j]

                    plost_n.iloc[i, j] = n_blocks * \
                        (t_lostN - t_lost0 * float(n_robots)) / float(n_robots)
        return plost_n

    @staticmethod
    def __calc_fl(perf_df: pd.DataFrame, plost_n: pd.DataFrame):
        """
        Calculate fractional losses as:

        (performance lost with N robots / performance with N robots)

        """
        fl_df = pd.DataFrame(columns=perf_df.columns, index=perf_df.index)
        exp0_dir = perf_df.columns[0]

        for i in range(0, len(fl_df.index)):
            for c in fl_df.columns:
                if i == 0 and c == exp0_dir:  # exp(0,0)
                    fl_df.loc[i, c] = 0.0  # By definition, no fractional losses in exp(0,0)
                    continue

                perf_N = csv_3D_value_loc(perf_df, i, c, slice(-1, None))
                if perf_N == 0:
                    fl_df.loc[i, c] = 1.0
                else:
                    fl_df.loc[i, c] = round(plost_n.loc[i, c] / perf_N, 4)
        return fl_df


def csv_3D_value_loc(df, xslice, ycol, zslice):
    # When collated, the column of data is written as a numpy array to string, so we
    # have to reparse it as an actual array
    arr = np.fromstring(df.loc[xslice, ycol][1:-1], dtype=np.float, sep=' ')
    # The second index is an artifact of how numpy represents scalars (1 element arrays).
    return arr[zslice][0]


def csv_3D_value_iloc(df, xslice, yslice, zslice):
    # When collated, the column of data is written as a numpy array to string, so we
    # have to reparse it as an actual array
    arr = np.fromstring(df.iloc[xslice, yslice][1:-1], dtype=np.float, sep=' ')
    # The second index is an artifact of how numpy represents scalars (1 element arrays).
    return arr[zslice][0]
