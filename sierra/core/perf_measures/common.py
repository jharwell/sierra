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

# Core packages
import os
import math
import copy
import typing as tp
import logging

# 3rd party packages
import pandas as pd
import numpy as np

# Project packages
import sierra.core.utils
from sierra.core.variables.population_size import PopulationSize
from sierra.core.variables import batch_criteria as bc
from sierra.core.graphs.heatmap import Heatmap
from sierra.core.graphs.summary_line_graph import SummaryLinegraph
import sierra.core.config
from sierra.core.xml_luigi import XMLAttrChangeSet
from sierra.core.variables import population_size
from sierra.core.variables import population_constant_density as pcd
from sierra.core.variables import population_variable_density as pvd
import sierra.core.stat_kernels

################################################################################
# Base Classes
################################################################################


class BaseSteadyStatePerfLostInteractiveSwarm():
    r"""
    Calculate the performance lost due to inter-robot interference in an interactive swarm of
    :math:`\mathcal{N}` robots.

    .. math::
       P_{lost}(N,\kappa,T) =
       \begin{cases}
         {P(1,\kappa,T)}{t_{lost}^{1}} & \text{if N = 1} \\
           \frac{P(N,\kappa,T){t_{lost}^{N}} - {N}{P_{lost}(1,\kappa,T)}}{N} & \text{if N  $>$ 1}
       \end{cases}

    Args:
        perf1: The performance achieved by a single robot, :math:`P(1,\kappa,T)`.

        tlost1: The amount of time lost due to wall collision avoidance by a single robot,
                :math:`t_{lost}^1`.

        perfN: The performance achieved by :math:`\mathcal{N}` robots,
               :math:`P(\mathcal{N},\kappa,T)`.

        tlostN: The amount of time lost due to wall collision avoidance `and` inter-robot
                interference in a swarm of :math:`\mathcal{N}` robots, :math:`t_{lost}^{N}`

        n_robots: The number of robots in the swarm, :math:`\mathcal{N}`.
    """

    @staticmethod
    def kernel(perf1: float,
               tlost1: float,
               perfN: float,
               tlostN: float,
               n_robots: int) -> float:

        plost1 = perf1 * tlost1

        if perfN == 0:
            return math.inf  # No performance = 100% interactive loss
        else:
            return (perfN * tlostN - n_robots * plost1) / n_robots


class BaseSteadyStateFL:
    r"""
    Base class for calculating the fractional performance losses of a swarm across a range of swarm
    sizes.

    Fractional performance losses are defined as:

    .. math::
       :label: pm-fractional-losses

       FL(N,\kappa) = \frac{P_{lost}(N,\kappa,T)}{P(N,\kappa,T)}

    (i.e the fraction of performance which has been lost due to inter-robot interference).

    """
    @staticmethod
    def kernel(perfN: float, plostN: float) -> float:
        if perfN == 0:
            return 1.0  # No performance = 100% fractional loss
        else:
            return round(plostN / perfN, 8)

    def __init__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.cmdopts = cmdopts
        self.batch_stat_collate_root = cmdopts["batch_stat_collate_root"]
        self.inter_perf_csv = inter_perf_csv
        self.interference_count_csv = interference_count_csv
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.interference_stem = interference_count_csv.split('.')[0]

        # Just need to get # timesteps per simulation which is the same for all
        # simulations/experiments, so we pick exp0 for simplicity to calculate
        exp_def = XMLAttrChangeSet.unpickle(os.path.join(cmdopts["batch_input_root"],
                                                         criteria.gen_exp_dirnames(self.cmdopts)[0],
                                                         sierra.core.config.kPickleLeaf))

        # Integers always seem to be pickled as floats, so you can't convert directly without an
        # exception.
        for path, attr, value in exp_def:
            if path == './/experiment' and attr == 'length':
                length = int(float(value))
            elif path == './/experiment' and attr == 'ticks_per_second':
                ticks = int(float(value))
        self.duration = length * ticks

################################################################################
# Univariate Classes
################################################################################


