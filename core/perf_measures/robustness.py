# Copyright 2020 John Harwell, All rights reserved.
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
Classes for measuring the robustness of a swarm configuration in various ways.
"""

# Core packages
import os
import logging
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
from core.graphs.summary_line_graph import SummaryLinegraph
from core.perf_measures import vcs
import core.variables.batch_criteria as bc
from core.graphs.heatmap import Heatmap
from core.graphs.scatterplot2D import Scatterplot2D
import core.variables.saa_noise as saan
import core.perf_measures.common as pmcommon
import core.utils
from core.variables.population_dynamics import PopulationDynamics
from core.xml_luigi import XMLAttrChangeSet

kIDEAL_SAA_ROBUSTNESS = 0.0


class BaseSteadyStateRobustnessSAA:
    kLeaf = 'PM-ss-robustness-saa'


class BaseSteadyStateRobustnessPD:
    r"""
    Calculate swarm robustness to fluctuating swarm populations. Equation taken from
    :xref:`Harwell2020`.

    .. math::
       B_{sz}(\kappa) = \sum_{t\in{T}}\theta_{B_{sz}}

    or

    .. math::
       B_{sz}(\kappa) = \sum_{t\in{T}}\frac{1}{1+e^(-\theta_{B_{sz}})} - \frac{1}{1+e^(+\theta_{B_{sz}})}

    depending on normalization configuration.

    where

    .. math::
       \theta_{B_{sz}}(\kappa,t) = P(N,\kappa,t) - \frac{T_S}{T}P_{ideal}(N,\kappa,t)

    """
    kLeaf = 'PM-ss-robustness-pd'

    @staticmethod
    def kernel(T_Sbar0: float,
               T_SbarN: float,
               perf0: float,
               perfN: float,
               normalize: bool,
               normalize_method: str) -> tp.Optional[float]:
        scaled_perf0 = float(T_Sbar0) / float(T_SbarN) * perf0
        theta = (perfN - scaled_perf0)

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


class SteadyStateRobustnessSAAUnivar(BaseSteadyStateRobustnessSAA):
    """
    Calculates the robustness of the swarm configuration to sensor and actuator noise across a
    univariate batched set of experiments within the same scenario from collated .csv data using
    curve similarity measures.
    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  main_config: tp.Dict[str, tp.Any],
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[pd.DataFrame, str]:
        saa_dfs = {}

        exp0 = list(collated_perf.keys())[0]
        exp0_perf_df = collated_perf[exp0]

        for i in range(1, criteria.n_exp()):
            expx = list(collated_perf.keys())[i]
            expx_perf_df = collated_perf[expx]
            saa_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns[1:],
                                         index=[0])  # Steady state

            for sim in expx_perf_df.columns:
                robustness = vcs.RawPerfCS(main_config,
                                           cmdopts).from_batch(ideal_perf_df=exp0_perf_df[sim],
                                                               expx_perf_df=expx_perf_df[sim])
                saa_dfs[expx].loc[0, sim] = robustness

        return saa_dfs

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate a robustness graph for a given controller in a given scenario by computing the
        value of the robustness metric for each experiment within the batch (Y values), and plotting
        a line graph from it using the X-values from the specified batch criteria.
        """

        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.main_config, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=opath,
                         title="Swarm Robustness (SAA)",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel=vcs.method_ylabel(self.cmdopts["rperf_cs_method"],
                                                  'robustness_saa'),
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
                         xtick_labels=criteria.graph_xticklabels(self.cmdopts)[1:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class SteadyStateRobustnessPDUnivar(BaseSteadyStateRobustnessPD):
    """
    Calculates the robustness of the swarm configuration to population size fluctuations across a
    univariate batched set of experiments within the same scenario from collated .csv data.
    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[pd.DataFrame, str]:
        pd_dfs = {}
        exp_dirs = criteria.gen_exp_dirnames(cmdopts)

        exp0 = list(collated_perf.keys())[0]
        exp0_perf_df = collated_perf[exp0]
        exp0_def = XMLAttrChangeSet.unpickle(os.path.join(cmdopts['batch_input_root'],
                                                          exp_dirs[0],
                                                          core.config.kPickleLeaf))
        T_Sbar0 = PopulationDynamics.calc_untasked_swarm_system_time(exp0_def)

        for i in range(0, criteria.n_exp()):
            expx = list(collated_perf.keys())[i]
            expx_perf_df = collated_perf[expx]
            pd_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                        index=[0])  # Steady state

            expN_def = XMLAttrChangeSet.unpickle(os.path.join(cmdopts['batch_input_root'],
                                                              exp_dirs[i],
                                                              core.config.kPickleLeaf))
            for sim in expx_perf_df.columns:
                T_SbarN = PopulationDynamics.calc_untasked_swarm_system_time(expN_def)
                perf0 = exp0_perf_df.loc[exp0_perf_df.index[-1], sim]
                perfN = expx_perf_df.loc[expx_perf_df.index[-1], sim]

                robustness = BaseSteadyStateRobustnessPD.kernel(T_Sbar0=T_Sbar0,
                                                                T_SbarN=T_SbarN,
                                                                perf0=perf0,
                                                                perfN=perfN,
                                                                normalize=cmdopts['pm_robustness_normalize'],
                                                                normalize_method=cmdopts['pm_normalize_method'])

                pd_dfs[expx].loc[0, sim] = robustness

        return pd_dfs

    def __init__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate a robustness graph for a given controller in a given scenario by computing the
        value of the robustness metric for each experiment within the batch (Y values), and plotting
        a line graph from it using the X-values from the specified batch criteria.
        """

        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(criteria, self.cmdopts, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True)

        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=opath,
                         title="Swarm Robustness (Population Dynamics)",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel="Robustness Value",
                         xticks=criteria.graph_xticks(self.cmdopts)[1:],
                         xtick_labels=criteria.graph_xticklabels(self.cmdopts)[1:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class RobustnessUnivarGenerator:
    """
    Calculates the robustness of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data in the following ways:

    - SAA robustness
    - Population dynamics robustness
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 main_config: tp.Dict[str, tp.Any],
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])
        perf_csv = main_config['perf']['intra_perf_csv']
        perf_col = main_config['perf']['intra_perf_col']

        if criteria.pm_query('robustness_saa'):
            SteadyStateRobustnessSAAUnivar(main_config,
                                           cmdopts,
                                           perf_csv,
                                           perf_col).from_batch(criteria)

        if criteria.pm_query('robustness_pd'):
            SteadyStateRobustnessPDUnivar(cmdopts,
                                          perf_csv,
                                          perf_col).from_batch(criteria)


