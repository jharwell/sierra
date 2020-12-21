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
import pandas as pd

# 3rd party packages

# Project packages
from core.graphs.batch_ranged_graph import BatchRangedGraph
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
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.logger = logging.getLogger(__name__)

    def from_batch(self, criteria: bc.IConcreteBatchCriteria, title: str, ylabel: str):
        self.logger.info("Univariate raw performance from %s", self.cmdopts["batch_collate_root"])

        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["batch_collate_root"], self.inter_perf_stem + '.csv')
        perf_opath = os.path.join(self.cmdopts["batch_collate_root"], self.kLeaf + '.csv')
        img_opath = os.path.join(
            self.cmdopts["batch_collate_graph_root"], self.kLeaf + core.config.kImageExt)

        # We always calculate the metric
        df = self.df_kernel(core.utils.pd_csv_read(perf_ipath))
        core.utils.pd_csv_write(df, perf_opath, index=False)

        # Stddev might not have been calculated in stage 3
        if core.utils.path_exists(stddev_ipath):
            stddev_df = self.df_kernel(core.utils.pd_csv_read(stddev_ipath))
            core.utils.pd_csv_write(stddev_df, stddev_opath, index=False)

        BatchRangedGraph(input_fpath=perf_opath,
                         output_fpath=img_opath,
                         stddev_fpath=stddev_opath,
                         model_fpath=os.path.join(self.cmdopts['batch_model_root'],
                                                  self.kLeaf + '.model'),
                         model_legend_fpath=os.path.join(self.cmdopts['batch_model_root'],
                                                         self.kLeaf + '.legend'),
                         title=title,
                         xlabel=criteria.graph_xlabel(self.cmdopts),
                         ylabel=ylabel,
                         xticks=criteria.graph_xticks(self.cmdopts),
                         logyscale=self.cmdopts['plot_log_yscale']).generate()


class RawBivar:
    """
    Generates a :class:`core.graphs.heatmap.Heatmap` from the cumulative raw performance count of
    the swarm configuration across a bivariate batched set of experiments within the same scenario
    from collated ``.csv`` data.

    """
    kLeaf = 'PM-raw'

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]
        self.logger = logging.getLogger(__name__)

    def from_batch(self, criteria: bc.IConcreteBatchCriteria, title: str):
        self.logger.info("Bivariate raw performance from %s", self.cmdopts["batch_collate_root"])
        stddev_ipath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["batch_collate_root"],
                                    self.inter_perf_stem + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["batch_collate_root"], self.inter_perf_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["batch_collate_graph_root"], self.kLeaf)

        if core.utils.path_exists(stddev_ipath):
            RawBivar._gen_stddev(stddev_ipath, stddev_opath)

        RawBivar._gen_csv(perf_ipath, perf_opath_stem + '.csv')

        Heatmap(input_fpath=perf_opath_stem + '.csv',
                output_fpath=perf_opath_stem + core.config.kImageExt,
                title=title,
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()

    @staticmethod
    def _gen_stddev(ipath: str, opath: str):
        total_stddev_df = core.utils.pd_csv_read(ipath)
        cum_stddev_df = pd.DataFrame(columns=total_stddev_df.columns)

        for c in cum_stddev_df.columns:
            cum_stddev_df[c] = total_stddev_df.tail(1)[c]

        core.utils.pd_csv_write(cum_stddev_df, opath, index=False)

    @staticmethod
    def _gen_csv(ipath: str, opath: str):
        assert(core.utils.path_exists(ipath)), "FATAL: {0} does not exist".format(ipath)
        total_df = core.utils.pd_csv_read(ipath)
        cum_df = pd.DataFrame(columns=total_df.columns,
                              index=total_df.index)

        for i in range(0, len(cum_df.index)):
            for j in range(0, len(cum_df.columns)):
                cum_df.iloc[i, j] = pm.common.csv_3D_value_iloc(total_df,
                                                                i,
                                                                j,
                                                                slice(-1, None))

        core.utils.pd_csv_write(cum_df, opath, index=False)


__api__ = [
    'RawUnivar',
    'RawBivar'
]
