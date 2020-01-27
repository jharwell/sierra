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
from core.graphs.scatterplot2D import Scatterplot2D
import core.variables.saa_noise as saan
import core.perf_measures.common as common


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
                                                      0,
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
        Generate (1) a :class:`~core.graphs.heatmap.Heatmap` of the robustness vs. the other one,
        (2) a :class:`~core.graphs.scatterplot2D.Scatterplot2D` of the robustness vs. performance.
        """
        csv_ipath = self.__gen_heatmap(main_config, batch_criteria)
        self.__gen_scatterplot(csv_ipath)

    def __gen_scatterplot(self, rob_ipath: str):
        """
        Generate a :class:`~core.graphs.scatterplot2D.Scatterplot2D` graph of robustness
        vs. performance AFTER the main robustness `.csv` has generated in :method:`__gen_heatmap()`
        """
        perf_ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_stem + '.csv')
        opath = os.path.join(self.cmdopts['collate_root'],
                             'pm-robustness-saa-vs-perf.csv')
        perf_df = pd.read_csv(perf_ipath, sep=';')
        rob_df = pd.read_csv(rob_ipath, sep=';')
        scatter_df = pd.DataFrame(columns=['perf', 'robustness-saa'])

        # The inter-perf csv has temporal sequences at each (i,j) location, so we need to reduce
        # each of those to a single scalar: the cumulate measure of performance.
        for i in range(0, len(perf_df.index)):
            for j in range(0, len(perf_df.columns)):
                n_blocks = common.csv_3D_value_iloc(perf_df,
                                                    i,
                                                    j,
                                                    slice(-1, None))
                perf_df.iloc[i, j] = n_blocks

        scatter_df['perf'] = perf_df.values.flatten()
        scatter_df['robustness-saa'] = rob_df.values.flatten()
        scatter_df.to_csv(opath, sep=';', index=False)

        Scatterplot2D(input_csv_fpath=opath,
                      output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                "pm-robustness-saa-vs-perf.png"),
                      title='Swarm Robustness (SAA) vs. Performance',
                      xcol='robustness-saa',
                      ycol='perf',
                      regression=self.cmdopts['plot_regression_lines'],
                      xlabel='Robustness Value',
                      ylabel='# Blocks Collected').generate()

    def __gen_heatmap(self, main_config: dict, batch_criteria: BatchCriteria):
        """
        Generate a robustness graph for a given controller in a given scenario by computing the
        value of the robustness metric for each experiment within the batch, and plot
        a :class:`~core.graphs.heatmap.Heatmap` of the robustness variable vs. the other one.

        Returns:
           The path to the `.csv` file used to generate the heatmap.
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
                    val = vcs.RawPerfCS(main_config,
                                        self.cmdopts,
                                        j,  # exp0 in first row with i=0
                                        i * len(df.columns) + j)(batch_criteria)
                else:
                    val = vcs.RawPerfCS(main_config,
                                        self.cmdopts,  # exp0 in first col with j=0
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
        return opath_stem + '.csv'