################################################################################
# Bivariate Classes
################################################################################


class SteadyStateRobustnessSAABivar(BaseSteadyStateRobustnessSAA):
    """
    Calculates the robustness of the swarm configuration to sensor and actuator noise across a
    bivariate batched set of experiments within the same scenario from collated .csv data using
    curve similarity measures.
    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  main_config: tp.Dict[str, tp.Any],
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        saa_dfs = {}

        for i in range(axis == 0, xsize):
            for j in range(axis == 1, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_perf_df = collated_perf[expx]
                saa_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                             index=[0])  # Steady state

                if axis == 0:
                    exp_ideal = list(collated_perf.keys())[j]  # exp0 in first row with i=0
                else:
                    # exp0 in first col with j=0
                    exp_ideal = list(collated_perf.keys())[i * ysize]

                ideal_perf_df = collated_perf[exp_ideal]

                for sim in expx_perf_df.columns:
                    robustness = vcs.RawPerfCS(main_config,
                                               cmdopts).from_batch(ideal_perf_df=ideal_perf_df[sim],
                                                                   expx_perf_df=expx_perf_df[sim])

                    saa_dfs[expx].loc[0, sim] = robustness

        return saa_dfs

    def __init__(self,
                 main_config: tp.Dict[str, tp.Any],
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)

        # We need to know which of the 2 variables was SAA noise, in order to determine the correct
        # dimension along which to compute the metric.
        axis = core.utils.get_primary_axis(criteria,
                                           [saan.SAANoise],
                                           self.cmdopts)

        pm_dfs = self.df_kernel(criteria, self.main_config, self.cmdopts, axis, dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, True, axis)

        ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                             self.kLeaf + core.config.kStatsExtensions['mean'])
        opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                             self.kLeaf + core.config.kImageExt)

        Heatmap(input_fpath=ipath,
                output_fpath=opath,
                title='Swarm Robustness (SAA)',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class SteadyStateRobustnessPDBivar(BaseSteadyStateRobustnessPD):
    """
    Calculates the robustness of the swarm configuration to fluctuating population sies across a
    bivariate batched set of experiments within the same scenario from collated .csv data.
    """
    @staticmethod
    def df_kernel(criteria: bc.IConcreteBatchCriteria,
                  cmdopts: tp.Dict[str, tp.Any],
                  axis: int,
                  collated_perf: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:
        xsize = len(criteria.criteria1.gen_attr_changelist())
        ysize = len(criteria.criteria2.gen_attr_changelist())
        exp_dirs = criteria.gen_exp_dirnames(cmdopts)
        pd_dfs = {}

        for i in range(axis == 0, xsize):
            for j in range(axis == 1, ysize):
                expx = list(collated_perf.keys())[i * ysize + j]
                expx_perf_df = collated_perf[expx]
                pd_dfs[expx] = pd.DataFrame(columns=collated_perf[expx].columns,
                                            index=[0])  # Steady state

                expx_pkl_path = os.path.join(cmdopts['batch_input_root'],
                                             exp_dirs[i * ysize + j],
                                             core.config.kPickleLeaf)
                expx_def = XMLAttrChangeSet.unpickle(expx_pkl_path)
                T_SbarN = PopulationDynamics.calc_untasked_swarm_system_time(expx_def)

                if axis == 0:
                    # exp0 in first row with i=0
                    exp0 = list(collated_perf.keys())[j]
                    exp0_pkl_path = os.path.join(cmdopts['batch_input_root'],
                                                 exp_dirs[j],
                                                 core.config.kPickleLeaf)
                else:
                    # exp0 in first col with j=0
                    exp0 = list(collated_perf.keys())[i * ysize]
                    exp0_pkl_path = os.path.join(cmdopts['batch_input_root'],
                                                 exp_dirs[i * ysize],
                                                 core.config.kPickleLeaf)

                exp0_perf_df = collated_perf[exp0]
                exp0_def = XMLAttrChangeSet.unpickle(exp0_pkl_path)
                T_Sbar0 = PopulationDynamics.calc_untasked_swarm_system_time(exp0_def)

                for sim in expx_perf_df.columns:
                    perf0 = exp0_perf_df.loc[exp0_perf_df.index[-1], sim]
                    perfN = expx_perf_df.loc[expx_perf_df.index[-1], sim]
                    robustness = BaseSteadyStateRobustnessPD.kernel(T_Sbar0=T_Sbar0,
                                                                    T_SbarN=T_SbarN,
                                                                    perfN=perfN,
                                                                    perf0=perf0,
                                                                    normalize=cmdopts['pm_robustness_normalize'],
                                                                    normalize_method=cmdopts['pm_normalize_method'])
                    pd_dfs[expx].loc[0, sim] = robustness

        return pd_dfs

    def __init__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 perf_csv: str,
                 perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col

    def from_batch(self, criteria: bc.IConcreteBatchCriteria) -> None:
        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        # We need to know which of the 2 variables was population dynamics, in order to determine
        # the correct dimension along which to compute the metric.
        axis = core.utils.get_primary_axis(criteria,
                                           [PopulationDynamics],
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
                title='Swarm Robustness (Fluctuating Populations)',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[axis == 0:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[axis == 1:]).generate()


class RobustnessBivarGenerator:
    """
    Calculates the robustness of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in the following ways:

    - SAA robustness
    - Population dynamics robustness
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 cmdopts: tp.Dict[str, tp.Any],
                 main_config: tp.Dict[str, tp.Any],
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("From %s", cmdopts["batch_stat_collate_root"])

        perf_csv = main_config['perf']['intra_perf_csv']
        perf_col = main_config['perf']['intra_perf_col']

        if criteria.pm_query('robustness_saa'):
            SteadyStateRobustnessSAABivar(main_config,
                                          cmdopts,
                                          perf_csv,
                                          perf_col).from_batch(criteria)

        if criteria.pm_query('robustness_pd'):
            SteadyStateRobustnessPDBivar(cmdopts, perf_csv, perf_col).from_batch(criteria)


__api__ = [
    'SteadyStateRobustnessSAAUnivar',
    'SteadyStateRobustnessPDUnivar',
    'SteadyStateRobustnessSAABivar',
    'SteadyStateRobustnessPDBivar',
]
