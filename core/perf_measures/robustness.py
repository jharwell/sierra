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


import os
import copy
import logging
import typing as tp

import pandas as pd

from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.perf_measures import vcs
from core.variables.batch_criteria import BatchCriteria
from core.graphs.heatmap import Heatmap
import core.variables.saa_noise as saan


class RobustnessSAAUnivar:
    """
    Calculates the robustness of the swarm configuration to sensor and actuator noise across a
    univariate batched set of experiments within the same scenario from collated .csv data using
    curve similarity measures.
    """

    def __init__(self, cmdopts: tp.Dict[str, str]):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us.
        self.cmdopts = copy.deepcopy(cmdopts)

    def generate(self, main_config: dict, batch_criteria: BatchCriteria):
        """
        Generate a robustness graph for a given controller in a given scenario by computing the
        value of the robustness metric for each experiment within the batch (Y values), and plotting
        a line graph from it using the X-values from the specified batch criteria.
        """

        logging.info("Univariate SAA Robustness from %s", self.cmdopts["collate_root"])
        batch_exp_dirnames = batch_criteria.gen_exp_dirnames(self.cmdopts)

        # Robustness is only defined for experiments > 0, as exp0 is assumed to be ideal conditions,
        # so we have to slice. We use the reactivity curve similarity measure because we are
        # interested in how closely the swarm's performnce under noise tracks that of ideal
        # conditions. With perfect SAA robustness, they should track exactly.

        df = pd.DataFrame(columns=batch_exp_dirnames, index=[0])
        df[batch_exp_dirnames[0]] = 0.0  # By definition

        for i in range(1, batch_criteria.n_exp()):
            df[batch_exp_dirnames[i]] = vcs.RawPerfCS(main_config,
                                                      self.cmdopts,
                                                      i)(batch_criteria)

        stem_opath = os.path.join(self.cmdopts["collate_root"], "pm-robustness-saa")

        # Write .csv to file
        df.to_csv(stem_opath + '.csv', sep=';', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_opath,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   "pm-saa-robustness.png"),
                         title="Swarm Robustness (SAA)",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel=vcs.method_ylabel(self.cmdopts["rperf_cs_method"],
                                                  'robustness_saa'),
                         xvals=batch_criteria.graph_xticks(self.cmdopts),
                         xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts)).generate()


class RobustnessSAABivar:
    """
    Calculates the robustness of the swarm configuration to sensor and actuator noise across a
    bivariate batched set of experiments within the same scenario from collated .csv data using
    curve similarity measures.

    """

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_stem = inter_perf_csv.split('.')[0]

    def generate(self, main_config: dict, batch_criteria: BatchCriteria):
        """
        Generate a robustness graph for a given controller in a given scenario by computing the
        value of the robustness metric for each experiment within the batch, and plot
        a heatmap of the robustness variable vs. the other one.

        """

        ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        raw_df = pd.read_csv(ipath, sep=';')
        df = pd.DataFrame(columns=raw_df.columns, index=raw_df.index)
        df.iloc[0, 0] = 0.0  # By definition

        xfactor = 0
        yfactor = 0
        # SAA noise is along rows (X), so the first row by definition has 0 distance to ideal
        # conditions
        if isinstance(batch_criteria.criteria1, saan.SAANoise):
            df.iloc[0, :] = 0.0
            xfactor = 1
        # SAA noise is along colums (Y), so the first column by definition has 0 distance to ideal
        # conditions
        else:
            df.iloc[:, 0] = 0.0
            yfactor = 1

        for i in range(0 + xfactor, len(df.index)):
            for j in range(0 + yfactor, len(df.columns)):
                # We need to know which of the 2 variables was SAA noise, in order to determine the
                # correct dimension along which to compute the metric.
                if isinstance(batch_criteria.criteria1, saan.SAANoise):
                    val = vcs.RawPerfCS(main_config, self.cmdopts, i / j, i)(batch_criteria)
                else:
                    val = vcs.RawPerfCS(main_config,
                                        self.cmdopts,
                                        i * len(df.columns),
                                        i * len(df.columns) + j)(batch_criteria)

                df.iloc[i, j] = val

        opath_stem = os.path.join(self.cmdopts["collate_root"], "pm-robustness-saa")

        df.to_csv(opath_stem + ".csv", sep=';', index=False)

        Heatmap(input_fpath=opath_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], "pm-robustness-saa.png"),
                title='Swarm Robustness (SAA)',
                xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                ylabel=batch_criteria.graph_ylabel(self.cmdopts),
                xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=batch_criteria.graph_yticklabels(self.cmdopts)).generate()
