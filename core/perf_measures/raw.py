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
import copy
import logging

# 3rd party packages
import pandas as pd

# Project packages
from core.graphs.summary_line_graph import SummaryLinegraph
from core.graphs.heatmap import Heatmap
import core.perf_measures as pm
import core.variables.batch_criteria as bc
import core.utils
import core.config


class RawUnivar:
    """
    Generates a :class:`~core.graphs.stacked_line_graph.StackedLineGraph` from the cumulative raw
    performance count of the swarm configuration across a univariate batched set of experiments
    within the same scenario from collated ``.csv`` data.

    """
    kLeaf = 'PM-raw'

    @staticmethod
    def df_kernel(df_t: pd.DataFrame) -> pd.DataFrame:
        df = pd.DataFrame(columns=df_t.columns, index=[0])
        for col in df_t:
            df[col] = df_t.loc[df_t.index[-1], col]

        return df

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]
        self.logger = logging.getLogger(__name__)

    def from_batch(self, criteria: bc.IConcreteBatchCriteria, title: str, ylabel: str):
        self.logger.info("From %s", self.cmdopts["batch_stat_collate_root"])

        perf_ipath = os.path.join(
            self.cmdopts["batch_stat_collate_root"], self.inter_perf_leaf + '.csv')
        perf_opath = os.path.join(self.cmdopts["batch_stat_collate_root"], self.kLeaf + '.csv')
        img_opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                                 self.kLeaf + core.config.kImageExt)

        # We always calculate the metric from experimental data
        df = self.df_kernel(core.utils.pd_csv_read(perf_ipath))
        core.utils.pd_csv_write(df, perf_opath, index=False)

        # We might calculate the metric from experiment statistics
        _stats_prepare(self.cmdopts, self.inter_perf_leaf, self.kLeaf, self.df_kernel)

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

    def _stats_prepare(self) -> None:
        for k in core.config.kStatsExtensions.keys():
            stat_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.inter_perf_leaf + core.config.kStatsExtensions[k])
            stat_opath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                      self.kLeaf + core.config.kStatsExtensions[k])
            if core.utils.path_exists(stat_ipath):
                stat_df = self.df_kernel(core.utils.pd_csv_read(stat_ipath))
                core.utils.pd_csv_write(stat_df, stat_opath, index=False)


class RawBivar:
    """
    Generates a :class:`core.graphs.heatmap.Heatmap` from the cumulative raw performance count of
    the swarm configuration across a bivariate batched set of experiments within the same scenario
    from collated ``.csv`` data.

    """
    kLeaf = 'PM-raw'

    @staticmethod
    def df_kernel(df_t: pd.DataFrame) -> pd.DataFrame:
        df = pd.DataFrame(columns=df_t.columns, index=df_t.index)

        for i in range(0, len(df_t.index)):
            for j in range(0, len(df_t.columns)):
                df.iloc[i, j] = pm.common.csv_3D_value_iloc(df_t,
                                                            i,
                                                            j,
                                                            slice(-1, None))

        return df

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_leaf = inter_perf_csv.split('.')[0]
        self.logger = logging.getLogger(__name__)

    def from_batch(self, criteria: bc.IConcreteBatchCriteria, title: str):
        self.logger.info("From %s", self.cmdopts["batch_stat_collate_root"])

        perf_ipath = os.path.join(self.cmdopts["batch_stat_collate_root"],
                                  self.inter_perf_leaf + core.config.kStatsExtensions['mean'])
        perf_opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                                  self.kLeaf + core.config.kStatsExtensions['mean'])
        img_opath = os.path.join(self.cmdopts["batch_graph_collate_root"],
                                 self.kLeaf + core.config.kImageExt)

        # We always calculate the metric from experimental data
        df = self.df_kernel(core.utils.pd_csv_read(perf_ipath))

        core.utils.pd_csv_write(df, perf_opath, index=False)

        # We might calculate the metric from experiment statistics
        _stats_prepare(self.cmdopts, self.inter_perf_leaf, self.kLeaf, self.df_kernel)

        Heatmap(input_fpath=perf_opath,
                output_fpath=img_opath,
                title=title,
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()


def _stats_prepare(cmdopts: dict,
                   inter_perf_ileaf: str,
                   oleaf: str,
                   kernel) -> None:

    for k in core.config.kStatsExtensions.keys():
        stat_ipath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  inter_perf_ileaf + core.config.kStatsExtensions[k])
        stat_opath = os.path.join(cmdopts["batch_stat_collate_root"],
                                  oleaf + core.config.kStatsExtensions[k])

        if core.utils.path_exists(stat_ipath) and core.config.kPickleExt not in stat_ipath:
            stat_df = kernel(core.utils.pd_csv_read(stat_ipath))
            core.utils.pd_csv_write(stat_df, stat_opath, index=False)
        elif core.utils.path_exists(stat_ipath) and core.config.kPickleExt in stat_ipath:
            stat_df = kernel(core.utils.pd_pickle_read(stat_ipath))
            core.utils.pd_pickle_write(stat_df, stat_opath)


__api__ = [
    'RawUnivar',
    'RawBivar'
]
