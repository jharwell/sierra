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


# Core packages
import os
import copy
import logging

# 3rd party packages
import pandas as pd

# Project packages
from core.graphs.summary_line_graph import SummaryLinegraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import common
from core.variables import batch_criteria as bc
from core.variables import population_size
from core.variables import population_density
import core.utils
import core.config

################################################################################
# Base Classes
################################################################################


class BaseFLMarginal():
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
    @staticmethod
    def kernel(fl_i: float,
               n_robots_i: int,
               fl_iminus1: float,
               n_robots_iminus1: int,
               normalize: bool,
               normalize_method: str):

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


class BaseFLInteractive():
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
    @staticmethod
    def kernel(fl_i: float,
               n_robots_i: int,
               fl_1: float,
               normalize: bool,
               normalize_method: str):
        scaled_fl_1 = float(n_robots_i) * fl_1
        theta = scaled_fl_1 - fl_i

        if normalize:
            if normalize_method == 'sigmoid':
                return core.utils.Sigmoid(theta)() - core.utils.Sigmoid(-theta)()
            else:
                return None
        else:
            return theta


class BasePGMarginal():
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
    @staticmethod
    def kernel(perf_i: float,
               n_robots_i: int,
               perf_iminus1: float,
               n_robots_iminus1: int,
               normalize: bool,
               normalize_method: str):
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


class BasePGInteractive():
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
    @staticmethod
    def kernel(perf_i: float,
               n_robots_i: int,
               perf_0: float,
               normalize: bool,
               normalize_method: str):
        theta = perf_i - n_robots_i * perf_0

        if normalize:
            if normalize_method == 'sigmoid':
                return core.utils.Sigmoid(theta)() - core.utils.Sigmoid(-theta)()
            else:
                return None
        else:
            return theta

################################################################################
# Univariate Classes
################################################################################


class FLMarginalUnivar(BaseFLMarginal):
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using marginal fractional
    performance losses due to inter-robot interference (See :class:`BaseFLMarginal`).

    Generates a :class:`~core.graphs.summary_line_graph.SummaryLinegraph` across swarm sizes of self
    organization using :class:`~core.perf_measures.common.FractionalLossesUnivar`.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-mfl"

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  fl: pd.DataFrame) -> pd.DataFrame:
        batch_exp_dirnames = criteria.gen_exp_dirnames(cmdopts)
        populations = criteria.populations(cmdopts)
        df_new = pd.DataFrame(columns=batch_exp_dirnames, index=[0])

        for i in range(0, len(fl.columns)):
            fl_i = fl[batch_exp_dirnames[i]].values[0]
            fl_iminus1 = fl[batch_exp_dirnames[i - 1]].values[0]
            n_robots_i = populations[i]
            n_robots_iminus1 = populations[i - 1]
            df_new.loc[0, batch_exp_dirnames[i]] = BaseFLMarginal.kernel(fl_i=fl_i,
                                                                         fl_iminus1=fl_iminus1,
                                                                         n_robots_i=n_robots_i,
                                                                         n_robots_iminus1=n_robots_iminus1,
                                                                         normalize=cmdopts['pm_self_org_normalize'],
                                                                         normalize_method=cmdopts['pm_normalize_method'])
        return df_new

    def __init__(self, cmdopts, inter_perf_csv, interference_count_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]
        self.interference_count_leaf = interference_count_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self._stats_prepare(criteria)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],
                         title="Swarm Self-Organization via Marginal Sub-Linear Performance Losses",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()

    def _stats_prepare(self, criteria: bc.IConcreteBatchCriteria) -> None:
        for k in core.config.kStatsExtensions.keys():
            perf_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.inter_perf_leaf + core.config.kStatsExtensions[k])
            int_count_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                           self.interference_count_leaf + core.config.kStatsExtensions[k])
            stat_opath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.kLeaf + core.config.kStatsExtensions[k])

            if core.utils.path_exists(perf_ipath):
                perf_stats = core.utils.pd_csv_read(perf_ipath)
                interference = core.utils.pd_csv_read(int_count_ipath)
                plostN = common.PerfLostInteractiveSwarmUnivar.df_kernel(criteria,
                                                                         self.cmdopts,
                                                                         interference,
                                                                         perf_stats)
                fl = common.FractionalLossesUnivar.df_kernel(perf_stats, plostN)
                odf = self.df_kernel(criteria, self.cmdopts, fl)
                core.utils.pd_csv_write(odf, stat_opath, index=False)