class SteadyStatePerfLostInteractiveSwarmUnivar(BaseSteadyStatePerfLostInteractiveSwarm):
    """
    Calculated as follows for all swarm sizes N in the batch:

    plost 1 robot = 0 # By definition

    plost N robots = :class:`~BaseSteadyStatePerfLostInteractiveSwarm`.kernel().

    This gives how much MORE performance was lost in the entire simulation as a result of a swarm of
    size N, as opposed to a group of N robots that do not interact with each other, only the arena
    walls. Swarms exhibiting high levels of emergent behavior should have `positive` values of
    performance loss (i.e. they performed `better` than a swarm of N independent robots).

    Does not require the batch criteria to be
    :class:`~sierra.core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    """

    @staticmethod
    def df_kernel(criteria: bc.UnivarBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_interference: tp.Dict[str, pd.DataFrame],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        """
        Calculated as follows for all swarm sizes N in the batch:

        performance exp0 * tlost_1 (for exp0)

        performance exp0 * (tlost_N - N * tlost_1) / N (else)

        This gives how much MORE performance was lost in the entire simulation as a result of a
        swarm of size N, as opposed to a group of N robots that do not interact with each other,
        only the arena walls.
        """
        n_exp = criteria.n_exp()
        populations = criteria.populations(cmdopts)
        plostn_dfs = {}

        # Case 1: 1 robot/exp0
        exp0 = list(collated_perf.keys())[0]

        plostn_dfs[exp0] = pd.DataFrame(columns=collated_perf[exp0].columns,
                                        index=[0])  # Steady state

        plostn_dfs[exp0].loc[0, :] = 0.0  # By definition, no performance losses in exp0

        # Case 2 : N>1 robots
        for i in range(1, n_exp):
            expx = list(collated_perf.keys())[i]
            expx_perf_df = collated_perf[expx]
            expx_interference_df = collated_interference[expx]
            plostn_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state
            n_robots = populations[i]

            exp0 = list(collated_perf.keys())[0]
            exp0_perf_df = collated_perf[exp0]
            exp0_interference_df = collated_interference[exp0]

            for sim in expx_perf_df.columns:
                # steady state
                tlost1 = exp0_interference_df.loc[exp0_interference_df.index[-1], sim]
                perf1 = exp0_perf_df.loc[exp0_perf_df.index[-1], sim]  # steady state

                # steady state
                tlostN = expx_interference_df.loc[expx_interference_df.index[-1], sim]
                perfN = expx_perf_df.loc[expx_perf_df.index[-1], sim]  # steady state

                plostN = BaseSteadyStatePerfLostInteractiveSwarm.kernel(perf1=perf1,
                                                                        tlost1=tlost1,
                                                                        perfN=perfN,
                                                                        tlostN=tlostN,
                                                                        n_robots=n_robots)

                plostn_dfs[expx].loc[0, sim] = BaseSteadyStatePerfLostInteractiveSwarm.kernel(perf1=perf1,
                                                                                              tlost1=tlost1,
                                                                                              perfN=perfN,
                                                                                              tlostN=tlostN,
                                                                                              n_robots=n_robots)

        return plostn_dfs


class SteadyStateFLUnivar(BaseSteadyStateFL):
    """
    Fractional losses calculation for univariate batch criteria.

    Does not require the batch criteria to be
    :class:`~sierra.core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  collated_perf: tp.Dict[str, pd.DataFrame],
                  collated_plost: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        n_exp = criteria.n_exp()
        fl_dfs = {}

        exp0 = list(collated_perf.keys())[0]

        fl_dfs[exp0] = pd.DataFrame(columns=collated_perf[exp0].columns,
                                    index=[0])  # Steady state

        fl_dfs[exp0].loc[0, :] = 0.0  # By definition, no fractional losses in exp0

        for i in range(1, n_exp):
            expx = list(collated_perf.keys())[i]
            expx_plost_df = collated_plost[expx]
            expx_perf_df = collated_perf[expx]
            fl_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                        index=[0])  # Steady state

            for sim in expx_perf_df.columns:
                plost_x = expx_plost_df.loc[expx_plost_df.index[-1], sim]
                perf_x = expx_perf_df.loc[expx_perf_df.index[-1], sim]
                fl_dfs[expx].loc[0, sim] = BaseSteadyStateFL.kernel(perf_x, plost_x)

        return fl_dfs


################################################################################
# Bivariate Classes
################################################################################


class SteadyStatePerfLostInteractiveSwarmBivar(BaseSteadyStatePerfLostInteractiveSwarm):
    """
    Bivariate calculator for the perforance lost per-robot for a swarm of size N of `interacting`
    robots, as oppopsed to a  swarm of size N of `non-interacting` robots. See
    :class:`~sierra.core.perf_measures.common.BaseSteadyStatePerfLostInteractiveSwarm` for a
    description of the mathematical calculations performed by this class.
    """
    @staticmethod
    def df_kernel(criteria: bc.BivarBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame],
                  collated_interference: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        populations = criteria.populations(cmdopts)
        plost_dfs = {}

        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.
        axis = sierra.core.utils.get_primary_axis(criteria,
                                                  [population_size.PopulationSize,
                                                   pcd.PopulationConstantDensity,
                                                   pvd.PopulationVariableDensity],
                                                  cmdopts)

        for i in range(0, xsize):
            for j in range(0, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_perf_df = collated_perf[expx]
                expx_interference_df = collated_interference[expx]
                plost_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                               index=[0])  # Steady state
                n_robots = populations[i][j]

                if axis == 0:
                    exp0_index = i
                else:
                    exp0_index = i * xsize

                exp0 = list(collated_perf.keys())[exp0_index]
                exp0_perf_df = collated_perf[exp0]
                exp0_interference_df = collated_interference[exp0]

                for sim in expx_perf_df.columns:
                    if (i * ysize + j) == exp0_index:  # exp0
                        plostN = 0.0  # By definition, no performance losses in exp0
                    else:
                        # steady state
                        tlost1 = exp0_interference_df.loc[exp0_interference_df.index[-1], sim]
                        perf1 = exp0_perf_df.loc[exp0_perf_df.index[-1], sim]  # steady state

                        # steady state
                        tlostN = expx_interference_df.loc[expx_interference_df.index[-1], sim]
                        perfN = expx_perf_df.loc[expx_perf_df.index[-1], sim]  # steady state

                        plostN = BaseSteadyStatePerfLostInteractiveSwarm.kernel(perf1=perf1,
                                                                                tlost1=tlost1,
                                                                                perfN=perfN,
                                                                                tlostN=tlostN,
                                                                                n_robots=n_robots)
                    plost_dfs[expx].loc[0, sim] = plostN

        return plost_dfs


class SteadyStateFLBivar(BaseSteadyStateFL):
    """
    Fractional losses calculation for bivariate batch criteria. See
    :class:`~sierra.core.perf_measures.common.BaseSteadyStateFL` for a description of the mathematical
    calculations performed by this class.

    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame],
                  collated_plost: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:

        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        fl_dfs = {}

        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.
        axis = sierra.core.utils.get_primary_axis(criteria,
                                                  [population_size.PopulationSize,
                                                   pcd.PopulationConstantDensity,
                                                   pvd.PopulationVariableDensity],
                                                  cmdopts)
        for i in range(0, xsize):
            for j in range(0, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_perf_df = collated_perf[expx]
                expx_plost_df = collated_plost[expx]
                fl_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state
                if axis == 0:
                    exp0_index = i
                else:
                    exp0_index = i * xsize

                for sim in expx_perf_df.columns:
                    if (i * ysize + j) == exp0_index:  # exp0
                        fl_x = 0.0  # By definition, no fractional losses in exp0
                    else:
                        perfN = expx_perf_df.loc[expx_perf_df.index[-1], sim]  # steady state
                        plostN = expx_plost_df.loc[expx_plost_df.index[-1], sim]  # steady state
                        fl_x = BaseSteadyStateFL.kernel(perfN, plostN)

                    fl_dfs[expx].loc[0, sim] = fl_x

        return fl_dfs


def gather_collated_sim_dfs(cmdopts: tp.Dict[str, tp.Any],
                            criteria: bc.IConcreteBatchCriteria,
                            perf_leaf: str,
                            perf_col: str) -> tp.Dict[str, pd.DataFrame]:
    exp_dirs = criteria.gen_exp_dirnames(cmdopts)
    dfs = {}
    for d in exp_dirs:
        perf_ipath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  d + '-' + perf_leaf + '-' + perf_col + '.csv')
        dfs[d] = sierra.core.utils.pd_csv_read(perf_ipath)
    return dfs


