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

import os
import copy
import logging
import pandas as pd

from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.heatmap import Heatmap
import core.perf_measures as pm
import core.variables.batch_criteria as bc


class RawUnivar:
    """
    Generates a :class:`~core.graphs.stacked_line_graph.StackedLineGraph` from the cumulative raw
    performance count of the swarm configuration across a univariate batched set of experiments
    within the same scenario from collated ``.csv`` data.

    """

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def generate(self, batch_criteria: bc.IConcreteBatchCriteria, title: str, ylabel: str):
        logging.info("Univariate raw performance from %s", self.cmdopts["collate_root"])
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.inter_perf_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["collate_root"],
                                    "pm-" + self.inter_perf_stem + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["collate_root"],
                                       "pm-" + self.inter_perf_stem)

        if os.path.exists(stddev_ipath):
            RawUnivar.__gen_stddev(stddev_ipath, stddev_opath)

        RawUnivar.__gen_csv(perf_ipath, perf_opath_stem + '.csv')

        BatchRangedGraph(inputy_stem_fpath=perf_opath_stem,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-" + self.inter_perf_stem + ".png"),
                         title=title,
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel=ylabel,
                         xticks=batch_criteria.graph_xticks(self.cmdopts)).generate()

    @staticmethod
    def __gen_stddev(ipath: str, opath: str):
        total_stddev_df = pd.read_csv(ipath, sep=';')
        cum_stddev_df = pd.DataFrame(columns=total_stddev_df.columns)

        for col in cum_stddev_df.columns:
            cum_stddev_df[col] = total_stddev_df.tail(1)[col]

        cum_stddev_df.to_csv(opath, sep=';', index=False)

    @staticmethod
    def __gen_csv(ipath: str, opath: str):
        assert(os.path.exists(ipath)), "FATAL: {0} does not exist".format(ipath)
        total_df = pd.read_csv(ipath, sep=';')
        cum_df = pd.DataFrame(columns=total_df.columns)

        for col in cum_df.columns:
            cum_df[col] = total_df.tail(1)[col]

        cum_df.to_csv(opath, sep=';', index=False)


class RawBivar:
    """
    Generates a :class:`core.graphs.heatmap.Heatmap` from the cumulative raw performance count of
    the swarm configuration across a bivariate batched set of experiments within the same scenario
    from collated ``.csv`` data.

    """

    def __init__(self, cmdopts: dict, inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def generate(self, batch_criteria: bc.IConcreteBatchCriteria, title: str):
        logging.info("Bivariate raw performance from %s", self.cmdopts["collate_root"])
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.inter_perf_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["collate_root"],
                                    self.inter_perf_stem + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["collate_root"],
                                       "pm-" + self.inter_perf_stem)

        if os.path.exists(stddev_ipath):
            RawBivar.__gen_stddev(stddev_ipath, stddev_opath)

        RawBivar.__gen_csv(perf_ipath, perf_opath_stem + '.csv')

        Heatmap(input_fpath=perf_opath_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"],
                                          "pm-" + self.inter_perf_stem + ".png"),
                title=title,
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()

    @staticmethod
    def __gen_stddev(ipath: str, opath: str):
        total_stddev_df = pd.read_csv(ipath, sep=';')
        cum_stddev_df = pd.DataFrame(columns=total_stddev_df.columns)

        for c in cum_stddev_df.columns:
            cum_stddev_df[c] = total_stddev_df.tail(1)[c]

        cum_stddev_df.to_csv(opath, sep=';', index=False)

    @staticmethod
    def __gen_csv(ipath: str, opath: str):
        assert(os.path.exists(ipath)), "FATAL: {0} does not exist".format(ipath)
        total_df = pd.read_csv(ipath, sep=';')
        cum_df = pd.DataFrame(columns=total_df.columns,
                              index=total_df.index)

        for i in range(0, len(cum_df.index)):
            for j in range(0, len(cum_df.columns)):
                cum_df.iloc[i, j] = pm.common.csv_3D_value_iloc(total_df,
                                                                i,
                                                                j,
                                                                slice(-1, None))

        cum_df.to_csv(opath, sep=';', index=False)


__api__ = [
    'RawUnivar',
    'RawBivar'
]