class FLInteractiveUnivar(BaseFLInteractive):
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional
    performance losses due to interative inter-robot interference vs. independent action (See
    :class:`BaseFLInteractive`).

    Generates a :class:`~core.graphs.summary_line_graph.SummaryLinegraph` across swarm sizes of self
    organization using :class:`~core.perf_measures.common.FractionalLossesUnivar`.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-ifl"

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  fl: pd.DataFrame) -> pd.DataFrame:
        batch_exp_dirnames = criteria.gen_exp_dirnames(cmdopts)
        populations = criteria.populations(cmdopts)
        df_new = pd.DataFrame(columns=batch_exp_dirnames, index=[0])

        for i in range(0, len(fl.columns)):
            fl_i = fl[batch_exp_dirnames[i]].values[0]
            n_robots_i = populations[i]
            fl_1 = fl[batch_exp_dirnames[0]].values[0]
            df_new.loc[0, batch_exp_dirnames[i]] = BaseFLInteractive.kernel(fl_i=fl_i,
                                                                            n_robots_i=n_robots_i,
                                                                            fl_1=fl_1,
                                                                            normalize=cmdopts['pm_self_org_normalize'],
                                                                            normalize_method=cmdopts['pm_normalize_method'])
        return df_new

    def __init__(self, cmdopts, inter_perf_csv, interference_count_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]
        self.interference_count_leaf = interference_count_csv.split('.')[0]

    def from_batch(self, criteria):
        self._stats_prepare(criteria)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],
                         title="Swarm Self-Organization via Sub-Linear Performance Losses Through Interaction",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()

    def _stats_prepare(self, criteria: bc.IConcreteBatchCriteria) -> None:
        for k in core.config.kStatsExtensions.keys():
            perf_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.inter_perf_leaf + core.config.kStatsExtensions[k])
            int_count_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                           self.interference_count_leaf + core.config.kStatsExtensions[k])
            stat_opath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.kLeaf + core.config.kStatsExtensions[k])

            if core.utils.path_exists(perf_ipath):
                perf_stats = core.utils.pd_csv_read(perf_ipath)
                interference = core.utils.pd_csv_read(int_count_ipath)
                plostN = common.PerfLostInteractiveSwarmUnivar.df_kernel(criteria,
                                                                         self.cmdopts,
                                                                         interference,
                                                                         perf_stats)
                fl = common.FractionalLossesUnivar.df_kernel(perf_stats, plostN)
                odf = self.df_kernel(criteria, self.cmdopts, fl)
                core.utils.pd_csv_write(odf, stat_opath, index=False)


