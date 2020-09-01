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
import logging

import pandas as pd
import numpy as np

import core.utils
from core.variables.population_size import PopulationSize
from core.variables import batch_criteria as bc
from core.graphs.heatmap import Heatmap
from core.graphs.batch_ranged_graph import BatchRangedGraph


class PerfLostInteractiveSwarmUnivar:
    r"""
    Univariate calculator for the perforance lost per robot for a swarm of size N of `interacting`
    robots, as oppopsed to a  swarm of size N of `non-interacting` robots.

    Calculated as (taken from :xref:`Harwell2019`):

    .. math::
       P_{lost}(N,\kappa,T) =
       \begin{cases}
         {P(1,\kappa,T)}{t_{lost}^{1}} & \text{if N = 1} \\
           \frac{P(N,\kappa,T){t_{lost}^{N}} - {N}{P_{lost}(1,\kappa,T)}}{N} & \text{if N  $>$ 1}
       \end{cases}

    Swarms exhibiting high levels of emergent behavior should have `positive` values of performance
    loss (i.e. they performed `better` than a swarm of N independent robots).

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.
    """

    def __init__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str) -> None:
        self.cmdopts = cmdopts
        self.batch_output_root = cmdopts["collate_root"]
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.interference_stem = interference_count_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.UnivarBatchCriteria):
        # Get .csv with interference info
        interference_path = os.path.join(self.batch_output_root, self.interference_stem + '.csv')
        assert(os.path.exists(interference_path)
               ), "FATAL: {0} does not exist".format(interference_path)
        interference_df = pd.read_csv(interference_path, sep=';')

        # Get .csv with performance info
        perf_path = os.path.join(self.batch_output_root, self.inter_perf_stem + '.csv')
        assert(os.path.exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = pd.read_csv(perf_path, sep=';')

        exp0_dirname = batch_criteria.gen_exp_dirnames(self.cmdopts)[0]

        # Calculate the performatime lost per timestep for a swarm of size N due to collision
        # avoidance interference
        plost_n = self.__calc_plost_n(interference_df,
                                      perf_df,
                                      batch_criteria)
        # By definition, no performance losses with 1 robot
        plost_n.loc[0, exp0_dirname] = 0.0
        return plost_n

    def __calc_plost_n(self,
                       interference_df: pd.DataFrame,
                       perf_df: pd.DataFrame,
                       batch_criteria: bc.UnivarBatchCriteria):
        """
        Calculated as follows for all swarm sizes N in the batch:

        performance exp0 * tlost_1 (for exp0)

        performance exp0 * (tlost_N - N * tlost_1) / N (else)
        """
        plost_n = pd.DataFrame(columns=perf_df.columns, index=[0])
        exp0_dir = perf_df.columns[0]
        scale_cols = [c for c in interference_df.columns if c not in [exp0_dir]]
        populations = batch_criteria.populations(self.cmdopts)
        plost_n[exp0_dir] = perf_df.tail(1)[exp0_dir] * (interference_df.tail(1)[exp0_dir])

        perf_taili = perf_df.index[-1]
        for c in scale_cols:
            n_robots = populations[list(plost_n.columns).index(c)]

            if perf_df.loc[perf_taili, c] == 0:
                plost_n.loc[0, c] = math.inf
            else:
                plost_n.loc[0, c] = perf_df.loc[perf_taili, c] * (interference_df.loc[perf_taili, c] -
                                                                  interference_df.loc[perf_taili, exp0_dir] * n_robots) / n_robots
        return plost_n


class PerfLostInteractiveSwarmBivar:
    """
    Bivariate calculator for the perforance lost per-robot for a swarm of size N of `interacting`
    robots, as oppopsed to a  swarm of size N of `non-interacting` robots. See
    :class:`~core.perf_measures.common.PerfLostInteractiveSwarmUnivar` for a description of the
    mathematical calculations performed by this class.
    """

    def __init__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str) -> None:
        self.cmdopts = cmdopts
        self.batch_output_root = cmdopts["collate_root"]
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.interference_stem = interference_count_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.BivarBatchCriteria):
        # Get .csv with interference info
        interference_path = os.path.join(self.batch_output_root, self.interference_stem + '.csv')
        assert(os.path.exists(interference_path)
               ), "FATAL: {0} does not exist".format(interference_path)
        interference_df = pd.read_csv(interference_path, sep=';')

        # Get .csv with performance info
        perf_path = os.path.join(self.batch_output_root, self.inter_perf_stem + '.csv')
        assert(os.path.exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = pd.read_csv(perf_path, sep=';')

        exp0_dirname = batch_criteria.gen_exp_dirnames(self.cmdopts)[0]

        # Calculate the performatime lost per timestep for a swarm of size N due to collision
        # avoidance interference
        plost_n = self.__calc_plost_n(interference_df, perf_df, batch_criteria)

        # By definition, no performance losses with 1 robot
        plost_n.insert(0, exp0_dirname, 0.0)
        return plost_n

    def __calc_plost_n(self,
                       interference_df: pd.DataFrame,
                       perf_df: pd.DataFrame,
                       batch_criteria: bc.BivarBatchCriteria):
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
        populations = batch_criteria.populations(self.cmdopts)

        # Calc for exp(0,0)
        t_lost0 = csv_3D_value_loc(interference_df,
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
                    t_lostN = csv_3D_value_iloc(interference_df,
                                                # Last row = N robots
                                                len(interference_df.index) - 1,
                                                j,
                                                slice(-1, None))  # Last in temporal seq = cum avg

                    # We need to know which of the 2 variables was swarm size, in order to determine
                    # the correct axis along which to compute the metric, which depends on
                    # performance between adjacent swarm sizes.
                    if isinstance(batch_criteria.criteria1, PopulationSize) or self.cmdopts['plot_primary_axis'] == '0':
                        n_robots = populations[i][0]  # same population in all columns
                    else:
                        n_robots = populations[0][j]  # same population in all rows

                    plost_n.iloc[i, j] = n_blocks * \
                        (t_lostN - t_lost0 * float(n_robots)) / float(n_robots)

        return plost_n


class FractionalLosses:
    """
    Base class for calculating the fractional performance losses of a swarm across a range of swarm
    sizes. Does not do any calculations, but contains functionality and definitions common to both
    :class:`~core.perf_measures.common.FractionalLossesUnivar` and
    :class:`~core.perf_measures.common.FractionalLossesBivar`.

    """

    def __init__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 batch_criteria: bc.IConcreteBatchCriteria) -> None:
        self.cmdopts = cmdopts
        self.batch_output_root = cmdopts["collate_root"]
        self.inter_perf_csv = inter_perf_csv
        self.interference_count_csv = interference_count_csv
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.interference_stem = interference_count_csv.split('.')[0]

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
    r"""
    Fractional losses calculation for univariate batch criteria. Fractional performance losses are
    defined as:

    .. math::
       :label: pm-fractional-losses

       FL(N,\kappa) = \frac{P_{lost}(N,\kappa,T)}{P(N,\kappa,T)}

    (i.e the fraction of performance which has been lost due to inter-robot interference).

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.
    """

    def calculate(self, batch_criteria: bc.UnivarBatchCriteria):
        # First calculate the performance lost due to inter-robot interference
        plost_n = PerfLostInteractiveSwarmUnivar(self.cmdopts,
                                                 self.inter_perf_csv,
                                                 self.interference_count_csv).calculate(batch_criteria)

        # Get .csv with interference info
        interference_path = os.path.join(self.batch_output_root, self.interference_stem + '.csv')
        assert(os.path.exists(interference_path)
               ), "FATAL: {0} does not exist".format(interference_path)
        interference_df = pd.read_csv(interference_path, sep=';')

        # Get .csv with performance info
        perf_path = os.path.join(self.batch_output_root, self.inter_perf_stem + '.csv')
        assert(os.path.exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = pd.read_csv(perf_path, sep=';')

        exp0_dirname = batch_criteria.gen_exp_dirnames(self.cmdopts)[0]
        scale_cols = [c for c in interference_df.columns if c not in [exp0_dirname]]

        # Calculate fractional losses for all swarm sizes
        fl_df = FractionalLossesUnivar.__calc_fl(perf_df, plost_n, scale_cols)

        # By definition, no fractional losses with 1 robot
        fl_df.insert(0, exp0_dirname, 0.0)
        return fl_df

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
    Fractional losses calculation for bivariate batch criteria. See
    :class:`~core.perf_measures.common.FractionalLossesUnivar` for a description of the mathematical
    calculations performed by this class.

    """

    def calculate(self, batch_criteria: bc.BivarBatchCriteria):
        # First calculate the performance lost due to inter-robot interference
        plost_n = PerfLostInteractiveSwarmBivar(self.cmdopts,
                                                self.inter_perf_csv,
                                                self.interference_count_csv).calculate(batch_criteria)

        # Get .csv with performance info
        perf_path = os.path.join(self.batch_output_root, self.inter_perf_stem + '.csv')
        assert(os.path.exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = pd.read_csv(perf_path, sep=';')

        # Calculate fractional losses for all swarm sizes
        fl_df = FractionalLossesBivar.__calc_fl(perf_df, plost_n)

        return fl_df

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


class WeightedPMUnivar():
    """
    Univariate calculator for a weighted performance measure.

    """

    def __init__(self,
                 cmdopts: dict,
                 output_leaf: str,
                 ax1_leaf: str,
                 ax2_leaf: str,
                 ax1_alpha: float,
                 ax2_alpha: float,
                 title: str) -> None:
        self.cmdopts = copy.deepcopy(cmdopts)
        self.output_leaf = output_leaf
        self.ax1_leaf = ax1_leaf
        self.ax2_leaf = ax2_leaf
        self.ax1_alpha = ax1_alpha
        self.ax2_alpha = ax2_alpha
        self.title = title

    def generate(self, batch_criteria: bc.IConcreteBatchCriteria):
        csv1_istem = os.path.join(self.cmdopts["collate_root"], self.ax1_leaf)
        csv2_istem = os.path.join(self.cmdopts["collate_root"], self.ax2_leaf)
        csv1_ipath = csv1_istem + '.csv'
        csv2_ipath = csv2_istem + '.csv'

        csv_ostem = os.path.join(self.cmdopts["collate_root"], self.output_leaf)
        png_ostem = os.path.join(self.cmdopts["graph_root"], self.output_leaf)

        if not os.path.exists(csv1_ipath) or not os.path.exists(csv2_ipath):
            logging.debug("Not generating univariate weighted performance measure: %s or %s does not exist",
                          csv1_ipath, csv2_ipath)
            return

        ax1_df = pd.read_csv(csv1_istem + '.csv', sep=';')
        ax2_df = pd.read_csv(csv2_istem + '.csv', sep=';')
        out_df = ax1_df * self.ax1_alpha + ax2_df * self.ax2_alpha

        out_df.to_csv(csv_ostem + '.csv', sep=';', index=False)

        xticks = batch_criteria.graph_xticks(self.cmdopts)
        len_diff = len(xticks) - len(out_df.columns)

        BatchRangedGraph(inputy_stem_fpath=csv_ostem,
                         output_fpath=png_ostem + '.png',
                         title=self.title,
                         ylabel="Value",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         xticks=xticks[len_diff:]).generate()


class WeightedPMBivar():
    """
    Bivariate calculator for a weighted performance measure.
    """

    def __init__(self,
                 cmdopts: dict,
                 output_leaf: str,
                 ax1_leaf: str,
                 ax2_leaf: str,
                 ax1_alpha: float,
                 ax2_alpha: float,
                 title: str) -> None:
        self.cmdopts = copy.deepcopy(cmdopts)
        self.output_leaf = output_leaf
        self.ax1_leaf = ax1_leaf
        self.ax2_leaf = ax2_leaf
        self.ax1_alpha = ax1_alpha
        self.ax2_alpha = ax2_alpha
        self.title = title

    def generate(self, batch_criteria: bc.IConcreteBatchCriteria):
        csv1_istem = os.path.join(self.cmdopts["collate_root"], self.ax1_leaf)
        csv2_istem = os.path.join(self.cmdopts["collate_root"], self.ax2_leaf)
        csv1_ipath = csv1_istem + '.csv'
        csv2_ipath = csv2_istem + '.csv'

        csv_ostem = os.path.join(self.cmdopts["collate_root"], self.output_leaf)
        png_ostem = os.path.join(self.cmdopts["graph_root"], self.output_leaf)

        if not os.path.exists(csv1_ipath) or not os.path.exists(csv2_ipath):
            logging.debug("Not generating bivariate weighted performance measure: %s or %s does not exist",
                          csv1_ipath, csv2_ipath)
            return

        ax1_df = pd.read_csv(csv1_istem + '.csv', sep=';')
        ax2_df = pd.read_csv(csv2_istem + '.csv', sep=';')
        out_df = ax1_df * self.ax1_alpha + ax2_df * self.ax2_alpha
        out_df.to_csv(csv_ostem + '.csv', sep=';', index=False)

        xlabels = batch_criteria.graph_xticklabels(self.cmdopts)
        ylabels = batch_criteria.graph_yticklabels(self.cmdopts)

        len_xdiff = len(xlabels) - len(out_df.index)
        len_ydiff = len(ylabels) - len(out_df.columns)

        Heatmap(input_fpath=csv_ostem + '.csv',
                output_fpath=png_ostem + '.png',
                title=self.title,
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts)[len_xdiff:],
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)[len_ydiff:]).generate()


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


__api__ = [
    'PerfLostInteractiveSwarmUnivar',
    'PerfLostInteractiveSwarmBivar',
    'FractionalLosses',
    'FractionalLossesUnivar',
    'FractionalLossesBivar',
]
