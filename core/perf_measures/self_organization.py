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


import os
import copy
import math
import logging
import pandas as pd

from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import common
from core.variables.population_size import PopulationSize


class SelfOrganizationFLUnivar:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to inter-robot interference.

    Only valid if the batch criteria was :class:`~variables.population_size.PopulationSize` derived.
    """

    def __init__(self, cmdopts, inter_perf_csv, ca_in_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.ca_in_csv = ca_in_csv

    def generate(self, batch_criteria):
        """
        Generates a :class:`~graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
        organization using :class:`perf_measures.common.FractionalLossesUnivar`, using the method
        defined in :xref:`Harwell2019`.
        """
        logging.info("Univariate FL self-organization from %s", self.cmdopts["collate_root"])
        batch_exp_dirnames = batch_criteria.gen_exp_dirnames(self.cmdopts)
        fl = common.FractionalLossesUnivar(self.cmdopts,
                                           self.inter_perf_csv,
                                           self.ca_in_csv,
                                           batch_criteria).calculate(batch_criteria)
        df_new = pd.DataFrame(columns=batch_exp_dirnames, index=[0])
        populations = batch_criteria.populations(self.cmdopts)

        # No self organization with 1 robot.
        df_new[df_new.columns[0]] = 0.0

        for i in range(1, len(fl.columns)):
            df_new.loc[0, batch_exp_dirnames[i]] = calc_harwell2019(fl[batch_exp_dirnames[i]],
                                                                    fl[batch_exp_dirnames[i - 1]],
                                                                    populations[i],
                                                                    populations[i - 1])

        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-self-org-fl")
        df_new.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-self-org-fl.png"),
                         title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xvals=batch_criteria.graph_xticks(self.cmdopts)).generate()


class SelfOrganizationFLBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to inter-robot interference.

    Only valid if one of the batch criteria was :class:`~variables.population_size.PopulationSize`
    derived.

    """

    def __init__(self, cmdopts, inter_perf_csv, ca_in_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.ca_in_csv = ca_in_csv

    def generate(self, batch_criteria):
        """
        Generates a :class:`~graphs.heatmap.Heatmap` across swarm sizes of self organization from
        :class:`~perf_measures.common.FractionalLossesBivar` data.

        The Harwell2019 method is only defined for one dimensional data, and we are dealing with 2D
        ``.csv`` files, so we project down the rows/across the columns as appropriate, depending on
        which axis in the ``.csv`` the :class:`~variables.population.Population` derived batch
        criteria is on.
        """

        logging.info("Bivariate FL self-organization from %s", self.cmdopts["collate_root"])
        fl = common.FractionalLossesBivar(self.cmdopts,
                                          self.inter_perf_csv,
                                          self.ca_in_csv,
                                          batch_criteria).calculate(batch_criteria)
        exp0_dir = fl.columns[0]
        so_df = pd.DataFrame(columns=[c for c in fl.columns if c not in exp0_dir],
                             index=fl.index)

        # We need to know which of the 2 variables was swarm size, in order to determine the correct
        # dimension along which to compute the metric, which depends on performance between adjacent
        # swarm sizes.
        if isinstance(batch_criteria.criteria1, PopulationSize):
            so_df = self.__calc_by_row(fl, batch_criteria)
        else:
            so_df = self.__calc_by_col(fl, batch_criteria)

        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-self-org-fl")
        so_df.to_csv(stem_path + ".csv", sep=';', index=False)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-self-org-fl.png"),
                title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calc_by_row(self, fl, batch_criteria):
        populations = batch_criteria.populations(self.cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        for i in range(0, len(fl.index)):
            for j in range(0, len(fl.columns)):
                # No self org possible with 1 robot
                if i == 0:
                    so_df.iloc[i, j] = 0
                    continue
                so_df.iloc[i, j] = calc_harwell2019(fl.iloc[i, j],
                                                    fl.iloc[i - 1, j],
                                                    populations[i][j],
                                                    populations[i - 1][j])

        return so_df

    def __calc_by_col(self, fl, batch_criteria):
        populations = batch_criteria.populations(self.cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        for i in range(0, len(fl.index)):
            for j in range(0, len(fl.columns)):
                # No self org possible with 1 robot
                if j == 0:
                    so_df.iloc[i, j] = 0
                    continue

                so_df.iloc[i, j] = calc_harwell2019(fl.iloc[i, j],
                                                    fl.iloc[i, j - 1],
                                                    populations[i][j],
                                                    populations[i][j - 1])
        return so_df


def calc_harwell2019(fl_x: float, fl_x1: float, n_robots_x: int, n_robots_x1: int):
    r"""
    Calculates the self organization for a particular swarm size N, given fractional performance
    losses for :math:`m_i` and a smaller swarm size :math:`m_{i-1}`. Equation taken from
    :xref:`Harwell2019`.

    .. math::
       \begin{equation}
       Z(m_i,\kappa) = \sum_{t\in{T}}1 - \frac{1}{1 + e^{-\theta_Z(m_i,\kappa,t)}}
       \end{equation}

    where

    .. math::
       \begin{equation}
       \theta_Z(m_i,\kappa,t) = P_{lost}(m_i,\kappa,t) - \frac{m_i}{m_{i-1}}{P_{lost}(m_{i-1},\kappa,t)}
       \end{equation}

    """
    theta = fl_x - float(n_robots_x) / float(n_robots_x1) * fl_x1
    return 1.0 - 1.0 / (1 + math.exp(-theta))
