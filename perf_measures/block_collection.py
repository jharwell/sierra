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
Measures for swarm performance in foraging tasks via block collection in univariate and bivariate
batched experiments.
"""

import os
import copy
import logging
import typing as tp
import pandas as pd
from graphs.batch_ranged_graph import BatchRangedGraph
from graphs.heatmap import Heatmap
import perf_measures.common
import variables.batch_criteria as bc


class BlockCollectionUnivar:
    """
    Generates a :class:`~graphs.stacked_line_graph.StackedLineGraph` from the cumulative blocks
    collected count of the swarm configuration across a univariate batched set of experiments within
    the same scenario from collated ``.csv`` data.

    """

    def __init__(self, cmdopts: tp.Dict[str, str], blocks_collected_csv: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_stem = blocks_collected_csv.split('.')[0]

    def generate(self, batch_criteria: bc.BatchCriteria):
        logging.info("Univariate block collection from %s", self.cmdopts["collate_root"])
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["collate_root"],
                                    "pm-" + self.blocks_collected_stem + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["collate_root"], self.blocks_collected_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["collate_root"],
                                       "pm-" + self.blocks_collected_stem)

        if os.path.exists(stddev_ipath):
            BlockCollectionUnivar.__gen_stddev(stddev_ipath, stddev_opath)

        BlockCollectionUnivar.__gen_csv(perf_ipath, perf_opath_stem + '.csv')

        BatchRangedGraph(inputy_stem_fpath=perf_opath_stem,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-" + self.blocks_collected_stem + ".png"),
                         title="Swarm Blocks Collected",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="# Blocks",
                         xvals=batch_criteria.graph_xticks(self.cmdopts)).generate()

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
        cum_df = pd.DataFrame(columns=total_df.columns)

        for col in cum_df.columns:
            cum_df[col] = total_df.tail(1)[col]

        cum_df.to_csv(opath, sep=';', index=False)


class BlockCollectionBivar:
    """
    Generates a :class:`graphs.heatmap.Heatmap` from the cumulative blocks collected count of the
    swarm configuration across a bivariate batched set of experiments within the same scenario from
    collated ``.csv`` data.

    """

    def __init__(self, cmdopts: tp.Dict[str, str], blocks_collected_csv: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_stem = blocks_collected_csv.split('.')[0]

    def generate(self, batch_criteria: bc.BatchCriteria):
        logging.info("Bivariate block collection from %s", self.cmdopts["collate_root"])
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["collate_root"], self.blocks_collected_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["collate_root"],
                                       "pm-" + self.blocks_collected_stem)

        if os.path.exists(stddev_ipath):
            BlockCollectionBivar.__gen_stddev(stddev_ipath, stddev_opath)

        BlockCollectionBivar.__gen_csv(perf_ipath, perf_opath_stem + '.csv')

        Heatmap(input_fpath=perf_opath_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"],
                                          "pm-" + self.blocks_collected_stem + ".png"),
                title='Swarm Blocks Collected',
                xlabel=batch_criteria.graph_ylabel(self.cmdopts),
                ylabel=batch_criteria.graph_xlabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_yticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_xticklabels(self.cmdopts)).generate()

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
                cum_df.iloc[i, j] = perf_measures.common.csv_3D_value_iloc(total_df,
                                                                           i,
                                                                           j,
                                                                           slice(-1, None))

        cum_df.to_csv(opath, sep=';', index=False)
