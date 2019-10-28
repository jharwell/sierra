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
import pandas as pd
import logging
from graphs.batch_ranged_graph import BatchRangedGraph
from graphs.heatmap import Heatmap
import perf_measures.common as common
import math
from variables.swarm_size import SwarmSize


class SelfOrganizationUnivar:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data.

    """

    def __init__(self, cmdopts, inter_perf_csv, ca_in_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.ca_in_csv = ca_in_csv

    def generate(self, batch_criteria):
        logging.info("Univariate self-organization from {0}".format(self.cmdopts["collate_root"]))
        batch_exp_dirnames = batch_criteria.gen_exp_dirnames(self.cmdopts)
        fl = common.FractionalLossesUnivar(self.cmdopts,
                                           self.inter_perf_csv,
                                           self.ca_in_csv,
                                           batch_criteria).calculate(batch_criteria)
        df_new = pd.DataFrame(columns=batch_exp_dirnames, index=[0])
        swarm_sizes = batch_criteria.swarm_sizes(self.cmdopts)

        # No self organization with 1 robot.
        df_new[df_new.columns[0]] = 0.0

        for i in range(1, len(fl.columns)):
            theta = fl[batch_exp_dirnames[i]] - \
                float(swarm_sizes[i]) / float(swarm_sizes[i - 1]) * fl[batch_exp_dirnames[i - 1]]
            df_new.loc[0, batch_exp_dirnames[i]] = 1.0 - 1.0 / math.exp(-theta)

        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-self-org")
        df_new.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-self-org.png"),
                         title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xvals=batch_criteria.graph_xticks(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()


class SelfOrganizationBivar:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data as follows:

    Self org = fl (N_i)  - * N_i / N_{i-1} * fl )N_{i-1}

    """

    def __init__(self, cmdopts, inter_perf_csv, ca_in_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.ca_in_csv = ca_in_csv

    def generate(self, batch_criteria):
        logging.info("Bivariate self-organization from {0}".format(self.cmdopts["collate_root"]))
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
        if isinstance(batch_criteria.criteria1, SwarmSize):
            so_df = self.__calc_by_row(fl, batch_criteria)
        else:
            so_df = self.__calc_by_col(fl, batch_criteria)

        stem_path = os.path.join(self.cmdopts["collate_root"], "pm-self-org")
        so_df.to_csv(stem_path + ".csv", sep=';', index=False)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-self-org.png"),
                title="Swarm Self-Organization Due To Sub-Linear Fractional Performance Losses",
                xlabel=batch_criteria.graph_ylabel(self.cmdopts),
                ylabel=batch_criteria.graph_xlabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_yticks(self.cmdopts),
                ytick_labels=batch_criteria.graph_xticks(self.cmdopts)).generate()

    def __calc_by_row(self, fl, batch_criteria):
        swarm_sizes = batch_criteria.swarm_sizes(self.cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        for i in range(0, len(fl.index)):
            for j in range(0, len(fl.columns)):
                # No self org possible with 1 robot
                if 0 == i:
                    so_df.iloc[i, j] = 0
                    continue
                n_robots_i = swarm_sizes[i][j]
                n_robots_i1 = swarm_sizes[i - 1][j]

                theta = fl.iloc[i, j] - float(n_robots_i) / float(n_robots_i1) * \
                    fl.iloc[i - 1, j]
                so_df.iloc[i, j] = 1.0 - 1.0 / math.exp(-theta)

        return so_df

    def __calc_by_col(self, fl, batch_criteria):
        swarm_sizes = batch_criteria.swarm_sizes(self.cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        for i in range(0, len(fl.index)):
            for j in range(0, len(fl.columns)):
                # No self org possible with 1 robot
                if 0 == j:
                    so_df.iloc[i, j] = 0
                    continue

                n_robots_j = swarm_sizes[i][j]
                n_robots_j1 = swarm_sizes[i][j - 1]

                theta = fl.iloc[i, j] - float(n_robots_j) / float(n_robots_j1) * \
                    fl.iloc[i, j - 1]
                so_df.iloc[i, j] = 1.0 - 1.0 / math.exp(-theta)
        return so_df