class PGMarginalUnivar(BasePGMarginal):
    r"""
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N`, :math:`2N`, a
    linear 2X increase in performance is expected, and more than this indicates emergent behavior).

    Generates a :class:`~core.graphs.summary_line_graph.SummaryLinegraph` across swarm sizes of self
    organization.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-mpg"

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  raw_df: pd.DataFrame) -> pd.DataFrame:
        eff_df = pd.DataFrame(columns=raw_df.columns, index=[0])

        idx = raw_df.index[-1]
        populations = criteria.populations(cmdopts)

        for i in range(0, len(eff_df.columns)):
            perf_i = raw_df.loc[idx, raw_df.columns[i]]
            perf_iminus1 = raw_df.loc[idx, raw_df.columns[i - 1]]
            n_robots_i = populations[i]
            n_robots_iminus1 = populations[i - 1]
            eff_df.loc[0, eff_df.columns[i]] = BasePGMarginal.kernel(perf_i=perf_i,
                                                                     n_robots_i=n_robots_i,
                                                                     perf_iminus1=perf_iminus1,
                                                                     n_robots_iminus1=n_robots_iminus1,
                                                                     normalize=cmdopts['pm_self_org_normalize'],
                                                                     normalize_method=cmdopts['pm_normalize_method'])

        return eff_df

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate marginal performance gain measure for the given controller for each experiment in
        a batch.
        """
        common.stats_prepare(self.cmdopts,
                             criteria,
                             self.inter_perf_leaf,
                             self.kLeaf,
                             self.df_kernel)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],
                         title="Swarm Self-Organization via Marginal Performance Gains",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class PGInteractiveUnivar(BasePGInteractive):
    r"""
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between a swarm of :math:`N` interactive vs. independent robots.
    See :class:`BasePGInteractive`.

    Generates a :class:`~core.graphs.summary_line_graph.SummaryLinegraph` across swarm sizes of self
    organization.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-ipg"

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  raw_df: pd.DataFrame) -> pd.DataFrame:
        eff_df = pd.DataFrame(columns=raw_df.columns, index=[0])

        idx = raw_df.index[-1]
        populations = criteria.populations(cmdopts)
        for i in range(0, len(eff_df.columns)):
            perf_i = raw_df.loc[idx, raw_df.columns[i]]
            perf_0 = raw_df.loc[idx, raw_df.columns[0]]
            n_robots_i = populations[i]
            eff_df.loc[0, eff_df.columns[i]] = BasePGInteractive.kernel(perf_i=perf_i,
                                                                        n_robots_i=n_robots_i,
                                                                        perf_0=perf_0,
                                                                        normalize=cmdopts['pm_self_org_normalize'],
                                                                        normalize_method=cmdopts['pm_normalize_method'])

        return eff_df

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate marginal performance gain measure for the given controller for each experiment in
        a batch.
        """
        common.stats_prepare(self.cmdopts,
                             criteria,
                             self.inter_perf_leaf,
                             self.kLeaf,
                             self.df_kernel)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],

                         title="Swarm Self-Organization via Performance Gains Through Interaction",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="Value",
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class SelfOrgUnivarGenerator:
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv datain various ways.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 alpha_S: float,
                 alpha_T: float,
                 criteria: bc.IConcreteBatchCriteria):
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        FLMarginalUnivar(cmdopts, inter_perf_csv, interference_count_csv).from_batch(criteria)
        FLInteractiveUnivar(cmdopts, inter_perf_csv, interference_count_csv).from_batch(criteria)
        PGMarginalUnivar(cmdopts, inter_perf_csv).from_batch(criteria)
        PGInteractiveUnivar(cmdopts, inter_perf_csv).from_batch(criteria)

        title1 = 'Swarm Emergent-Self Organization '
        title2 = r'($\alpha_{{E_S}}={0},\alpha_{{E_T}}={1}$)'.format(alpha_S, alpha_T)
        w = common.WeightedPMUnivar(cmdopts=cmdopts,
                                    output_leaf='PM-self-org',
                                    ax1_leaf=FLInteractiveBivar.kLeaf,
                                    ax2_leaf=PGMarginalBivar.kLeaf,
                                    ax1_alpha=alpha_S,
                                    ax2_alpha=alpha_T,
                                    title=title1 + title2)
        w.generate(criteria)

################################################################################
# Bivariate Classes
################################################################################


