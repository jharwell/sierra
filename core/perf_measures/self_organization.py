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

r"""
Measures for swarm self-organization/emergence in univariate and bivariate batched experiments.

.. IMPORTANT:: The calculations performed by classes in this module make the following assumptions:

               - Different swarm sizes are used for at least `some` experiments in the batch.

               - exp0 has $\mathcal{N}=1$

               If these assumptions are violated, the calculations may still have some
               value/utility, but it will be reduced.
"""


# Core packages
import os
import logging
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
from core.graphs.summary_line_graph import SummaryLinegraph
from core.graphs.heatmap import Heatmap
import core.perf_measures.common as pmcommon
from core.variables import batch_criteria as bc
from core.variables import population_size
from core.variables import population_density
import core.utils
import core.config

################################################################################
# Base Classes
################################################################################


class BaseSteadyStateFLMarginal():
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
    kLeaf = "PM-ss-self-org-mfl"

    @staticmethod
    def kernel(fl_i: float,
               n_robots_i: int,
               fl_iminus1: float,
               n_robots_iminus1: int,
               normalize: bool,
               normalize_method: str) -> tp.Optional[float]:

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


class BaseSteadyStateFLInteractive():
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
    kLeaf = "PM-ss-self-org-ifl"

    @staticmethod
    def kernel(fl_i: float,
               n_robots_i: int,
               fl_1: float,
               normalize: bool,
               normalize_method: str) -> tp.Optional[float]:
        scaled_fl_1 = float(n_robots_i) * fl_1
        theta = scaled_fl_1 - fl_i

        if normalize:
            if normalize_method == 'sigmoid':
                return core.utils.Sigmoid(theta)() - core.utils.Sigmoid(-theta)()
            else:
                return None
        else:
            return theta


class BaseSteadyStatePGMarginal():
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
    kLeaf = "PM-ss-self-org-mpg"

    @staticmethod
    def kernel(perf_i: float,
               n_robots_i: int,
               perf_iminus1: float,
               n_robots_iminus1: int,
               normalize: bool,
               normalize_method: str) -> tp.Optional[float]:
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


class BaseSteadyStatePGInteractive():
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
    kLeaf = "PM-ss-self-org-ipg"

    @staticmethod
    def kernel(perf_i: float,
               n_robots_i: int,
               perf_0: float,
               normalize: bool,
               normalize_method: str) -> tp.Optional[float]:
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


