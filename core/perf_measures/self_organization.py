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

kNO_SELF_ORG = 0.0

################################################################################
# Univariate Classes
################################################################################


class FractionalLossesMarginalUnivar:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using marginal fractional
    performance losses due to inter-robot interference (See :func:`calc_self_org_mfl`).

    Generates a :class:`~graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization using :class:`perf_measures.common.FractionalLossesUnivar`.

    Assumptions:
        - exp0 has 1 robot.
        - The batch criteria was :class:`~variables.population_size.PopulationSize` derived.
    """
    kLeaf = "pm-self-org-mfl"

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

        df_new[batch_exp_dirnames[0]] = kNO_SELF_ORG

        for i in range(1, len(fl.columns)):
            fl_i = fl[batch_exp_dirnames[i]].values[0]
            fl_iminus1 = fl[batch_exp_dirnames[i - 1]].values[0]
            n_robots_i = populations[i]
            n_robots_iminus1 = populations[i - 1]
            df_new.loc[0, batch_exp_dirnames[i]] = calc_self_org_mfl(fl_i=fl_i,
                                                                     fl_iminus1=fl_iminus1,
                                                                     n_robots_i=n_robots_i,
                                                                     n_robots_iminus1=n_robots_iminus1)

        stem_path = os.path.join(self.cmdopts["collate_root"], self.kLeaf)
        df_new.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   self.kLeaf + ".png"),
                         title="Swarm Self-Organization via Marginal Sub-Linear Performance Losses",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()


class FractionalLossesInteractiveUnivar:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional
    performance losses due to interative inter-robot interference vs. independent action (See
    :func:`calc_self_org_ifl`).

    Generates a :class:`~graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization using :class:`perf_measures.common.FractionalLossesUnivar`.

    Assumptions:
        - exp0 has 1 robot.
        - The batch criteria was :class:`~variables.population_size.PopulationSize` derived.
    """
    kLeaf = "pm-self-org-ifl"

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

        df_new[batch_exp_dirnames[0]] = kNO_SELF_ORG
        for i in range(1, len(fl.columns)):
            fl_i = fl[batch_exp_dirnames[i]].values[0]
            n_robots_i = populations[i]
            fl_1 = fl[batch_exp_dirnames[0]].values[0]
            df_new.loc[0, batch_exp_dirnames[i]] = calc_self_org_ifl(fl_i=fl_i,
                                                                     n_robots_i=n_robots_i,
                                                                     fl_1=fl_1)

        stem_path = os.path.join(self.cmdopts["collate_root"], self.kLeaf)
        df_new.to_csv(stem_path + ".csv", sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_path,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   self.kLeaf + ".png"),
                         title="Swarm Self-Organization via Sub-Linear Performance Losses Through Interaction",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()


class PerformanceGainMarginalUnivar:
    r"""
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N` :math:`2N`, a 2X
    increase in performance is expected, and more than this indicates emergent behavior).
    See :func:`calc_self_org_mpg`).

    Generates a :class:`~graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization.

    Assumptions:
        - exp0 has 1 robot.
        - The batch criteria was :class:`~variables.population_size.PopulationSize` derived.

    """
    kLeaf = "pm-self-org-mpg"

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
                         title="Swarm Self-Organization via Marginal Performance Gains",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
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
            eff_df.loc[0, eff_df.columns[i]] = calc_self_org_mpg(perf_i=perf_i,
                                                                 n_robots_i=n_robots_i,
                                                                 perf_iminus1=perf_iminus1,
                                                                 n_robots_iminus1=n_robots_iminus1)

        return eff_df


class PerformanceGainInteractiveUnivar:
    r"""
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between a swarm of :math:`N` interactive vs. independent robots.
    See :func:`calc_self_org_ipg`).

    Generates a :class:`~graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization.

    Assumptions:
        - exp0 has 1 robot.
        - The batch criteria was :class:`~variables.population_size.PopulationSize` derived.

    """
    kLeaf = "pm-self-org-ipg"

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.UnivarBatchCriteria):
        """
        Calculate interactive performance gain measure for th given controller for each experiment
        in a batch.

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
                         title="Swarm Self-Organization via Performance Gains Through Interaction",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
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
            perf_0 = raw_df.loc[idx, raw_df.columns[0]]
            n_robots_i = populations[i]
            eff_df.loc[0, eff_df.columns[i]] = calc_self_org_ipg(perf_i=perf_i,
                                                                 n_robots_i=n_robots_i,
                                                                 perf_0=perf_0)

        return eff_df


class SelfOrgUnivarGenerator:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def __call__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 alpha_S: float,
                 alpha_T: float,
                 batch_criteria: bc.UnivarBatchCriteria):
        logging.info("Univariate self-organization from %s", cmdopts["collate_root"])

        mfl = FractionalLossesMarginalUnivar(cmdopts, inter_perf_csv, interference_count_csv)
        mfl.generate(batch_criteria)

        ifl = FractionalLossesInteractiveUnivar(cmdopts, inter_perf_csv, interference_count_csv)
        ifl.generate(batch_criteria)

        mpg = PerformanceGainMarginalUnivar(cmdopts, inter_perf_csv)
        mpg.generate(mpg.calculate(batch_criteria), batch_criteria)

        ipg = PerformanceGainInteractiveUnivar(cmdopts, inter_perf_csv)
        ipg.generate(ipg.calculate(batch_criteria), batch_criteria)

        title1 = 'Swarm Emergent-Self Organization '
        title2 = r'($\alpha_{{E_S}}={0},\alpha_{{E_T}}={1}$)'.format(alpha_S, alpha_T)
        w = common.WeightedPMUnivar(cmdopts=cmdopts,
                                    output_leaf='pm-self-org',
                                    ax1_leaf=FractionalLossesInteractiveBivar.kLeaf,
                                    ax2_leaf=PerformanceGainMarginalBivar.kLeaf,
                                    ax1_alpha=alpha_S,
                                    ax2_alpha=alpha_T,
                                    title=title1 + title2)
        w.generate(batch_criteria)

################################################################################
# Bivariate Classes
################################################################################


class FractionalLossesMarginalBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to inter-robot interference  (See :meth:`calc_self_org_mfl`).

    Generates a :class:`~graphs.heatmap.Heatmap` across swarm sizes of self organization from
    :class:`~perf_measures.common.FractionalLossesBivar` data.

    Assumptions:
        - exp0 has 1 robot.
        - One of the batch criteria was :class:`~variables.population_size.PopulationSize` derived.
    """
    kLeaf = "pm-self-org-mfl"

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
                title="Swarm Self-Organization via Marginal Sub-Linear Performance Losses",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calc_measure(self, fl, batch_criteria):
        populations = batch_criteria.populations(self.cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        xfactor = 0
        yfactor = 0
        if isinstance(batch_criteria.criteria1, ps.PopulationSize) or self.cmdopts['plot_primary_axis'] == '0':
            so_df.iloc[:, 0] = kNO_SELF_ORG
            xfactor = 1
        else:
            so_df.iloc[0, :] = kNO_SELF_ORG
            yfactor = 1

        for i in range(xfactor, len(fl.index)):
            for j in range(yfactor, len(fl.columns)):
                fl_i = fl.iloc[i][j]
                n_robots_i = populations[i][j]

                # We need to know which of the 2 variables was swarm size, in order to determine the
                # correct dimension along which to compute the metric, which depends on performance
                # between adjacent swarm sizes.
                if isinstance(batch_criteria.criteria1, ps.PopulationSize) or self.cmdopts['plot_primary_axis'] == '0':
                    fl_iminus1 = fl.iloc[i - 1, j]
                    n_robots_iminus1 = populations[i - 1][j]
                else:
                    fl_iminus1 = fl.iloc[i, j - 1]
                    n_robots_iminus1 = populations[i][j - 1]

                so_df.iloc[i, j] = calc_self_org_mfl(fl_i=fl_i,
                                                     n_robots_i=n_robots_i,
                                                     fl_iminus1=fl_iminus1,
                                                     n_robots_iminus1=n_robots_iminus1)
        return so_df


class FractionalLossesInteractiveBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to interactive inter-robot interference vs independent action  (See
    :meth:`calc_self_org_ifl`).

    Generates a :class:`~graphs.heatmap.Heatmap` across swarm sizes of self organization from
    :class:`~perf_measures.common.FractionalLossesBivar` data.

    Assumptions:
        - exp0 has 1 robot.
        - One of the batch criteria was :class:`~variables.population_size.PopulationSize` derived.
    """
    kLeaf = "pm-self-org-ifl"

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
                title="Swarm Self-Organization via Sub-Linear Performance Losses",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calc_measure(self, fl, batch_criteria):
        populations = batch_criteria.populations(self.cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        xfactor = 0
        yfactor = 0
        if isinstance(batch_criteria.criteria1, ps.PopulationSize) or self.cmdopts['plot_primary_axis'] == '0':
            so_df.iloc[:, 0] = kNO_SELF_ORG
            xfactor = 1
        else:
            so_df.iloc[0, :] = kNO_SELF_ORG
            yfactor = 1

        for i in range(xfactor, len(fl.index)):
            for j in range(yfactor, len(fl.columns)):
                fl_i = fl.iloc[i][j]
                n_robots_i = populations[i][j]

                # We need to know which of the 2 variables was swarm size, in order to determine the
                # correct dimension along which to compute the metric, which depends on performance
                # between adjacent swarm sizes.
                if isinstance(batch_criteria.criteria1, ps.PopulationSize) or self.cmdopts['plot_primary_axis'] == '0':
                    fl_1 = fl.iloc[0, j]
                else:
                    fl_1 = fl.iloc[i, 0]

                so_df.iloc[i, j] = calc_self_org_ifl(fl_i=fl_i,
                                                     n_robots_i=n_robots_i,
                                                     fl_1=fl_1)
        return so_df


class PerformanceGainMarginalBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N` :math:`2N`, a 2X
    increase in performance is expected, and more than this indicates emergent behavior).
    See :func:`calc_self_org_mpg`).

    Generates a :class:`~graphs.heatmap.Heatmap` across swarm sizes of self organization.

    Assumptions:
        - exp0 has 1 robot.
        - One of the batch criteria was :class:`~variables.population_size.PopulationSize` derived.
    """
    kLeaf = "pm-self-org-mpg"

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
        cum_stem = os.path.join(self.cmdopts["collate_root"], self.kLeaf)
        metric_df, stddev_df = dfs

        metric_df.to_csv(cum_stem + ".csv", sep=';', index=False)
        if stddev_df is not None:
            stddev_df.to_csv(cum_stem + ".stddev", sep=';', index=False)

        Heatmap(input_fpath=cum_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], self.kLeaf + ".png"),
                title="Swarm Self-Organization via Marginal Performance Gains",
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

                if isinstance(batch_criteria.criteria1, ps.PopulationSize) or self.cmdopts['plot_primary_axis'] == '0':
                    perf_iminus1 = raw_df[i - 1][j]
                    n_robots_iminus1 = populations[i - 1][j]
                else:
                    perf_iminus1 = raw_df[i][j - 1]
                    n_robots_iminus1 = populations[i][j - 1]

                eff_df.iloc = calc_self_org_mpg(perf_i, n_robots_i, perf_iminus1, n_robots_iminus1)

        return eff_df


class PerformanceGainInteractiveBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between a swarm of :math:`N` interacting vs. indpendently acting robots.
    See :func:`calc_self_org_ipg`).

    Generates a :class:`~graphs.heatmap.Heatmap` across swarm sizes of self organization.

    Assumptions:
        - exp0 has 1 robot.
        - One of the batch criteria was :class:`~variables.population_size.PopulationSize` derived.
    """
    kLeaf = "pm-self-org-ipg"

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
        cum_stem = os.path.join(self.cmdopts["collate_root"], self.kLeaf)
        metric_df, stddev_df = dfs

        metric_df.to_csv(cum_stem + ".csv", sep=';', index=False)
        if stddev_df is not None:
            stddev_df.to_csv(cum_stem + ".stddev", sep=';', index=False)

        Heatmap(input_fpath=cum_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], self.kLeaf + ".png"),
                title="Swarm Self-Organization via Performance Gains Through Interaction",
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

                if isinstance(batch_criteria.criteria1, ps.PopulationSize) or self.cmdopts['plot_primary_axis'] == '0':
                    perf_0 = raw_df[0][j]
                else:
                    perf_0 = raw_df[i][0]

                eff_df.iloc = calc_self_org_ipg(perf_i=perf_i,
                                                n_robots_i=n_robots_i,
                                                perf_0=perf_0)

        return eff_df


