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
import core.utils
from core.variables.population_size import PopulationSize
from core.variables import batch_criteria as bc
from core.graphs.heatmap import Heatmap
from core.graphs.summary_line_graph import SummaryLinegraph
import core.config
from core.xml_luigi import XMLAttrChangeSet

################################################################################
# Base Classes
################################################################################


class BasePerfLostInteractiveSwarm():
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


class BaseFractionalLosses:
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
        if plostN == 0:
            return 1.0  # No performance = 100% fractional loss
        else:
            return round(plostN / perfN, 8)

    def __init__(self,
                 cmdopts: dict,
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
                                                         core.config.kPickleLeaf))

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


class PerfLostInteractiveSwarmUnivar(BasePerfLostInteractiveSwarm):
    """
    Calculated as follows for all swarm sizes N in the batch:

    plost 1 robot = 0 # By definition

    plost N robots = :class:`~BasePerfLostInteractiveSwarm`.kernel().

    This gives how much MORE performance was lost in the entire simulation as a result of a swarm of
    size N, as opposed to a group of N robots that do not interact with each other, only the arena
    walls. Swarms exhibiting high levels of emergent behavior should have `positive` values of
    performance loss (i.e. they performed `better` than a swarm of N independent robots).

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    """

    @staticmethod
    def df_kernel(criteria: bc.UnivarBatchCriteria,
                  cmdopts: dict,
                  interference_df: pd.DataFrame,
                  perf_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculated as follows for all swarm sizes N in the batch:

        performance exp0 * tlost_1 (for exp0)

        performance exp0 * (tlost_N - N * tlost_1) / N (else)

        This gives how much MORE performance was lost in the entire simulation as a result of a
        swarm of size N, as opposed to a group of N robots that do not interact with each other,
        only the arena walls.
        """

        plostN = pd.DataFrame(columns=perf_df.columns, index=[0])
        exp0_dir = perf_df.columns[0]
        populations = criteria.populations(cmdopts)

        # Case 1: 1 robot/exp0
        perf1 = perf_df.loc[perf_df.index[-1], exp0_dir]
        tlost1 = interference_df.loc[interference_df.index[-1], exp0_dir]

        # Case 2 : N>1 robots
        scale_cols = [c for c in interference_df.columns if c not in [exp0_dir]]
        perf_taili = perf_df.index[-1]

        for c in scale_cols:
            n_robots = populations[list(plostN.columns).index(c)]
            perfN = perf_df.loc[perf_taili, c]
            tlostN = interference_df.loc[perf_taili, c]

            plostN.loc[0, c] = BasePerfLostInteractiveSwarm.kernel(perf1=perf1,
                                                                   tlost1=tlost1,
                                                                   perfN=perfN,
                                                                   tlostN=tlostN,
                                                                   n_robots=n_robots)

        # By definition, no performance losses with 1 robot
        plostN.loc[0, exp0_dir] = 0.0
        return plostN

    def __init__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str) -> None:
        self.cmdopts = cmdopts
        self.batch_stat_collate_root = cmdopts["batch_stat_collate_root"]
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.interference_stem = interference_count_csv.split('.')[0]

    def from_batch(self, criteria: bc.UnivarBatchCriteria) -> pd.DataFrame:
        # Get .csv with interference info
        interference_path = os.path.join(
            self.batch_stat_collate_root, self.interference_stem + '.csv')
        assert(core.utils.path_exists(interference_path)
               ), "FATAL: {0} does not exist".format(interference_path)
        interference_df = core.utils.pd_csv_read(interference_path)
        interference_df = interference_df.tail(1)

        # Get .csv with performance info
        perf_path = os.path.join(self.batch_stat_collate_root, self.inter_perf_stem + '.csv')

        assert(core.utils.path_exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = core.utils.pd_csv_read(perf_path)
        perf_df = perf_df.tail(1)

        # Calculate the performatime lost per timestep for a swarm of size N due to collision
        # avoidance interference
        return self.df_kernel(criteria, self.cmdopts, interference_df, perf_df)


class FractionalLossesUnivar(BaseFractionalLosses):
    """
    Fractional losses calculation for univariate batch criteria.

    Does not require the batch criteria to be
    :class:`~core.variables.population_size.PopulationSize` derived, but if all experiments in a
    batch have the same swarm size, then this calculation will be of limited use.

    """
    @staticmethod
    def df_kernel(perf_df: pd.DataFrame, plostN: pd.DataFrame) -> pd.DataFrame:
        fl_df = pd.DataFrame(columns=perf_df.columns, index=[0])

        perf_taili = perf_df.index[-1]
        fl_df.iloc[0, 0] = 0.0  # By definition, no fractional losses in exp(0,0)

        for i in range(1, len(fl_df.columns)):
            c = fl_df.columns[i]
            fl_df.loc[0, c] = BaseFractionalLosses.kernel(perf_df.loc[perf_taili, c],
                                                          plostN.loc[0, c])

        return fl_df

    def from_batch(self, criteria: bc.UnivarBatchCriteria) -> pd.DataFrame:
        # First calculate the performance lost due to inter-robot interference
        plostN = PerfLostInteractiveSwarmUnivar(self.cmdopts,
                                                self.inter_perf_csv,
                                                self.interference_count_csv).from_batch(criteria)

        # Get .csv with performance info
        perf_path = os.path.join(self.batch_stat_collate_root, self.inter_perf_stem + '.csv')
        assert(core.utils.path_exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = core.utils.pd_csv_read(perf_path)

        # Calculate fractional losses for all swarm sizes
        return self.df_kernel(perf_df, plostN)


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
        self.logger = logging.getLogger(__name__)

    def generate(self, criteria: bc.IConcreteBatchCriteria):
        csv1_istem = os.path.join(self.cmdopts["batch_stat_collate_root"], self.ax1_leaf)
        csv2_istem = os.path.join(self.cmdopts["batch_stat_collate_root"], self.ax2_leaf)
        csv1_ipath = csv1_istem + '.csv'
        csv2_ipath = csv2_istem + '.csv'

        csv_ostem = os.path.join(self.cmdopts["batch_stat_collate_root"], self.output_leaf)
        img_ostem = os.path.join(self.cmdopts["batch_graph_collate_root"], self.output_leaf)

        if not core.utils.path_exists(csv1_ipath) or not core.utils.path_exists(csv2_ipath):
            self.logger.debug("Not generating univariate weighted performance measure: %s or %s does not exist",
                              csv1_ipath, csv2_ipath)
            return

        ax1_df = core.utils.pd_csv_read(csv1_istem + '.csv')
        ax2_df = core.utils.pd_csv_read(csv2_istem + '.csv')
        out_df = ax1_df * self.ax1_alpha + ax2_df * self.ax2_alpha

        core.utils.pd_csv_write(out_df, csv_ostem + '.csv', index=False)

        xticks = criteria.graph_xticks(self.cmdopts)
        len_diff = len(xticks) - len(out_df.columns)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=csv_ostem,
                         output_fpath=img_ostem + core.config.kImageExt,
                         title=self.title,
                         ylabel="Value",
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         xticks=xticks[len_diff:],
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()

################################################################################
# Bivariate Classes
################################################################################


class PerfLostInteractiveSwarmBivar(BasePerfLostInteractiveSwarm):
    """
    Bivariate calculator for the perforance lost per-robot for a swarm of size N of `interacting`
    robots, as oppopsed to a  swarm of size N of `non-interacting` robots. See
    :class:`~core.perf_measures.common.PerfLostInteractiveSwarmUnivar` for a description of the
    mathematical calculations performed by this class.
    """
    @staticmethod
    def df_kernel(criteria: bc.BivarBatchCriteria,
                  cmdopts: dict,
                  interference_df: pd.DataFrame,
                  perf_df: pd.DataFrame):
        plostN = pd.DataFrame(columns=perf_df.columns, index=perf_df.index)
        exp0_dir = perf_df.columns[0]
        populations = criteria.populations(cmdopts)

        # Calc for exp(0,0)
        tlost1 = csv_3D_value_loc(interference_df,
                                  0,  # exp0 = 1 robot
                                  exp0_dir,
                                  slice(-1, None))  # Last in temporal seq = cum avg
        perf1 = csv_3D_value_loc(perf_df,
                                 0,  # exp0 = 1 robot
                                 exp0_dir,
                                 slice(-1, None))  # Last in temporal seq = cum count

        # Calc for general case
        for i in range(0, len(plostN.index)):
            for j in range(0, len(plostN.columns)):
                if i == 0 and plostN.columns[j] == exp0_dir:  # exp(0,0)
                    # By definition, no performance losses with 1 robot
                    plostN.loc[i, exp0_dir] = 0.0
                    continue

                perfN = csv_3D_value_iloc(perf_df,
                                          i,
                                          j,
                                          slice(-1, None))

                tlostN = csv_3D_value_iloc(interference_df,
                                           # Last row = N robots
                                           len(interference_df.index) - 1,
                                           j,
                                           slice(-1, None))  # Last in temporal seq = cum avg

                # We need to know which of the 2 variables was swarm size, in order to determine the
                # correct axis along which to compute the metric, which depends on swarm size.
                if isinstance(criteria.criteria1, PopulationSize) or cmdopts['plot_primary_axis'] == '0':
                    n_robots = populations[i][0]  # same population in all columns
                else:
                    n_robots = populations[0][j]  # same population in all rows

                plostN.iloc[i, j] = BasePerfLostInteractiveSwarm.kernel(perf1=perf1,
                                                                        tlost1=tlost1,
                                                                        perfN=perfN,
                                                                        tlostN=tlostN,
                                                                        n_robots=n_robots)

        return plostN

    def __init__(self,
                 cmdopts: dict,
                 inter_perf_csv: str,
                 interference_count_csv: str) -> None:
        self.cmdopts = cmdopts
        self.batch_stat_collate_root = cmdopts["batch_stat_collate_root"]
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.interference_stem = interference_count_csv.split('.')[0]

    def from_batch(self, criteria: bc.BivarBatchCriteria):
        # Get .csv with interference info
        interference_path = os.path.join(
            self.batch_stat_collate_root, self.interference_stem + '.csv')
        assert(core.utils.path_exists(interference_path)
               ), "FATAL: {0} does not exist".format(interference_path)
        interference_df = core.utils.pd_csv_read(interference_path)

        # Get .csv with performance info
        perf_path = os.path.join(self.batch_stat_collate_root, self.inter_perf_stem + '.csv')
        assert(core.utils.path_exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = core.utils.pd_csv_read(perf_path)

        # Calculate the performatime lost per timestep for a swarm of size N due to
        # inter-robot interference
        return self.df_kernel(criteria, self.cmdopts, interference_df, perf_df)


class FractionalLossesBivar(BaseFractionalLosses):
    """
    Fractional losses calculation for bivariate batch criteria. See
    :class:`~core.perf_measures.common.FractionalLossesUnivar` for a description of the mathematical
    calculations performed by this class.

    """
    @staticmethod
    def df_kernel(perf_df: pd.DataFrame, plost_df: pd.DataFrame):
        fl_df = pd.DataFrame(columns=perf_df.columns, index=perf_df.index)
        exp0_dir = perf_df.columns[0]

        for i in range(0, len(fl_df.index)):
            for c in fl_df.columns:
                if i == 0 and c == exp0_dir:  # exp(0,0)
                    fl_df.loc[i, c] = 0.0  # By definition, no fractional losses in exp(0,0)
                    continue

                perfN = csv_3D_value_loc(perf_df, i, c, slice(-1, None))
                plostN = plost_df.loc[i, c]
                fl_df.loc[i, c] = BaseFractionalLosses.kernel(perfN, plostN)

        return fl_df

    def from_batch(self, criteria: bc.BivarBatchCriteria):
        # First calculate the performance lost due to inter-robot interference
        plostN = PerfLostInteractiveSwarmBivar(self.cmdopts,
                                               self.inter_perf_csv,
                                               self.interference_count_csv).from_batch(criteria)

        # Get .csv with performance info
        perf_path = os.path.join(self.batch_stat_collate_root, self.inter_perf_stem + '.csv')
        assert(core.utils.path_exists(perf_path)), "FATAL: {0} does not exist".format(perf_path)
        perf_df = core.utils.pd_csv_read(perf_path)

        # Calculate fractional losses for all swarm sizes
        return FractionalLossesBivar.df_kernel(perf_df, plostN)


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
        self.logger = logging.getLogger(__name__)

    def generate(self, criteria: bc.IConcreteBatchCriteria):
        csv1_istem = os.path.join(self.cmdopts["batch_stat_collate_root"], self.ax1_leaf)
        csv2_istem = os.path.join(self.cmdopts["batch_stat_collate_root"], self.ax2_leaf)
        csv1_ipath = csv1_istem + '.csv'
        csv2_ipath = csv2_istem + '.csv'

        csv_ostem = os.path.join(self.cmdopts["batch_stat_collate_root"], self.output_leaf)
        img_ostem = os.path.join(self.cmdopts["batch_graph_collate_root"], self.output_leaf)

        if not core.utils.path_exists(csv1_ipath) or not core.utils.path_exists(csv2_ipath):
            self.logger.debug("Not generating bivariate weighted performance measure: %s or %s does not exist",
                              csv1_ipath, csv2_ipath)
            return

        ax1_df = core.utils.pd_csv_read(csv1_istem + '.csv')
        ax2_df = core.utils.pd_csv_read(csv2_istem + '.csv')
        out_df = ax1_df * self.ax1_alpha + ax2_df * self.ax2_alpha
        core.utils.pd_csv_write(out_df, csv_ostem + '.csv', index=False)

        xlabels = criteria.graph_xticklabels(self.cmdopts)
        ylabels = criteria.graph_yticklabels(self.cmdopts)

        len_xdiff = len(xlabels) - len(out_df.index)
        len_ydiff = len(ylabels) - len(out_df.columns)

        Heatmap(input_fpath=csv_ostem + '.csv',
                output_fpath=img_ostem + core.config.kImageExt,
                title=self.title,
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts)[len_xdiff:],
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)[len_ydiff:]).generate()


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


def stats_prepare(cmdopts: dict,
                  criteria: bc.IConcreteBatchCriteria,
                  inter_perf_ileaf: str,
                  oleaf: str,
                  kernel) -> None:
    for k in core.config.kStatsExtensions.keys():
        stat_ipath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  inter_perf_ileaf + core.config.kStatsExtensions[k])
        stat_opath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  oleaf + core.config.kStatsExtensions[k])
        if core.utils.path_exists(stat_ipath):
            stat_df = kernel(criteria, cmdopts, core.utils.pd_csv_read(stat_ipath))
            core.utils.pd_csv_write(stat_df, stat_opath, index=False)


__api__ = [
    'PerfLostInteractiveSwarmUnivar',
    'PerfLostInteractiveSwarmBivar',
    'FractionalLossesUnivar',
    'FractionalLossesBivar',
    'BasePerfLostInteractiveSwarm',
    'BaseFractionalLosses'
]
