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
Measures for swarm self-organization/emergence in univariate and bivariate batched experiments.
"""


import os
import copy
import math
import logging
import typing as tp

import pandas as pd

from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import common
from core.variables import batch_criteria as bc
from core.variables import population_size as ps

################################################################################
# Univariate Classes
################################################################################


class FractionalLossesUnivar:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractppional performance
    losses due to inter-robot interference (See :func:`calc_self_org_fl`).

    Generates a :class:`~graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization using :class:`perf_measures.common.FractionalLossesUnivar`.

    Only valid if the batch criteria was :class:`~variables.population_size.PopulationSize` derived.
    """
    kLeaf = "pm-self-org-fl"

    def __init__(self, cmdopts, inter_perf_csv, interference_count_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.interference_count_csv = interference_count_csv

    def generate(self, batch_criteria):
        batch_exp_dirnames = batch_criteria.gen_exp_dirnames(self.cmdopts)
        fl = common.FractionalLossesUnivar(self.cmdopts,
                                           self.inter_perf_csv,
                                           self.interference_count_csv,
                                           batch_criteria).calculate(batch_criteria)
        df_new = pd.DataFrame(columns=batch_exp_dirnames, index=[0])
        populations = batch_criteria.populations(self.cmdopts)

        for i in range(0, len(fl.columns)):
            df_new.loc[0, batch_exp_dirnames[i]] = calc_self_org_fl(fl[batch_exp_dirnames[i]],
                                                                    fl[batch_exp_dirnames[i - 1]],
                                                                    populations[i],
                                                                    populations[i - 1])

        stem_path = os.path.join(self.cmdopts["collate_root"], self.kLeaf)
        df_new.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   self.kLeaf + ".png"),
                         title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()


