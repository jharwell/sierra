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
import logging
import typing as tp

import pandas as pd

from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import common
from core.variables import batch_criteria as bc
from core.variables import population_size
from core.variables import population_density
import core.utils

################################################################################
# Univariate Classes
################################################################################


class FractionalLossesMarginalUnivar:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using marginal fractional
    performance losses due to inter-robot interference (See :func:`calc_self_org_mfl()`).

    Generates a :class:`~core.graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization using :class:`~core.perf_measures.common.FractionalLossesUnivar`.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-mfl"

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
            fl_i = fl[batch_exp_dirnames[i]].values[0]
            fl_iminus1 = fl[batch_exp_dirnames[i - 1]].values[0]
            n_robots_i = populations[i]
            n_robots_iminus1 = populations[i - 1]
            df_new.loc[0, batch_exp_dirnames[i]] = calc_self_org_mfl(fl_i=fl_i,
                                                                     fl_iminus1=fl_iminus1,
                                                                     n_robots_i=n_robots_i,
                                                                     n_robots_iminus1=n_robots_iminus1,
                                                                     normalize=self.cmdopts['pm_self_org_normalize'],
                                                                     normalize_method=self.cmdopts['pm_normalize_method'])

        stem_path = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        core.utils.pd_csv_write(df_new, stem_path + ".csv", index=False)

        BatchRangedGraph(input_fpath=stem_path + '.csv',
                         output_fpath=os.path.join(self.cmdopts["batch_collate_graph_root"],
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
    :func:`calc_self_org_ifl()`).

    Generates a :class:`~core.graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization using :class:`~core.perf_measures.common.FractionalLossesUnivar`.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-ifl"

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
            fl_i = fl[batch_exp_dirnames[i]].values[0]
            n_robots_i = populations[i]
            fl_1 = fl[batch_exp_dirnames[0]].values[0]
            df_new.loc[0, batch_exp_dirnames[i]] = calc_self_org_ifl(fl_i=fl_i,
                                                                     n_robots_i=n_robots_i,
                                                                     fl_1=fl_1,
                                                                     normalize=self.cmdopts['pm_self_org_normalize'],
                                                                     normalize_method=self.cmdopts['pm_normalize_method'])

        stem_path = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        core.utils.pd_csv_write(df_new, stem_path + ".csv", index=False)

        BatchRangedGraph(input_fpath=stem_path + '.csv',
                         output_fpath=os.path.join(self.cmdopts["batch_collate_graph_root"],
                                                   self.kLeaf + ".png"),
                         title="Swarm Self-Organization via Sub-Linear Performance Losses Through Interaction",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()


class PerformanceGainMarginalUnivar:
    r"""
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N`, :math:`2N`, a
    linear 2X increase in performance is expected, and more than this indicates emergent behavior).
    See :func:`calc_self_org_mpg()`).

    Generates a :class:`~core.graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-mpg"

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.IConcreteBatchCriteria):
        """
        Calculate marginal performance gain measure for th given controller for each experiment in a
        batch.

        Return:
          (Calculated metric dataframe, stddev dataframe) if stddev was collected.
          (Calculated metric datafram, None) otherwise.
        """
        sc_ipath = os.path.join(self.cmdopts["batch_collate_root"], self.inter_perf_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation
        if core.utils.path_exists(stddev_ipath):
            return (self.__calculate_measure(sc_ipath, batch_criteria),
                    self.__calculate_measure(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_measure(sc_ipath, batch_criteria), None)

    def generate(self,
                 dfs: tp.Tuple[pd.DataFrame, pd.DataFrame],
                 batch_criteria: bc.IConcreteBatchCriteria):

        cum_stem = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        metric_df = dfs[0]
        stddev_df = dfs[1]

        core.utils.pd_csv_write(metric_df, cum_stem + ".csv", index=False)
        if stddev_df is not None:
            core.utils.pd_csv_write(stddev_df, cum_stem + ".stddev", index=False)

        BatchRangedGraph(input_fpath=cum_stem + '.csv',
                         output_fpath=os.path.join(
                             self.cmdopts["batch_collate_graph_root"], self.kLeaf),
                         title="Swarm Self-Organization via Marginal Performance Gains",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()

    def __calculate_measure(self,
                            ipath: str,
                            batch_criteria: bc.UnivarBatchCriteria,
                            must_exist: bool = True):
        assert(not (must_exist and not core.utils.path_exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = core.utils.pd_csv_read(ipath)
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
                                                                 n_robots_iminus1=n_robots_iminus1,
                                                                 normalize=self.cmdopts['pm_self_org_normalize'],
                                                                 normalize_method=self.cmdopts['pm_normalize_method'])

        return eff_df


class PerformanceGainInteractiveUnivar:
    r"""
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between a swarm of :math:`N` interactive vs. independent robots.
    See :func:`calc_self_org_ipg()`).

    Generates a :class:`~core.graphs.batch_ranged_graph.BatchRangedGraph` across swarm sizes of self
    organization.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-ipg"

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
        sc_ipath = os.path.join(self.cmdopts["batch_collate_root"], self.inter_perf_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation
        if core.utils.path_exists(stddev_ipath):
            return (self.__calculate_measure(sc_ipath, batch_criteria),
                    self.__calculate_measure(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_measure(sc_ipath, batch_criteria), None)

    def generate(self,
                 dfs: tp.Tuple[pd.DataFrame, pd.DataFrame],
                 batch_criteria: bc.IConcreteBatchCriteria):

        cum_stem = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        metric_df = dfs[0]
        stddev_df = dfs[1]

        core.utils.pd_csv_write(metric_df, cum_stem + ".csv", index=False)
        if stddev_df is not None:
            core.utils.pd_csv_write(stddev_df, cum_stem + ".stddev", index=False)

        BatchRangedGraph(input_fpath=cum_stem + '.csv',
                         output_fpath=os.path.join(
                             self.cmdopts["batch_collate_graph_root"], self.kLeaf),
                         title="Swarm Self-Organization via Performance Gains Through Interaction",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()

    def __calculate_measure(self,
                            ipath: str,
                            batch_criteria: bc.UnivarBatchCriteria,
                            must_exist: bool = True):
        assert(not (must_exist and not core.utils.path_exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = core.utils.pd_csv_read(ipath)
        eff_df = pd.DataFrame(columns=raw_df.columns, index=[0])

        idx = raw_df.index[-1]
        populations = batch_criteria.populations(self.cmdopts)
        for i in range(0, len(eff_df.columns)):
            perf_i = raw_df.loc[idx, raw_df.columns[i]]
            perf_0 = raw_df.loc[idx, raw_df.columns[0]]
            n_robots_i = populations[i]
            eff_df.loc[0, eff_df.columns[i]] = calc_self_org_ipg(perf_i=perf_i,
                                                                 n_robots_i=n_robots_i,
                                                                 perf_0=perf_0,
                                                                 normalize=self.cmdopts['pm_self_org_normalize'],
                                                                 normalize_method=self.cmdopts['pm_normalize_method'])

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
                 batch_criteria: bc.IConcreteBatchCriteria):
        logging.info("Univariate self-organization from %s", cmdopts["batch_collate_root"])

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
                                    output_leaf='PM-self-org',
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
    losses due to inter-robot interference (See :meth:`calc_self_org_mfl`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` across swarm sizes of self organization from
    :class:`~core.perf_measures.common.FractionalLossesBivar` data.

    Assumptions:
        - exp0 has 1 robot.
        - One of the batch criteria was :class:`~core.variables.population_size.PopulationSize`
          derived.
    """
    kLeaf = "PM-self-org-mfl"

    def __init__(self, cmdopts, inter_perf_csv, interference_count_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv
        self.interference_count_csv = interference_count_csv

    def generate(self, batch_criteria: bc.IConcreteBatchCriteria):
        fl = common.FractionalLossesBivar(self.cmdopts,
                                          self.inter_perf_csv,
                                          self.interference_count_csv,
                                          batch_criteria).calculate(batch_criteria)
        exp0_dir = fl.columns[0]
        so_df = pd.DataFrame(columns=[c for c in fl.columns if c not in exp0_dir],
                             index=fl.index)

        so_df = self.__calc_measure(fl, batch_criteria)

        stem_path = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        core.utils.pd_csv_write(so_df, stem_path + ".csv", index=False)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["batch_collate_graph_root"],
                                          self.kLeaf + ".png"),
                title="Swarm Self-Organization via Marginal Sub-Linear Performance Losses",
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
                axis = core.utils.get_primary_axis(batch_criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   self.cmdopts)
                if axis == 0:
                    fl_iminus1 = fl.iloc[i - 1, j]
                    n_robots_iminus1 = populations[i - 1][j]
                else:
                    fl_iminus1 = fl.iloc[i, j - 1]
                    n_robots_iminus1 = populations[i][j - 1]

                so_df.iloc[i, j] = calc_self_org_mfl(fl_i=fl_i,
                                                     n_robots_i=n_robots_i,
                                                     fl_iminus1=fl_iminus1,
                                                     n_robots_iminus1=n_robots_iminus1,
                                                     normalize=self.cmdopts['pm_self_org_normalize'],
                                                     normalize_method=self.cmdopts['pm_normalize_method'])
        return so_df


class FractionalLossesInteractiveBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to interactive inter-robot interference vs independent action  (See
    :meth:`calc_self_org_ifl`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` across swarm sizes of self organization from
    :class:`~core.perf_measures.common.FractionalLossesBivar` data.

    Does not require one of the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-ifl"

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

        stem_path = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        core.utils.pd_csv_write(so_df, stem_path + ".csv", index=False)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(
                    self.cmdopts["batch_collate_graph_root"], self.kLeaf + ".png"),
                title="Swarm Self-Organization via Sub-Linear Performance Losses",
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
                axis = core.utils.get_primary_axis(batch_criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   self.cmdopts)
                if axis == 0:
                    fl_1 = fl.iloc[0, j]
                else:
                    fl_1 = fl.iloc[i, 0]

                so_df.iloc[i, j] = calc_self_org_ifl(fl_i=fl_i,
                                                     n_robots_i=n_robots_i,
                                                     fl_1=fl_1,
                                                     normalize=self.cmdopts['pm_self_org_normalize'],
                                                     normalize_method=self.cmdopts['pm_normalize_method'])
        return so_df


class PerformanceGainMarginalBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N`, :math:`2N`, a 2X
    increase in performance is expected, and more than this indicates emergent behavior).
    See :func:`calc_self_org_mpg()`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` across swarm sizes of self organization.

    Does not require one of the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-mpg"

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.IConcreteBatchCriteria):
        """
        Calculate marginal performance gain metric for the given controller for each experiment in a
        batch.

        Return:
          (Calculated metric dataframe, stddev dataframe) if stddev was collected
          (Calculated metric datafram, None) otherwise.
        """
        sc_ipath = os.path.join(self.cmdopts["batch_collate_root"], self.inter_perf_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation,
        if core.utils.path_exists(stddev_ipath):
            return (self.__calculate_measure(sc_ipath, batch_criteria),
                    self.__calculate_measure(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_measure(sc_ipath, batch_criteria), None)

    def generate(self,
                 dfs: tp.Tuple[pd.DataFrame, pd.DataFrame],
                 batch_criteria: bc.BivarBatchCriteria):
        cum_stem = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        metric_df, stddev_df = dfs

        core.utils.pd_csv_write(metric_df, cum_stem + ".csv", index=False)
        if stddev_df is not None:
            core.utils.pd_csv_write(stddev_df, cum_stem + ".stddev", index=False)

        Heatmap(input_fpath=cum_stem + '.csv',
                output_fpath=os.path.join(
                    self.cmdopts["batch_collate_graph_root"], self.kLeaf + ".png"),
                title="Swarm Self-Organization via Marginal Performance Gains",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calculate_measure(self,
                            ipath: str,
                            batch_criteria: bc.IConcreteBatchCriteria,
                            must_exist: bool = True):
        assert(not (must_exist and not core.utils.path_exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = core.utils.pd_csv_read(ipath)
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)

        populations = batch_criteria.populations(self.cmdopts)

        for i in range(0, len(raw_df.index)):
            for j in range(0, len(raw_df.columns)):
                # We need to know which of the 2 variables was swarm size, in order to determine
                # the correct dimension along which to compute the metric, which depends on
                # performance between adjacent swarm sizes.
                perf_i = common.csv_3D_value_iloc(raw_df,
                                                  i,
                                                  j,
                                                  slice(-1, None))
                n_robots_i = populations[i][j]

                axis = core.utils.get_primary_axis(batch_criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   self.cmdopts)
                if axis == 0:
                    perf_iminus1 = common.csv_3D_value_iloc(raw_df,
                                                            i - 1,
                                                            j,
                                                            slice(-1, None))
                    n_robots_iminus1 = populations[i - 1][j]
                else:
                    perf_iminus1 = common.csv_3D_value_iloc(raw_df,
                                                            i,
                                                            j - 1,
                                                            slice(-1, None))
                    n_robots_iminus1 = populations[i][j - 1]

                eff_df.iloc[i, j] = calc_self_org_mpg(perf_i=perf_i,
                                                      n_robots_i=n_robots_i,
                                                      perf_iminus1=perf_iminus1,
                                                      n_robots_iminus1=n_robots_iminus1,
                                                      normalize=self.cmdopts['pm_self_org_normalize'],
                                                      normalize_method=self.cmdopts['pm_normalize_method'])

        return eff_df


class PerformanceGainInteractiveBivar:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between a swarm of :math:`N` interacting vs. indpendently acting robots.
    See :func:`calc_self_org_ipg()`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` across swarm sizes of self organization.

    Does not require one of the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-ipg"

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def calculate(self, batch_criteria: bc.IConcreteBatchCriteria):
        """
        Calculate marginal performance gain metric for the given controller for each experiment in a
        batch.

        Return:
          (Calculated metric dataframe, stddev dataframe) if stddev was collected
          (Calculated metric datafram, None) otherwise.
        """
        sc_ipath = os.path.join(self.cmdopts["batch_collate_root"], self.inter_perf_stem + '.csv')
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')

        # Metric calculation is the same for the actual value of it and the std deviation,
        if core.utils.path_exists(stddev_ipath):
            return (self.__calculate_measure(sc_ipath, batch_criteria),
                    self.__calculate_measure(stddev_ipath, batch_criteria, False))
        else:
            return (self.__calculate_measure(sc_ipath, batch_criteria), None)

    def generate(self,
                 dfs: tp.Tuple[pd.DataFrame, pd.DataFrame],
                 batch_criteria: bc.BivarBatchCriteria):
        cum_stem = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf)
        metric_df, stddev_df = dfs

        core.utils.pd_csv_write(metric_df, cum_stem + ".csv", index=False)
        if stddev_df is not None:
            core.utils.pd_csv_write(stddev_df, cum_stem + ".stddev", index=False)

        Heatmap(input_fpath=cum_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["batch_collate_graph_root"],
                                          self.kLeaf + ".png"),
                title="Swarm Self-Organization via Performance Gains Through Interaction",
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    def __calculate_measure(self,
                            ipath: str,
                            batch_criteria: bc.BivarBatchCriteria,
                            must_exist: bool = True):
        assert(not (must_exist and not core.utils.path_exists(ipath))
               ), "FATAL: {0} does not exist".format(ipath)
        raw_df = core.utils.pd_csv_read(ipath)
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)

        populations = batch_criteria.populations(self.cmdopts)

        for i in range(0, len(raw_df.index)):
            for j in range(0, len(raw_df.columns)):
                # We need to know which of the 2 variables was swarm size, in order to determine
                # the correct dimension along which to compute the metric, which depends on
                # performance between adjacent swarm sizes.
                perf_i = common.csv_3D_value_iloc(raw_df,
                                                  i,
                                                  j,
                                                  slice(-1, None))
                n_robots_i = populations[i][j]

                axis = core.utils.get_primary_axis(batch_criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   self.cmdopts)
                if axis == 0:
                    perf_0 = common.csv_3D_value_iloc(raw_df,
                                                      0,
                                                      j,
                                                      slice(-1, None))
                else:
                    perf_0 = common.csv_3D_value_iloc(raw_df,
                                                      i,
                                                      0,
                                                      slice(-1, None))

                eff_df.iloc[i, j] = calc_self_org_ipg(perf_i=perf_i,
                                                      n_robots_i=n_robots_i,
                                                      perf_0=perf_0,
                                                      normalize=self.cmdopts['pm_self_org_normalize'],
                                                      normalize_method=self.cmdopts['pm_normalize_method'])

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
                 batch_criteria: bc.IConcreteBatchCriteria):
        logging.info("Bivariate self-organization from %s", cmdopts["batch_collate_root"])

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


def calc_self_org_ifl(fl_i: float,
                      n_robots_i: int,
                      fl_1: float,
                      normalize: bool,
                      normalize_method: str):
    r"""
    Calculates the self organization due to inter-robot interaction for a swarm configuration of
    size :math:`N`, using scaled fractional performance losses in comparison to a non-interactive
    swarm of size :math:`N`.

    .. math::
       E_S(N,\kappa) = \sum_{t\in{T}}\theta_{E_S}(N,\kappa)

    or

    .. math::
       E_S(N,\kappa) = \sum_{t\in{T}}\frac{1}{1 + e^{-\theta_{E_S}(t)}} - \frac{1}{1 + e^{\theta_{E_S}(t)}}

    where

    .. math::
       \theta_{E_S}(t) = {N}{P_{lost}(1,\kappa,t)} - P_{lost}(N,\kappa,t)

    depending on normalization configuration.

    Inspired by :xref:`Harwell2019`.

    """

    scaled_fl_1 = float(n_robots_i) * fl_1
    theta = scaled_fl_1 - fl_i

    if normalize:
        if normalize_method == 'sigmoid':
            return core.utils.Sigmoid(theta)() - core.utils.Sigmoid(-theta)()
        else:
            return None
    else:
        return theta


def calc_self_org_mfl(fl_i: float,
                      n_robots_i: int,
                      fl_iminus1: float,
                      n_robots_iminus1: int,
                      normalize: bool,
                      normalize_method: str):
    r"""
    Calculates the self organization due to inter-robot interaction for a  swarm configuration of
    size :math:`N_2`, given fractional performance losses for :math:`N_2` robots and for a
    smaller swarm of size :math:`N_1` with the same configuration.

    .. math::
       E_S(N_1,N_2,\kappa) = \sum_{t\in{T}}\theta_{E_S}(t)

    or

    .. math::
       E_S(N_1,N_2,\kappa) = \sum_{t\in{T}}\frac{1}{1 + e^{-\theta_{E_S}(t)}} - \frac{1}{1 + e^{\theta_{E_S}(t)}}

    where

    .. math::
       \theta_{E_S}(t) = \frac{N_2}{N_1}{P_{lost}(N_1,\kappa,t)} - P_{lost}(N_2,\kappa,t)

    depending on normalization configuration.

    Defined for swarms with :math:`N_1` > 1 robots. For :math:`N_1=1`, we obtain a :math:`\theta`
    value using L'Hospital's rule and taking the derivative with respect to :math:`N_1`.

    Original equation taken from :xref:`Harwell2019`, modified to have better theoretical limits.

    """
    if n_robots_i > 1:
        theta = float(n_robots_i) / float(n_robots_iminus1) * fl_iminus1 - fl_i
    else:
        theta = 0.0

    if normalize:
        if normalize_method == 'sigmoid':
            return core.utils.Sigmoid(theta)() - core.utils.Sigmoid(-theta)()
        else:
            return None
    else:
        return theta


def calc_self_org_mpg(perf_i: float,
                      n_robots_i: int,
                      perf_iminus1: float,
                      n_robots_iminus1: int,
                      normalize: bool,
                      normalize_method: str):
    r"""
    Calculates the marginal performance gains achieved by the swarm configuration of size
    :math:`N_2`, given the performance achieved with :math:`N_2` robots and with a smaller swarm
    size :math:`N_1` with the same configuration.

    .. math::
       E_T(N_1,N_2,\kappa) = \sum_{t\in{T}} \theta_{E_T}(t)

    or

    .. math::
       E_T(N_1,N_2,\kappa) = \sum_{t\in{T}} \frac{1}{1 + e^{-\theta_{E_T}(t)}} - \frac{1}{1 + e^{\theta_{E_T}(t)}}

    where

    .. math::
       \theta_{E_T}(t) = P(N_2,\kappa,t) - \frac{N_2}{N_1}{P(N_1,\kappa,t)}

    depending on normalization configuration.

    Defined for swarms with :math:`N_1` > 1 robots. For :math:`N_1=1`, we obtain a
    :math:`\theta` value using L'Hospital's rule and taking the derivative with respect to
    :math:`N_1`.

    Inspired by :xref:`Rosenfeld2006`.

    """
    if n_robots_i > 1:
        theta = perf_i - (float(n_robots_i) / float(n_robots_iminus1)) * perf_iminus1
    else:
        theta = 0.0

    if normalize:
        if normalize_method == 'sigmoid':
            return core.utils.Sigmoid(theta)() - core.utils.Sigmoid(-theta)()
        else:
            return None
    else:
        return theta


def calc_self_org_ipg(perf_i: float,
                      n_robots_i: int,
                      perf_0: float,
                      normalize: bool,
                      normalize_method: str):
    r"""
    Calculates the self organization due to inter-robot interaction for a swarm configuration of
    size :math:`N`, given the performance achieved with a single robot with the same configuration.

    .. math::
       E_T(N,\kappa) = \sum_{t\in{T}} \theta_{E_T}(t)

    or

    .. math::
       E_T(N,\kappa) = \sum_{t\in{T}} \frac{1}{1 + e^{-\theta_{E_T}(t)}} - \frac{1}{1 + e^{\theta_{E_T}(t)}}

    where

    .. math::
       \theta_{E_T}(t) =  P(N,\kappa,t} - {N}{P(1,\kappa,t)}

    depending on normalization configuration.

    Inspired by :xref:`Rosenfeld2006`.

    """
    theta = perf_i - n_robots_i * perf_0

    if normalize:
        if normalize_method == 'sigmoid':
            return core.utils.Sigmoid(theta)() - core.utils.Sigmoid(-theta)()
        else:
            return None
    else:
        return theta


__api__ = [
    'FractionalLossesMarginalUnivar',
    'FractionalLossesInteractiveUnivar',
    'PerformanceGainMarginalUnivar',
    'PerformanceGainInteractiveUnivar',
    'FractionalLossesMarginalBivar',
    'FractionalLossesInteractiveBivar',
    'PerformanceGainMarginalBivar',
    'PerformanceGainInteractiveBivar',
    'calc_self_org_ifl',
    'calc_self_org_mfl',
    'calc_self_org_mpg',
    'calc_self_org_ipg'
]
