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


import os
import copy
import pandas as pd
import numpy as np
import logging
from graphs.batch_ranged_graph import BatchRangedGraph
from graphs.heatmap import Heatmap


class BlockCollectionUnivar:
    """
    Generates a stacked line graph from the cumulative blocks collected count of the swarm
    configuration across a univariate batched set of experiments within the same scenario from
    collated .csv data.

    """

    def __init__(self, cmdopts, blocks_collected_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_stem = blocks_collected_csv.split('.')[0]

    def generate(self, batch_criteria):
        logging.info("Univariate block collection from {0}".format(self.cmdopts["collate_root"]))
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["collate_root"],
                                    "pm-" + self.blocks_collected_stem + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["collate_root"], self.blocks_collected_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["collate_root"],
                                       "pm-" + self.blocks_collected_stem)

        if os.path.exists(stddev_ipath):
            self.__gen_stddev(stddev_ipath, stddev_opath)

        self.__gen_csv(perf_ipath, perf_opath_stem + '.csv')

        BatchRangedGraph(inputy_stem_fpath=perf_opath_stem,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-" + self.blocks_collected_stem + ".png"),
                         title="Swarm Blocks Collected",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel="# Blocks",
                         xvals=batch_criteria.graph_xticks(self.cmdopts),
                         legend=None,
                         polynomial_fit=-1).generate()

    def __gen_stddev(self, ipath, opath):
        total_stddev_df = pd.read_csv(ipath, sep=';')
        cum_stddev_df = pd.DataFrame(columns=total_stddev_df.columns)

        for c in cum_stddev_df.columns:
            cum_stddev_df[c] = total_stddev_df.tail(1)[c]

        cum_stddev_df.to_csv(opath, sep=';', index=False)

    def __gen_csv(self, ipath, opath):
        assert(os.path.exists(ipath)), "FATAL: {0} does not exist".format(ipath)
        total_df = pd.read_csv(ipath, sep=';')
        cum_df = pd.DataFrame(columns=total_df.columns)

        for col in cum_df.columns:
            cum_df[col] = total_df.tail(1)[col]

        cum_df.to_csv(opath, sep=';', index=False)


class BlockCollectionBivar:
    """
    Generates a 2D heatmap from the cumulative blocks collected count of the swarm configuration
    across a bivariate batched set of experiments within the same scenario from collated .csv data.

    """

    def __init__(self, cmdopts, blocks_collected_csv):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.blocks_collected_stem = blocks_collected_csv.split('.')[0]

    def generate(self, batch_criteria):
        logging.info("Bivariate block collection from {0}".format(self.cmdopts["collate_root"]))
        stddev_ipath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + '.stddev')
        stddev_opath = os.path.join(self.cmdopts["collate_root"],
                                    self.blocks_collected_stem + ".stddev")
        perf_ipath = os.path.join(self.cmdopts["collate_root"], self.blocks_collected_stem + '.csv')
        perf_opath_stem = os.path.join(self.cmdopts["collate_root"],
                                       "pm-" + self.blocks_collected_stem)

        if os.path.exists(stddev_ipath):
            self.__gen_stddev(stddev_ipath, stddev_opath)

        self.__gen_csv(perf_ipath, perf_opath_stem + '.csv')

        Heatmap(input_fpath=perf_opath_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"],
                                          "pm-" + self.blocks_collected_stem + ".png"),
                title='Swarm Blocks Collected',
                xlabel=batch_criteria.graph_ylabel(self.cmdopts),
                ylabel=batch_criteria.graph_xlabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_yticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_xticklabels(self.cmdopts)).generate()

    def __gen_stddev(self, ipath, opath):
        total_stddev_df = pd.read_csv(ipath, sep=';')
        cum_stddev_df = pd.DataFrame(columns=total_stddev_df.columns)

        for c in cum_stddev_df.columns:
            cum_stddev_df[c] = total_stddev_df.tail(1)[c]

        cum_stddev_df.to_csv(opath, sep=';', index=False)

    def __gen_csv(self, ipath, opath):
        assert(os.path.exists(ipath)), "FATAL: {0} does not exist".format(ipath)
        total_df = pd.read_csv(ipath, sep=';')
        cum_df = pd.DataFrame(columns=total_df.columns,
                              index=total_df.index)

        for i in range(0, len(cum_df.index)):
            for col in cum_df.columns:
                # When collated, the column of data is written as a numpy array to string, so we
                # have to reparse it as an actual array
                arr = np.fromstring(total_df.loc[i, col][1:-1], dtype=np.float, sep=' ')

                # We want the CUMULATIVE count of blocks, which will be the last element in this
                # array. The second index is an artifact of how numpy represents scalars (1 element
                # arrays).
                cum_df.loc[i, col] = arr[-1:][0]

        cum_df.to_csv(opath, sep=';', index=False)