class MarginalPerformanceGainUnivar:
    r"""
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N` :math:`2N`, a 2X
    increase in performance is expected, and more than this indicates emergent behavior).
    See :func:`calc_self_org_mpg`).

    Generates a :class:`~graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization.

    Only valid if one of the batch criteria was :class:`~variables.population_size.PopulationSize`
    derived.

    """
    kLeaf = "pm-marginal-perf-gain"

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.UnivarBatchCriteria):
        """
        Calculate marginal performance gain measure for th given controller for each experiment in a
        batch.

        Return:
          (Calculated metric dataframe, stddev dataframe) if stddev was collected.
          (Calculated metric datafram, None) otherwise.
        """
        sc_ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.inter_perf_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation
        if os.path.exists(stddev_ipath):
            return (self.__calculate_measure(sc_ipath, batch_criteria),
                    self.__calculate_measure(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_measure(sc_ipath, batch_criteria), None)

    def generate(self,
                 dfs: tp.Tuple[pd.DataFrame, pd.DataFrame],
                 batch_criteria: bc.UnivarBatchCriteria):

        cum_stem = os.path.join(self.cmdopts["collate_root"], self.kLeaf)
        metric_df = dfs[0]
        stddev_df = dfs[1]

        metric_df.to_csv(cum_stem + ".csv", sep=';', index=False)
        if stddev_df is not None:
            stddev_df.to_csv(cum_stem + ".stddev", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=cum_stem,
                         output_fpath=os.path.join(self.cmdopts["graph_root"], self.kLeaf),
                         title="Swarm Marginal Performance Gain",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Marginal Performance Gain",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()

    def __calculate_measure(self,
                            ipath: str,
                            batch_criteria: bc.UnivarBatchCriteria,
                            must_exist: bool = True):
        assert(not (must_exist and not os.path.exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = pd.read_csv(ipath, sep=';')
        eff_df = pd.DataFrame(columns=raw_df.columns, index=[0])

        idx = raw_df.index[-1]
        populations = batch_criteria.populations(self.cmdopts)

        for i in range(0, len(eff_df.columns)):
            perf_i = raw_df.loc[idx, raw_df.columns[i]]
            perf_iminus1 = raw_df.loc[idx, raw_df.columns[i - 1]]
            n_robots_i = populations[i]
            n_robots_iminus1 = populations[i - 1]
            eff_df.loc[0, eff_df.columns[i]] = calc_self_org_mpg(perf_i,
                                                                 n_robots_i,
                                                                 perf_iminus1,
                                                                 n_robots_iminus1)

        return eff_df


class SelfOrgUnivarGenerator:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def __call__(self,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 cmdopts: dict,
                 batch_criteria: bc.UnivarBatchCriteria):
        logging.info("Univariate self-organization from %s", cmdopts["collate_root"])

        fl = FractionalLossesUnivar(cmdopts, inter_perf_csv, interference_count_csv)
        fl.generate(batch_criteria)

        p = MarginalPerformanceGainUnivar(cmdopts, inter_perf_csv)
        p.generate(p.calculate(batch_criteria), batch_criteria)

################################################################################
# Bivariate Classes
################################################################################


class FractionalLossesBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to inter-robot interference  (See :meth:`calc_self_org_fl`).

    Generates a :class:`~graphs.heatmap.Heatmap` across swarm sizes of self organization from
    :class:`~perf_measures.common.FractionalLossesBivar` data.

    Only valid if one of the batch criteria was :class:`~variables.population_size.PopulationSize`
    derived.
    """
    kLeaf = "pm-self-org-fl"

    def __init__(self, cmdopts, inter_perf_csv, interference_count_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.interference_count_csv = interference_count_csv

    def generate(self, batch_criteria):
        fl = common.FractionalLossesBivar(self.cmdopts,
                                          self.inter_perf_csv,
                                          self.interference_count_csv,
                                          batch_criteria).calculate(batch_criteria)
        exp0_dir = fl.columns[0]
        so_df = pd.DataFrame(columns=[c for c in fl.columns if c not in exp0_dir],
                             index=fl.index)

        so_df = self.__calc_measure(fl, batch_criteria)

        stem_path = os.path.join(self.cmdopts["collate_root"], self.kLeaf)
        so_df.to_csv(stem_path + ".csv", sep=';', index=False)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], self.kLeaf + ".png"),
                title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calc_measure(self, fl, batch_criteria):
        populations = batch_criteria.populations(self.cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        for i in range(0, len(fl.index)):
            for j in range(0, len(fl.columns)):
                fl_i = fl.iloc[i][j]
                n_robots_i = populations[i][j]

                # We need to know which of the 2 variables was swarm size, in order to determine the
                # correct dimension along which to compute the metric, which depends on performance
                # between adjacent swarm sizes.
                if isinstance(batch_criteria.criteria1, ps.PopulationSize):
                    fl_iminus1 = fl.iloc[i, j - 1]
                    n_robots_iminus1 = populations[i][j - 1]
                else:
                    fl_iminus1 = fl.iloc[i - 1, j]
                    n_robots_iminus1 = populations[i - 1][j]

                so_df.iloc[i, j] = calc_self_org_fl(fl_i,
                                                    n_robots_i,
                                                    fl_iminus1,
                                                    n_robots_iminus1)
        return so_df


class MarginalPerformanceGainBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N` :math:`2N`, a 2X
    increase in performance is expected, and more than this indicates emergent behavior).
    See :func:`calc_self_org_mpg`).

    Generates a :class:`~graphs.heatmap.Heatmap` across swarm sizes of self organization.

    Only valid if one of the batch criteria was :class:`~variables.population_size.PopulationSize`
    derived.
    """
    kLeaf = "pm-marginal-perf-gain"

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.BivarBatchCriteria):
        """
        Calculate marginal performance gain metric for the given controller for each experiment in a
        batch.

        Return:
          (Calculated metric dataframe, stddev dataframe) if stddev was collected
          (Calculated metric datafram, None) otherwise.
        """
        sc_ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.inter_perf_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation,
        if os.path.exists(stddev_ipath):
            return (self.__calculate_measure(sc_ipath, batch_criteria),
                    self.__calculate_measure(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_measure(sc_ipath, batch_criteria), None)

    def generate(self,
                 dfs: tp.Tuple[pd.DataFrame, pd.DataFrame],
                 batch_criteria: bc.BivarBatchCriteria):
        logging.info("Bivariate MPG self-organization from %s", self.cmdopts["collate_root"])

        cum_stem = os.path.join(self.cmdopts["collate_root"], self.kLeaf)
        metric_df, stddev_df = dfs

        metric_df.to_csv(cum_stem + ".csv", sep=';', index=False)
        if stddev_df is not None:
            stddev_df.to_csv(cum_stem + ".stddev", sep=';', index=False)

        Heatmap(input_fpath=cum_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], self.kLeaf + ".png"),
                title='Swarm Marginal Performance Gains',
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calculate_measure(self,
                            ipath: str,
                            batch_criteria: bc.BivarBatchCriteria,
                            must_exist: bool = True):
        assert(not (must_exist and not os.path.exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = pd.read_csv(ipath, sep=';')
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)

        populations = batch_criteria.populations(self.cmdopts)

        for i in range(0, len(raw_df.index)):
            for j in range(0, len(raw_df.columns)):
                # We need to know which of the 2 variables was swarm size, in order to determine
                # the correct dimension along which to compute the metric, which depends on
                # performance between adjacent swarm sizes.
                perf_i = raw_df[i][j]
                n_robots_i = populations[i][j]

                if isinstance(batch_criteria.criteria1, ps.PopulationSize):
                    perf_iminus1 = raw_df[i][j - 1]
                    n_robots_iminus1 = populations[i][j - 1]
                else:
                    perf_iminus1 = raw_df[i - 1][j]
                    n_robots_iminus1 = populations[i - 1][j]

                eff_df.iloc = calc_self_org_mpg(perf_i, n_robots_i, perf_iminus1, n_robots_iminus1)

        return eff_df


class SelfOrgBivarGenerator:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def __call__(self,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 cmdopts: dict,
                 batch_criteria: bc.BivarBatchCriteria):
        logging.info("Bivariate self-organization from %s", cmdopts["collate_root"])

        fl = FractionalLossesBivar(cmdopts, inter_perf_csv, interference_count_csv)
        fl.generate(batch_criteria)

        p = MarginalPerformanceGainBivar(cmdopts, inter_perf_csv)
        p.generate(p.calculate(batch_criteria), batch_criteria)


################################################################################
# Calculation Functions
################################################################################

def calc_self_org_fl(fl_i: float, n_robots_i: int, fl_iminus1: float, n_robots_iminus1: int):
    r"""
    Calculates the self organization for a particular swarm configuration of size :math:`m_i`, given
    fractional performance losses for :math:`m_i` and a smaller swarm size :math:`m_{i-1}`. Equation
    taken from :xref:`Harwell2019`.

    .. math::
       \begin{equation}
       Z(m_i,\kappa) = \sum_{t\in{T}}1 - \frac{1}{1 + e^{-\theta_Z(m_i,\kappa,t)}}
       \end{equation}

    where

    .. math::
       \begin{equation}
       \theta_Z(m_i,\kappa,t) = P_{lost}(m_i,\kappa,t) - \frac{m_i}{m_{i-1}}{P_{lost}(m_{i-1},\kappa,t)}
       \end{equation}

    Defined for swarms with :math:`N` > 1 robots. For :math:`N=1`, we obtain a :math:`\theta` value
    of :math:`-P_{lost}(m_{i-1},\kappa,t)` using L'Hospital's rule and taking the derivative with
    respect to :math:`N`.
    """

    if n_robots_iminus1 > 0:
        theta = fl_i - float(n_robots_i) / float(n_robots_iminus1) * fl_iminus1
    else:
        theta = - fl_iminus1

    return 1.0 - 1.0 / (1 + math.exp(-theta))


def calc_self_org_mpg(perf_i: float, n_robots_i: int, perf_iminus1: float, n_robots_iminus1: int):
    r"""
    Calculates the marginal performance gains achieved by the swarm configuration of size
    :math:`m_i`, given the performance achieved with :math:`m_i` robots and with a smaller swarm
    size :math:`m_{i-1}`.

    .. math::
       \begin{equation}
       Z(m_i,\kappa) = \sum_{t\in{T}}1 - \frac{1}{1 + e^{-\theta_Z(m_i,\kappa,t)}}
       \end{equation}

    .. math::
       \begin{equation}
       theta = \frac{m_i}{m_{i-1}} - \frac{P(m_i,\kappa,t}{P(m_{i-1},\kappa,t)}
       \end{equation}

    Defined for swarms with :math:`N` > 1 robots. For :math:`N=1`, we obtain a :math:`\theta` value
    of -1.0 using L'Hospital's rule and taking the derivative with respect to :math:`N`.

    Inspired by :xref:`Rosenfield2006`.

    """
    if n_robots_iminus1 > 0:
        theta = (perf_i / perf_iminus1) - (float(n_robots_i) / float(n_robots_iminus1))
    else:
        theta = -1.0

    return 1.0 - 1.0 / (1 + math.exp(-theta))
