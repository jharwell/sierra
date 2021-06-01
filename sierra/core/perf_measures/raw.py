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
Measures for raw swarm performance in foraging tasks, according to whatever their configured
measure in univariate and bivariate batched experiments.

"""
# Core packages
import os
import logging
import typing as tp

# 3rd party packages
import pandas as pd

# Project packages
from sierra.core.graphs.summary_line_graph import SummaryLinegraph
from sierra.core.graphs.heatmap import Heatmap
import sierra.core.perf_measures as pm
import sierra.core.variables.batch_criteria as bc
import sierra.core.utils
import sierra.core.config
import sierra.core.stat_kernels
import sierra.core.perf_measures.common as pmcommon


class BaseSteadyStateRaw:
    kLeaf = 'PM-ss-raw'

    @staticmethod
    def df_kernel(collated: tp.Dict[str, pd.DataFrame]) -> tp.Dict[str, pd.DataFrame]:

        dfs = {}
        for exp in collated.keys():
            dfs[exp] = pd.DataFrame(columns=collated[exp].columns,
                                    index=[0])  # Steady state

            for col in collated[exp].columns:
                dfs[exp][col] = collated[exp].loc[collated[exp].index[-1], col]

        return dfs


class SteadyStateRawUnivar(BaseSteadyStateRaw):
    """
    Generates a :class:`~sierra.core.graphs.summary_line_graph.SummaryLinegraph` from the raw
    performance count of the swarm configuration across a univariate batched set of experiments
    within the same scenario from collated ``.csv`` data.

    """

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col
        self.logger = logging.getLogger(__name__)

    def from_batch(self, criteria: bc.IConcreteBatchCriteria, title: str, ylabel: str) -> None:
        self.logger.info("From %s", self.cmdopts["batch_stat_collate_root"])

        img_opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                                 self.kLeaf + sierra.core.config.kImageExt)

        dfs = pmcommon.gather_collated_sim_dfs(self.cmdopts,
                                               criteria,
                                               self.perf_leaf,
                                               self.perf_col)
        pm_dfs = self.df_kernel(dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.univar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, False)

        SummaryLinegraph(stats_root=self.cmdopts['batch_stat_collate_root'],
                         input_stem=self.kLeaf,
                         stats=self.cmdopts['dist_stats'],
                         output_fpath=img_opath,
                         model_root=self.cmdopts['batch_model_root'],
                         title=title,
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel=ylabel,
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text']).generate()


class SteadyStateRawBivar(BaseSteadyStateRaw):
    """
    Generates a :class:`sierra.core.graphs.heatmap.Heatmap` from the raw performance count of the swarm
    configuration across a bivariate batched set of experiments within the same scenario from
    collated ``.csv`` data.

    """

    def __init__(self, cmdopts: tp.Dict[str, tp.Any], perf_csv: str, perf_col: str) -> None:
        self.cmdopts = cmdopts
        self.perf_leaf = perf_csv.split('.')[0]
        self.perf_col = perf_col
        self.logger = logging.getLogger(__name__)

    def from_batch(self, criteria: bc.IConcreteBatchCriteria, title: str) -> None:
        self.logger.info("From %s", self.cmdopts["batch_stat_collate_root"])

        img_opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                                 self.kLeaf + sierra.core.config.kImageExt)

        dfs = pmcommon.gather_collated_sim_dfs(
            self.cmdopts, criteria, self.perf_leaf, self.perf_col)
        pm_dfs = self.df_kernel(dfs)

        # Calculate summary statistics for the performance measure
        pmcommon.bivar_distribution_prepare(self.cmdopts, criteria, self.kLeaf, pm_dfs, False)

        stat_opath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                  self.kLeaf + sierra.core.config.kStatsExtensions['mean'])
        img_opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                                 self.kLeaf + sierra.core.config.kImageExt)

        Heatmap(input_fpath=stat_opath,
                output_fpath=img_opath,
                title=title,
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


__api__ = [
    'BaseSteadyStateRaw',
    'SteadyStateRawUnivar',
    'SteadyStateRawBivar'
]