class FLMarginalBivar(BaseFLMarginal):
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to inter-robot interference (See :class:`BaseFLMarginal`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` across swarm sizes of self organization from
    :class:`~core.perf_measures.common.FractionalLossesBivar` data.

    Assumptions:
        - exp0 has 1 robot.
        - One of the batch criteria was :class:`~core.variables.population_size.PopulationSize`
          derived.
    """
    kLeaf = "PM-self-org-mfl"

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  fl: pd.DataFrame) -> pd.DataFrame:
        populations = criteria.populations(cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        for i in range(0, len(fl.index)):
            for j in range(0, len(fl.columns)):
                fl_i = fl.iloc[i][j]
                n_robots_i = populations[i][j]

                # We need to know which of the 2 variables was swarm size, in order to determine the
                # correct dimension along which to compute the metric, which depends on performance
                # between adjacent swarm sizes.
                axis = core.utils.get_primary_axis(criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   cmdopts)
                if axis == 0:
                    fl_iminus1 = fl.iloc[i - 1, j]
                    n_robots_iminus1 = populations[i - 1][j]
                else:
                    fl_iminus1 = fl.iloc[i, j - 1]
                    n_robots_iminus1 = populations[i][j - 1]

                so_df.iloc[i, j] = BaseFLMarginal.kernel(fl_i=fl_i,
                                                         n_robots_i=n_robots_i,
                                                         fl_iminus1=fl_iminus1,
                                                         n_robots_iminus1=n_robots_iminus1,
                                                         normalize=cmdopts['pm_self_org_normalize'],
                                                         normalize_method=cmdopts['pm_normalize_method'])
        return so_df

    def __init__(self, cmdopts, inter_perf_csv, interference_count_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]
        self.interference_count_leaf = interference_count_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self._stats_prepare(criteria)
        stem_path = os.path.join(self.cmdopts["batch_stat_collate_root"], self.kLeaf)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                          self.kLeaf + core.config.kImageExt),
                title="Swarm Self-Organization via Marginal Sub-Linear Performance Losses",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()

    def _stats_prepare(self, criteria: bc.IConcreteBatchCriteria) -> None:
        for k in core.config.kStatsExtensions.keys():
            perf_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.inter_perf_leaf + core.config.kStatsExtensions[k])
            int_count_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                           self.interference_count_leaf + core.config.kStatsExtensions[k])
            stat_opath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.kLeaf + core.config.kStatsExtensions[k])

            if core.utils.path_exists(perf_ipath):
                perf_stats = core.utils.pd_csv_read(perf_ipath)
                interference = core.utils.pd_csv_read(int_count_ipath)
                plostN = common.PerfLostInteractiveSwarmBivar.df_kernel(criteria,
                                                                        self.cmdopts,
                                                                        interference,
                                                                        perf_stats)
                fl = common.FractionalLossesBivar.df_kernel(perf_stats, plostN)
                odf = self.df_kernel(criteria, self.cmdopts, fl)
                core.utils.pd_csv_write(odf, stat_opath, index=False)


class FLInteractiveBivar(BaseFLInteractive):
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to interactive inter-robot interference vs independent action  (See
    :class:`BaseFLInteractive`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` across swarm sizes of self organization from
    :class:`~core.perf_measures.common.FractionalLossesBivar` data.

    Does not require one of the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-ifl"

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  fl: pd.DataFrame) -> pd.DataFrame:
        populations = criteria.populations(cmdopts)
        so_df = pd.DataFrame(columns=fl.columns, index=fl.index)

        for i in range(0, len(fl.index)):
            for j in range(0, len(fl.columns)):
                fl_i = fl.iloc[i][j]
                n_robots_i = populations[i][j]

                # We need to know which of the 2 variables was swarm size, in order to determine the
                # correct dimension along which to compute the metric, which depends on performance
                # between adjacent swarm sizes.
                axis = core.utils.get_primary_axis(criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   cmdopts)
                if axis == 0:
                    fl_1 = fl.iloc[0, j]
                else:
                    fl_1 = fl.iloc[i, 0]

                so_df.iloc[i, j] = BaseFLInteractive.kernel(fl_i=fl_i,
                                                            n_robots_i=n_robots_i,
                                                            fl_1=fl_1,
                                                            normalize=cmdopts['pm_self_org_normalize'],
                                                            normalize_method=cmdopts['pm_normalize_method'])
        return so_df

    def __init__(self, cmdopts, inter_perf_csv, interference_count_csv) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]
        self.interference_count_leaf = interference_count_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria):
        self._stats_prepare(criteria)
        stem_path = os.path.join(self.cmdopts["batch_stat_collate_root"], self.kLeaf)

        Heatmap(input_fpath=stem_path + '.csv',
                output_fpath=os.path.join(
                    self.cmdopts["batch_graph_collate_root"], self.kLeaf + core.config.kImageExt),
                title="Swarm Self-Organization via Sub-Linear Performance Losses",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()

    def _stats_prepare(self, criteria: bc.IConcreteBatchCriteria) -> None:
        for k in core.config.kStatsExtensions.keys():
            perf_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.inter_perf_leaf + core.config.kStatsExtensions[k])
            int_count_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                           self.interference_count_leaf + core.config.kStatsExtensions[k])
            stat_opath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.kLeaf + core.config.kStatsExtensions[k])

            if core.utils.path_exists(perf_ipath):
                perf_stats = core.utils.pd_csv_read(perf_ipath)
                interference = core.utils.pd_csv_read(int_count_ipath)
                plostN = common.PerfLostInteractiveSwarmBivar.df_kernel(criteria,
                                                                        self.cmdopts,
                                                                        interference,
                                                                        perf_stats)
                fl = common.FractionalLossesBivar.df_kernel(perf_stats, plostN)
                odf = self.df_kernel(criteria, self.cmdopts, fl)
                core.utils.pd_csv_write(odf, stat_opath, index=False)