class SteadyStateFLMarginalUnivar(BaseSteadyStateFLMarginal):
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using marginal fractional
    performance losses due to inter-robot interference (See :class:`BaseSteadyStateFLMarginal`).

    Generates a :class:`~core.graphs.summary_line_graph.SummaryLinegraph` of self organization using
    :class:`~core.perf_measures.common.FractionalLossesUnivar`.
    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_fl: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        so_dfs = {}

        for i in range(1, criteria.n_exp()):
            n_robots_x = populations[i]
            expx = list(collated_fl.keys())[i]
            expx_fl_df = collated_fl[expx]

            n_robots_xminus1 = populations[i - 1]
            exp_xminus1 = list(collated_fl.keys())[i - 1]
            exp_xminus1_fl_df = collated_fl[exp_xminus1]

            so_dfs[expx] = pd.DataFrame(columns=collated_fl[expx].columns,
                                        index=[0])  # Steady state

            for sim in expx_fl_df.columns:
                fl_x = expx_fl_df.loc[expx_fl_df.index[-1], sim]
                fl_xminus1 = exp_xminus1_fl_df.loc[exp_xminus1_fl_df.index[-1], sim]

                self_org = BaseSteadyStateFLMarginal.kernel(fl_i=fl_x,
                                                            fl_iminus1=fl_xminus1,
                                                            n_robots_i=n_robots_x,
                                                            n_robots_iminus1=n_robots_xminus1,
                                                            normalize=cmdopts['pm_self_org_normalize'],
                                                            normalize_method=cmdopts['pm_normalize_method'])
                so_dfs[expx].loc[0, sim] = self_org

        return so_dfs

    def __init__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str,
                 interference_csv: str,
                 interference_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col
        self.interference_leaf = interference_csv.split('.')[0]
        self.interference_col = interference_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        perf_dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                                    criteria,
                                                    self.perf_leaf,
                                                    self.perf_col)
        interference_dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                                            criteria,
                                                            self.interference_leaf,
                                                            self.interference_col)

        plostN = pmcommon.SteadyStatePerfLostInteractiveSwarmUnivar.df_kernel(criteria,
                                                                              self.cmdopts,
                                                                              interference_dfs,
                                                                              perf_dfs)

        fl = pmcommon.SteadyStateFLUnivar.df_kernel(criteria, perf_dfs, plostN)

        pm_dfs = self.df_kernel(criteria, self.cmdopts, fl)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],
                         title="Swarm Self-Organization via Marginal Sub-Linear Performance Losses",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class SteadyStateFLInteractiveUnivar(BaseSteadyStateFLInteractive):
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional
    performance losses due to interative inter-robot interference vs. independent action (See
    :class:`BaseSteadyStateFLInteractive`).

    Generates a :class:`~core.graphs.summary_line_graph.SummaryLinegraph` of self organization using
    :class:`~core.perf_measures.common.FractionalLossesUnivar`.
    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_fl: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        so_dfs = {}

        exp0 = list(collated_fl.keys())[0]
        exp0_fl_df = collated_fl[exp0]

        for i in range(1, criteria.n_exp()):
            n_robots_x = populations[i]
            expx = list(collated_fl.keys())[i]
            expx_fl_df = collated_fl[expx]

            so_dfs[expx] = pd.DataFrame(columns=collated_fl[expx].columns,
                                        index=[0])  # Steady state

            for sim in expx_fl_df.columns:
                fl_x = expx_fl_df.loc[expx_fl_df.index[-1], sim]
                fl_1 = exp0_fl_df.loc[exp0_fl_df.index[-1], sim]
                self_org = BaseSteadyStateFLInteractive.kernel(fl_i=fl_x,
                                                               n_robots_i=n_robots_x,
                                                               fl_1=fl_1,
                                                               normalize=cmdopts['pm_self_org_normalize'],
                                                               normalize_method=cmdopts['pm_normalize_method'])
                so_dfs[expx].loc[0, sim] = self_org

        return so_dfs

    def __init__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str,
                 interference_csv: str,
                 interference_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col
        self.interference_leaf = interference_csv.split('.')[0]
        self.interference_col = interference_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        perf_dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                                    criteria,
                                                    self.perf_leaf,
                                                    self.perf_col)
        interference_dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                                            criteria,
                                                            self.interference_leaf,
                                                            self.interference_col)

        plostN = pmcommon.SteadyStatePerfLostInteractiveSwarmUnivar.df_kernel(criteria,
                                                                              self.cmdopts,
                                                                              interference_dfs,
                                                                              perf_dfs)

        fl = pmcommon.SteadyStateFLUnivar.df_kernel(criteria, perf_dfs, plostN)

        pm_dfs = self.df_kernel(criteria, self.cmdopts, fl)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],
                         title="Swarm Self-Organization via Sub-Linear Performance Losses Through Interaction",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class SteadyStatePGMarginalUnivar(BaseSteadyStatePGMarginal):
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N`, :math:`2N`, a
    linear 2X increase in performance is expected, and more than this indicates emergent behavior).

    Generates a :class:`~core.graphs.summary_line_graph.SummaryLinegraph` of self organization.
    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        so_dfs = {}

        for i in range(1, criteria.n_exp()):
            n_robots_x = populations[i]
            expx = list(collated_perf.keys())[i]
            expx_perf_df = collated_perf[expx]

            n_robots_xminus1 = populations[i - 1]
            exp_xminus1 = list(collated_perf.keys())[i - 1]
            exp_xminus1_perf_df = collated_perf[exp_xminus1]

            so_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                        index=[0])  # Steady state

            for sim in expx_perf_df.columns:
                perf_x = expx_perf_df.loc[expx_perf_df.index[-1], sim]
                perf_xminus1 = exp_xminus1_perf_df.loc[exp_xminus1_perf_df.index[-1], sim]
                self_org = BaseSteadyStatePGMarginal.kernel(perf_i=perf_x,
                                                            n_robots_i=n_robots_x,
                                                            perf_iminus1=perf_xminus1,
                                                            n_robots_iminus1=n_robots_xminus1,
                                                            normalize=cmdopts['pm_self_org_normalize'],
                                                            normalize_method=cmdopts['pm_normalize_method'])
                so_dfs[expx].loc[0, sim] = self_org

        return so_dfs

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate marginal performance gain measure for the given controller for each experiment in
        a batch.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],
                         title="Swarm Self-Organization via Marginal Performance Gains",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class SteadyStatePGInteractiveUnivar(BaseSteadyStatePGInteractive):
    """
    Calculates the self-organization of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between a swarm of :math:`N` interactive vs. independent robots.
    See :class:`BaseSteadyStatePGInteractive`.

    Generates a :class:`~core.graphs.summary_line_graph.SummaryLinegraph` of self organization.
    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        so_dfs = {}

        exp0 = list(collated_perf.keys())[0]
        exp0_perf_df = collated_perf[exp0]

        for i in range(1, criteria.n_exp()):
            n_robots_x = populations[i]
            expx = list(collated_perf.keys())[i]
            expx_perf_df = collated_perf[expx]

            so_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                        index=[0])  # Steady state

            for sim in expx_perf_df.columns:
                perf_0 = exp0_perf_df.loc[exp0_perf_df.index[-1], sim]
                perf_x = expx_perf_df.loc[expx_perf_df.index[-1], sim]
                self_org = BaseSteadyStatePGInteractive.kernel(perf_i=perf_x,
                                                               n_robots_i=n_robots_x,
                                                               perf_0=perf_0,
                                                               normalize=cmdopts['pm_self_org_normalize'],
                                                               normalize_method=cmdopts['pm_normalize_method'])

                so_dfs[expx].loc[0, sim] = self_org

        return so_dfs

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate marginal performance gain measure for the given controller for each experiment in
        a batch.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                                   self.kLeaf + core.config.kImageExt),
                         model_root=self.cmdopts['batch_model_root'],

                         title="Swarm Self-Organization via Performance Gains Through Interaction",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="",
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
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
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str,
                 interference_csv: str,
                 interference_col: str,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        SteadyStateFLMarginalUnivar(cmdopts,
                                    perf_csv,
                                    perf_col,
                                    interference_csv,
                                    interference_col).from_batch(criteria)
        SteadyStateFLInteractiveUnivar(cmdopts,
                                       perf_csv,
                                       perf_col,
                                       interference_csv,
                                       interference_col).from_batch(criteria)
        SteadyStatePGMarginalUnivar(cmdopts, perf_csv, perf_col).from_batch(criteria)
        SteadyStatePGInteractiveUnivar(cmdopts, perf_csv, perf_col).from_batch(criteria)


################################################################################
# Bivariate Classes
################################################################################


class SteadyStateFLMarginalBivar(BaseSteadyStateFLMarginal):
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to inter-robot interference (See :class:`BaseSteadyStateFLMarginal`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` of self organization from
    :class:`~core.perf_measures.common.FractionalLossesBivar` data.

    Assumptions:
        - exp0 has 1 robot.
        - One of the batch criteria was :class:`~core.variables.population_size.PopulationSize`
          derived.

    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_fl: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        so_dfs = {}

        for i in range(axis == 0, xsize):
            for j in range(axis == 1, ysize):
                expx = list(collated_fl.keys())[i * ysize + j]
                flx_df = collated_fl[expx]

                so_dfs[expx] = pd.DataFrame(columns=collated_fl[expx].columns,
                                            index=[0])  # Steady state
                n_robots_x = populations[i][j]

                for sim in flx_df.columns:
                    fl_x = flx_df.loc[flx_df.index[-1], sim]  # steady state

                    if axis == 0:
                        exp_xminus1 = list(collated_fl.keys())[(i - 1) * ysize + j]
                        n_robots_xminus1 = populations[i - 1][j]
                    else:
                        exp_xminus1 = list(collated_fl.keys())[i * ysize + (j - 1)]
                        n_robots_xminus1 = populations[i][j - 1]

                    fl_xminus1_df = collated_fl[exp_xminus1]
                    fl_xminus1 = fl_xminus1_df.loc[fl_xminus1_df.index[-1], sim]  # steady state

                    self_org = BaseSteadyStateFLMarginal.kernel(fl_i=fl_x,
                                                                n_robots_i=n_robots_x,
                                                                fl_iminus1=fl_xminus1,
                                                                n_robots_iminus1=n_robots_xminus1,
                                                                normalize=cmdopts['pm_self_org_normalize'],
                                                                normalize_method=cmdopts['pm_normalize_method'])

                    so_dfs[expx].loc[0, sim] = self_org

        return so_dfs

    def __init__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str,
                 interference_csv: str,
                 interference_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col
        self.interference_leaf = interference_csv.split('.')[0]
        self.interference_col = interference_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        perf_dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                                    criteria,
                                                    self.perf_leaf,
                                                    self.perf_col)
        interference_dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                                            criteria,
                                                            self.interference_leaf,
                                                            self.interference_col)

        plostN = pmcommon.SteadyStatePerfLostInteractiveSwarmBivar.df_kernel(criteria,
                                                                             self.cmdopts,
                                                                             interference_dfs,
                                                                             perf_dfs)

        fl = pmcommon.SteadyStateFLBivar.df_kernel(criteria, self.cmdopts, perf_dfs, plostN)

        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.
        axis = core.utils.get_primary_axis(criteria,
                                           [population_size.PopulationSize,
                                            population_density.PopulationConstantDensity],
                                           self.cmdopts)

        pm_dfs = self.df_kernel(criteria, self.cmdopts, axis, fl)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True, axis)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                             self.kLeaf + core.config.kStatsExtensions['mean'])
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title="Swarm Self-Organization via Marginal Sub-Linear Performance Losses",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class SteadyStateFLInteractiveBivar(BaseSteadyStateFLInteractive):
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using fractional performance
    losses due to interactive inter-robot interference vs independent action  (See
    :class:`BaseSteadyStateFLInteractive`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` of self organization from
    :class:`~core.perf_measures.common.FractionalLossesBivar` data.

    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_fl: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        so_dfs = {}

        for i in range(axis == 0, xsize):
            for j in range(axis == 1, ysize):
                expx = list(collated_fl.keys())[i * ysize + j]

                if axis == 0:
                    exp0 = list(collated_fl.keys())[0 * ysize + j]
                else:
                    exp0 = list(collated_fl.keys())[i * ysize + 0]

                flx_df = collated_fl[expx]

                so_dfs[expx] = pd.DataFrame(columns=collated_fl[expx].columns,
                                            index=[0])  # Steady state
                n_robots_x = populations[i][j]

                for sim in flx_df.columns:
                    fl_x = flx_df.loc[flx_df.index[-1], sim]  # steady state

                    fl_1_df = collated_fl[exp0]
                    fl_1 = fl_1_df.loc[fl_1_df.index[-1], sim]  # steady state

                    self_org = BaseSteadyStateFLInteractive.kernel(fl_i=fl_x,
                                                                   n_robots_i=n_robots_x,
                                                                   fl_1=fl_1,
                                                                   normalize=cmdopts['pm_self_org_normalize'],
                                                                   normalize_method=cmdopts['pm_normalize_method'])
                    so_dfs[expx].loc[0, sim] = self_org

        return so_dfs

    def __init__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str,
                 interference_csv: str,
                 interference_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col
        self.interference_leaf = interference_csv.split('.')[0]
        self.interference_col = interference_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        perf_dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                                    criteria,
                                                    self.perf_leaf,
                                                    self.perf_col)
        interference_dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                                            criteria,
                                                            self.interference_leaf,
                                                            self.interference_col)

        plostN = pmcommon.SteadyStatePerfLostInteractiveSwarmBivar.df_kernel(criteria,
                                                                             self.cmdopts,
                                                                             interference_dfs,
                                                                             perf_dfs)
        fl = pmcommon.SteadyStateFLBivar.df_kernel(criteria, self.cmdopts, perf_dfs, plostN)

        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.
        axis = core.utils.get_primary_axis(criteria,
                                           [population_size.PopulationSize,
                                            population_density.PopulationConstantDensity],
                                           self.cmdopts)

        pm_dfs = self.df_kernel(criteria, self.cmdopts, axis, fl)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True, axis)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                             self.kLeaf + core.config.kStatsExtensions['mean'])
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title="Swarm Self-Organization via Sub-Linear Performance Losses",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class SteadyStatePGMarginalBivar(BaseSteadyStatePGMarginal):
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between adjacent swarm size (e.g. for two swarms of size :math:`N`, :math:`2N`, a 2X
    increase in performance is expected, and more than this indicates emergent behavior).
    See :class:`BaseSteadyStatePGMarginal`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` of self organization.
    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        so_dfs = {}

        for i in range(axis == 0, xsize):
            for j in range(axis == 1, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_df = collated_perf[expx]
                so_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state
                n_robots_x = populations[i][j]

                for sim in expx_df.columns:
                    perf_x = expx_df.loc[expx_df.index[-1], sim]  # steady state

                    if axis == 0:
                        exp_xminus1 = list(collated_perf.keys())[(i - 1) * ysize + j]
                        exp_xminus1_df = collated_perf[exp_xminus1]

                        # steady state
                        perf_xminus1 = exp_xminus1_df.loc[exp_xminus1_df.index[-1], sim]
                        n_robots_xminus1 = populations[i - 1][j]
                    else:
                        exp_xminus1 = list(collated_perf.keys())[i * ysize + (j - 1)]
                        exp_xminus1_df = collated_perf[exp_xminus1]

                        # steady state
                        perf_xminus1 = exp_xminus1_df.loc[exp_xminus1_df.index[-1], sim]
                        n_robots_xminus1 = populations[i][j - 1]

                    self_org = BaseSteadyStatePGMarginal.kernel(perf_i=perf_x,
                                                                n_robots_i=n_robots_x,
                                                                perf_iminus1=perf_xminus1,
                                                                n_robots_iminus1=n_robots_xminus1,
                                                                normalize=cmdopts['pm_self_org_normalize'],
                                                                normalize_method=cmdopts['pm_normalize_method'])
                    so_dfs[expx].loc[0, sim] = self_org

        return so_dfs

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate marginal performance gain metric for the given controller for each experiment in a
        batch.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.
        axis = core.utils.get_primary_axis(criteria,
                                           [population_size.PopulationSize,
                                            population_density.PopulationConstantDensity],
                                           self.cmdopts)

        pm_dfs = self.df_kernel(criteria, self.cmdopts, axis, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True, axis)

        so_opath = os.path.join(self.cmdopts["batch_stat_collate_root"], self.kLeaf)

        Heatmap(input_fpath=so_opath + '.csv',
                output_fpath=os.path.join(self.cmdopts["batch_graph_collate_root"],
                                          self.kLeaf + core.config.kImageExt),
                title="Swarm Self-Organization via Marginal Performance Gains",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class SteadyStatePGInteractiveBivar(BaseSteadyStatePGInteractive):
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated ``.csv`` data using superlinear increases in
    performance between a swarm of :math:`N` interacting vs. indpendently acting robots.
    See :class:`BaseSteadyStatePGInteractive`).

    Generates a :class:`~core.graphs.heatmap.Heatmap` of self organization.
    """

    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        populations = criteria.populations(cmdopts)
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        so_dfs = {}

        for i in range(axis == 0, xsize):
            for j in range(axis == 1, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_df = collated_perf[expx]
                so_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state
                n_robots_x = populations[i][j]

                for sim in expx_df.columns:
                    perf_x = expx_df.loc[expx_df.index[-1], sim]  # steady state

                    if axis == 0:
                        exp0 = list(collated_perf.keys())[0 * ysize + j]
                    else:
                        exp0 = list(collated_perf.keys())[i * ysize + 0]

                    exp0_df = collated_perf[exp0]
                    perf_0 = exp0_df.loc[exp0_df.index[-1], sim]

                    self_org = BaseSteadyStatePGInteractive.kernel(perf_i=perf_x,
                                                                   n_robots_i=n_robots_x,
                                                                   perf_0=perf_0,
                                                                   normalize=cmdopts['pm_self_org_normalize'],
                                                                   normalize_method=cmdopts['pm_normalize_method'])
                    so_dfs[expx].loc[0, sim] = self_org

        return so_dfs

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Calculate marginal performance gain metric for the given controller for each experiment in a
        batch.
        """
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        # We need to know which of the 2 variables was swarm size, in order to determine
        # the correct dimension along which to compute the metric, which depends on
        # performance between adjacent swarm sizes.
        axis = core.utils.get_primary_axis(criteria,
                                           [population_size.PopulationSize,
                                            population_density.PopulationConstantDensity],
                                           self.cmdopts)
        pm_dfs = self.df_kernel(criteria, self.cmdopts, axis, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True, axis)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                             self.kLeaf + core.config.kStatsExtensions['mean'])
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title="Swarm Self-Organization via Performance Gains Through Interaction",
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class SelfOrgBivarGenerator:
    """
    Calculates the self-organization of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in various ways.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str,
                 interference_csv: str,
                 interference_col: str,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        SteadyStateFLMarginalBivar(cmdopts,
                                   perf_csv,
                                   perf_col,
                                   interference_csv,
                                   interference_col).from_batch(criteria)
        SteadyStateFLInteractiveBivar(cmdopts,
                                      perf_csv,
                                      perf_col,
                                      interference_csv,
                                      interference_col).from_batch(criteria)
        SteadyStatePGMarginalBivar(cmdopts, perf_csv, perf_col).from_batch(criteria)
        SteadyStatePGInteractiveBivar(cmdopts, perf_csv, perf_col).from_batch(criteria)


################################################################################
# Calculation Functions
################################################################################

__api__ = [
    'BaseSteadyStateFLInteractive',
    'BaseSteadyStateFLMarginal',
    'BaseSteadyStatePGInteractive',
    'BaseSteadyStatePGMarginal',
    'SteadyStateFLMarginalUnivar',
    'SteadyStateFLInteractiveUnivar',
    'SteadyStatePGMarginalUnivar',
    'SteadyStatePGInteractiveUnivar',
    'SteadyStateFLMarginalBivar',
    'SteadyStateFLInteractiveBivar',
    'SteadyStatePGMarginalBivar',
    'SteadyStatePGInteractiveBivar',
]