class SelfOrgBivarGenerator:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in various ways.
    """

    def __call__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 alpha_S: float,
                 alpha_T: float,
                 batch_criteria: bc.BivarBatchCriteria):
        logging.info("Bivariate self-organization from %s", cmdopts["collate_root"])

        mfl = FractionalLossesMarginalBivar(cmdopts, inter_perf_csv, interference_count_csv)
        mfl.generate(batch_criteria)

        ifl = FractionalLossesInteractiveBivar(cmdopts, inter_perf_csv, interference_count_csv)
        ifl.generate(batch_criteria)

        mpg = PerformanceGainMarginalBivar(cmdopts, inter_perf_csv)
        mpg.generate(mpg.calculate(batch_criteria), batch_criteria)

        ipg = PerformanceGainInteractiveBivar(cmdopts, inter_perf_csv)
        ipg.generate(ipg.calculate(batch_criteria), batch_criteria)

        title1 = 'Swarm Emergent-Self Organization '
        title2 = r'($\alpha_{{E_S}}={0},\alpha_{{E_T}}={1}$)'.format(alpha_S, alpha_T)
        w = common.WeightedPMBivar(cmdopts=cmdopts,
                                   output_leaf='pm-self-org',
                                   ax1_leaf=FractionalLossesInteractiveBivar.kLeaf,
                                   ax2_leaf=PerformanceGainMarginalBivar.kLeaf,
                                   ax1_alpha=alpha_S,
                                   ax2_alpha=alpha_T,
                                   title=title1 + title2)
        w.generate(batch_criteria)


################################################################################
# Calculation Functions
################################################################################


def calc_self_org_ifl(fl_i: float, n_robots_i: int, fl_1: float):
    r"""
    Calculates the self organization due to inter-robot interaction for a swarm configuration of
    size :math:`N`, using scaled fractional performance losses in comparison to a non-interactive
    swarm of size :math:`N`.

    .. math::
       \begin{equation}
       Z(N,\kappa) = \sum_{t\in{T}}\frac{1}{1 + e^{-\theta_Z(N,\kappa,t)}} - {1 + e^{\theta_Z(N,\kappa,t)}}
       \end{equation}

    where

    .. math::
       \begin{equation}
       \theta_Z(N,\kappa,t) = {N}{P_{lost}(1,\kappa,t)} - P_{lost}(N,\kappa,t)
       \end{equation}

    Inspired by :xref:`Harwell2019`.

    """

    scaled_fl_1 = float(n_robots_i) * fl_1
    theta = scaled_fl_1 - fl_i

    return 1.0 / (1 + math.exp(-theta)) - 1.0 / (1 + math.exp(theta))


def calc_self_org_mfl(fl_i: float, n_robots_i: int, fl_iminus1: float, n_robots_iminus1: int):
    r"""
    Calculates the self organization due to inter-robot interaction for a  swarm configuration of
    size :math:`m_{i}`, given fractional performance losses for :math:`m_{i}` robots and for a
    smaller swarm of size :math:`m_{i-1}` with the same configuration.

    .. math::
       \begin{equation}
       Z(m_i,\kappa) = \sum_{t\in{T}}\frac{1}{1 + e^{-\theta_Z(m_i,\kappa,t)}} - {1 + e^{\theta_Z(m_i,\kappa,t)}}
       \end{equation}

    where

    .. math::
       \begin{equation}
       \theta_Z(m_i,\kappa,t) = \frac{m_{i}}{m_{i-1}}{P_{lost}(m_{i-1},\kappa,t)} - P_{lost}(m_{i},\kappa,t)
       \end{equation}

    Defined for swarms with :math:`N` > 1 robots. For :math:`N=1`, we obtain a :math:`\theta` value
    using L'Hospital's rule and taking the derivative with respect to :math:`m_{i-1}`.

    Original equation taken from :xref:`Harwell2019`, modified to have better theoretical limits.

    """
    if n_robots_i > 1:
        theta = float(n_robots_i) / float(n_robots_iminus1) * fl_iminus1 - fl_i
        return 1.0 / (1 + math.exp(-theta)) - 1.0 / (1 + math.exp(theta))
    else:
        return 0.0


def calc_self_org_mpg(perf_i: float, n_robots_i: int, perf_iminus1: float, n_robots_iminus1: int):
    r"""
    Calculates the marginal performance gains achieved by the swarm configuration of size
    :math:`m_i`, given the performance achieved with :math:`m_i` robots and with a smaller swarm
    size :math:`m_{i-1}` with the same configuration.

    .. math::
       \begin{equation}
       Z(m_i,\kappa) = \sum_{t\in{T}}\frac{1}{1 + e^{-\theta_Z(m_i,\kappa,t)}} - \frac{1}{1 + e^{\theta_Z(m_i,\kappa,t)}}
       \end{equation}

    .. math::
       \begi{equation}
       theta = P(m_i,\kappa,t) - \frac{m_i}{m_{i-1}}{P(m_{i-1},\kappa,t)}
       \end{equation}

    Defined for swarms with :math:`m_{i-1}` > 1 robots. For :math:`m_{i-1}=1`, we obtain a
    :math:`\theta` value using L'Hospital's rule and taking the derivative with respect to
    :math:`m_i{i-1}`.

    Inspired by :xref:`Rosenfield2006`.

    """
    if n_robots_i > 1:
        theta = perf_i - (float(n_robots_i) / float(n_robots_iminus1)) * perf_iminus1
        return 1.0 / (1 + math.exp(-theta)) - 1.0 / (1 + math.exp(theta))
    else:
        return 0.0


def calc_self_org_ipg(perf_i: float, n_robots_i: int, perf_0: float):
    r"""
    Calculates the self organization due to inter-robot interaction for a swarm configuration of
    size :math:`N`, given the performance achieved with a single robot with the same configuration.

    .. math::
       \begin{equation}
       Z(N,\kappa) = \sum_{t\in{T}}\frac{1}{1 + e^{-\theta_Z(N,\kappa,t)}} - \frac{1}{1 + e^{\theta_Z(N,\kappa,t)}}
       \end{equation}

    .. math::
       \begin{equation}
       theta_Z(N,\kappa,t) =  P(N,\kappa,t} - {N}{P(1,\kappa,t)}
       \end{equation}

    Inspired by :xref:`Rosenfield2006`.

    """
    theta = perf_i - n_robots_i * perf_0

    return 1.0 / (1 + math.exp(-theta)) - 1.0 / (1 + math.exp(theta))


__api__ = [
    'FractionalLossesMarginalUnivar',
    'FractionalLossesInteractiveUnivar',
    'PerformanceGainMarginalUnivar',
    'PerformanceGainInteractiveUnivar',
    'WeightedSelfOrgUnivar',
    'FractionalLossesMarginalBivar',
    'FractionalLossesInteractiveBivar',
    'PerformanceGainMarginalBivar',
    'PerformanceGainInteractiveBivar',
    'WeightedSelfOrgBivar'
]