class PGMarginalBivar(BasePGMarginal):
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N`, :math:`2N`, a 2X
    increase in performance is expected, and more than this indicates emergent behavior).
    See :class:`BasePGMarginal`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` across swarm sizes of self organization.

    Does not require one of the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-mpg"

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  raw_df: pd.DataFrame) -> pd.DataFrame:
        eff_df = pd.DataFrame(columns=raw_df.columns,
                              index=raw_df.index)

        populations = criteria.populations(cmdopts)

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

                axis = core.utils.get_primary_axis(criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   cmdopts)
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

                eff_df.iloc[i, j] = BasePGMarginal.kernel(perf_i=perf_i,
                                                          n_robots_i=n_robots_i,
                                                          perf_iminus1=perf_iminus1,
                                                          n_robots_iminus1=n_robots_iminus1,
                                                          normalize=cmdopts['pm_self_org_normalize'],
                                                          normalize_method=cmdopts['pm_normalize_method'])

        return eff_df

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate marginal performance gain metric for the given controller for each experiment in a
        batch.
        """
        common.stats_prepare(self.cmdopts,
                             criteria,
                             self.inter_perf_leaf,
                             self.kLeaf,
                             self.df_kernel)

        so_opath = os.path.join(self.cmdopts["batch_stat_collate_root"], self.kLeaf)

        Heatmap(input_fpath=so_opath + '.csv',
                output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                          self.kLeaf + core.config.kImageExt),
                title="Swarm Self-Organization via Marginal Performance Gains",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


class PGInteractiveBivar(BasePGInteractive):
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between a swarm of :math:`N` interacting vs. indpendently acting robots.
    See :class:`BasePGInteractive`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` across swarm sizes of self organization.

    Does not require one of the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    Does not require exp0 to have 1 robot, but the calculation will be more meaningful if that is
    the case.
    """
    kLeaf = "PM-self-org-ipg"

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: dict,
                  raw_df: pd.DataFrame) -> pd.DataFrame:
        eff_df = pd.DataFrame(columns=raw_df.columns, index=raw_df.index)

        populations = criteria.populations(cmdopts)

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

                axis = core.utils.get_primary_axis(criteria,
                                                   [population_size.PopulationSize,
                                                    population_density.PopulationConstantDensity],
                                                   cmdopts)
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

                eff_df.iloc[i, j] = BasePGInteractive.kernel(perf_i=perf_i,
                                                             n_robots_i=n_robots_i,
                                                             perf_0=perf_0,
                                                             normalize=cmdopts['pm_self_org_normalize'],
                                                             normalize_method=cmdopts['pm_normalize_method'])

        return eff_df

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate marginal performance gain metric for the given controller for each experiment in a
        batch.
        """
        common.stats_prepare(self.cmdopts,
                             criteria,
                             self.inter_perf_leaf,
                             self.kLeaf,
                             self.df_kernel)

        so_opath = os.path.join(self.cmdopts["batch_stat_collate_root"], self.kLeaf)

        Heatmap(input_fpath=so_opath + '.csv',
                output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                          self.kLeaf + core.config.kImageExt),
                title="Swarm Self-Organization via Performance Gains Through Interaction",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


class SelfOrgBivarGenerator:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in various ways.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str,
                 alpha_S: float,
                 alpha_T: float,
                 criteria: bc.IConcreteBatchCriteria):
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        FLMarginalBivar(cmdopts, inter_perf_csv, interference_count_csv).from_batch(criteria)
        FLInteractiveBivar(cmdopts, inter_perf_csv, interference_count_csv).from_batch(criteria)
        PGMarginalBivar(cmdopts, inter_perf_csv).from_batch(criteria)
        PGInteractiveBivar(cmdopts, inter_perf_csv).from_batch(criteria)

        title1 = 'Swarm Emergent-Self Organization '
        title2 = r'($\alpha_{{E_S}}={0},\alpha_{{E_T}}={1}$)'.format(alpha_S, alpha_T)
        w = common.WeightedPMBivar(cmdopts=cmdopts,
                                   output_leaf='pm-self-org',
                                   ax1_leaf=FLInteractiveBivar.kLeaf,
                                   ax2_leaf=PGMarginalBivar.kLeaf,
                                   ax1_alpha=alpha_S,
                                   ax2_alpha=alpha_T,
                                   title=title1 + title2)
        w.generate(criteria)


################################################################################
# Calculation Functions
################################################################################


__api__ = [
    'BaseFLInteractive',
    'BaseFLMarginal',
    'BasePGInteractive',
    'BasePGMarginal',
    'FLMarginalUnivar',
    'FLInteractiveUnivar',
    'PGMarginalUnivar',
    'PGInteractiveUnivar',
    'FLMarginalBivar',
    'FLInteractiveBivar',
    'PGMarginalBivar',
    'PGInteractiveBivar',
]