def univar_distribution_prepare(cmdopts: tp.Dict[str, tp.Any],
                                criteria: bc.IConcreteBatchCriteria,
                                oleaf: str,
                                pm_dfs: tp.Dict[str, pd.DataFrame],
                                exclude_exp0: bool) -> None:

    if cmdopts['dist_stats'] in ['conf95', 'all']:
        dist_dfs = sierra.core.stat_kernels.conf95.from_pm(pm_dfs)
        _univar_distribution_do_prepare(cmdopts, criteria, oleaf, dist_dfs, exclude_exp0)

    if cmdopts['dist_stats'] in ['bw', 'all']:
        dist_dfs = sierra.core.stat_kernels.bw.from_pm(pm_dfs)
        _univar_distribution_do_prepare(cmdopts, criteria, oleaf, dist_dfs, exclude_exp0)


def bivar_distribution_prepare(cmdopts: tp.Dict[str, tp.Any],
                               criteria: bc.IConcreteBatchCriteria,
                               oleaf: str,
                               pm_dfs: tp.Dict[str, pd.DataFrame],
                               exclude_exp0: bool,
                               axis: tp.Optional[int] = None) -> None:

    if cmdopts['dist_stats'] in ['conf95', 'all']:
        dist_dfs = sierra.core.stat_kernels.conf95.from_pm(pm_dfs)
        _bivar_distribution_do_prepare(cmdopts, criteria, oleaf, dist_dfs, exclude_exp0, axis)

    if cmdopts['dist_stats'] in ['bw', 'all']:
        dist_dfs = sierra.core.stat_kernels.bw.from_pm(pm_dfs)
        _bivar_distribution_do_prepare(cmdopts, criteria, oleaf, dist_dfs, exclude_exp0, axis)


def _univar_distribution_do_prepare(cmdopts: tp.Dict[str, tp.Any],
                                    criteria: bc.IConcreteBatchCriteria,
                                    oleaf: str,
                                    dist_dfs: tp.Dict[str, pd.DataFrame],
                                    exclude_exp0: bool) -> None:

    exp_dirs = criteria.gen_exp_dirnames(cmdopts)

    # For batch criteria only defined for exp > 0 for some graphs
    if exclude_exp0:
        exp_dirs = exp_dirs[1:]

    for stat in dist_dfs[list(dist_dfs.keys())[0]]:
        stat_opath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  oleaf + stat)
        df = pd.DataFrame(columns=exp_dirs, index=[0])
        for exp in exp_dirs:
            df.loc[0, exp] = dist_dfs[exp][stat]

        sierra.core.utils.pd_csv_write(df, stat_opath, index=False)


def _bivar_distribution_do_prepare(cmdopts: tp.Dict[str, tp.Any],
                                   criteria: bc.IConcreteBatchCriteria,
                                   oleaf: str,
                                   dist_dfs: tp.Dict[str, pd.DataFrame],
                                   exclude_exp0: bool,
                                   axis: tp.Optional[int] = None) -> None:

    exp_dirs = criteria.gen_exp_dirnames(cmdopts)

    xlabels, ylabels = sierra.core.utils.bivar_exp_labels_calc(exp_dirs)
    if exclude_exp0:
        xlabels = xlabels[axis == 0:]
        ylabels = ylabels[axis == 1:]

    for stat in dist_dfs[list(dist_dfs.keys())[0]]:
        stat_opath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  oleaf + stat)
        df = pd.DataFrame(columns=ylabels, index=xlabels)

        for exp in exp_dirs:
            xlabel, ylabel = exp.split('+')
            if xlabel in xlabels and ylabel in ylabels:
                df.iloc[xlabels.index(xlabel), ylabels.index(ylabel)] = dist_dfs[exp][stat]

        sierra.core.utils.pd_csv_write(df, stat_opath, index=False)


__api__ = [
    'BaseSteadyStatePerfLostInteractiveSwarm',
    'BaseSteadyStateFL',

    'SteadyStatePerfLostInteractiveSwarmUnivar',
    'SteadyStateFLUnivar',

    'SteadyStatePerfLostInteractiveSwarmBivar',
    'SteadyStateFLBivar',

]
