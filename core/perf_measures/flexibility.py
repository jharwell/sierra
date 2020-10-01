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
Measures for swarm flexibility in univariate and bivariate batched experiments.

"""


import os
import copy
import logging
import typing as tp

import pandas as pd

from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.heatmap import Heatmap
from core.perf_measures import vcs
import core.variables.batch_criteria as bc
import core.perf_measures.common as common
import core.variables.temporal_variance as tv
import core.utils

################################################################################
# Univariate Classes
################################################################################


class ReactivityUnivar:
    """
    Calculates the reactivity of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data.
    """
    kLeaf = 'pm-reactivity'

    def __init__(self, cmdopts: tp.Dict[str, str]) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us.
        self.cmdopts = copy.deepcopy(cmdopts)

    def generate(self, main_config: dict, batch_criteria: bc.IConcreteBatchCriteria):
        """
        Calculate the reactivity metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """

        batch_exp_dirnames = batch_criteria.gen_exp_dirnames(self.cmdopts)

        df = pd.DataFrame(columns=batch_exp_dirnames[1:], index=[0])
        for i in range(1, len(batch_exp_dirnames)):
            df[batch_exp_dirnames[i]] = vcs.ReactivityCS(main_config,
                                                         self.cmdopts,
                                                         batch_criteria,
                                                         0,
                                                         i)()

        stem_opath = os.path.join(self.cmdopts["collate_root"], self.kLeaf)

        # Write .csv to file
        core.utils.pd_csv_write(df, stem_opath + '.csv', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_opath,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   self.kLeaf + ".png"),
                         title="Swarm Reactivity",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel=vcs.method_ylabel(self.cmdopts["reactivity_cs_method"],
                                                  'reactivity'),
                         xticks=batch_criteria.graph_xticks(self.cmdopts)[1:],
                         xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts)[1:]).generate()


class AdaptabilityUnivar:
    """
    Calculates the adaptability of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data.
    """
    kLeaf = 'pm-adaptability'

    def __init__(self, cmdopts: tp.Dict[str, str]) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us.
        self.cmdopts = copy.deepcopy(cmdopts)

    def generate(self, main_config: dict, batch_criteria: bc.IConcreteBatchCriteria):
        """
        Calculate the adaptability metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """

        batch_exp_dirnames = batch_criteria.gen_exp_dirnames(self.cmdopts)

        df = pd.DataFrame(columns=batch_exp_dirnames[1:], index=[0])
        for i in range(1, len(batch_exp_dirnames)):
            df[batch_exp_dirnames[i]] = vcs.AdaptabilityCS(main_config,
                                                           self.cmdopts,
                                                           batch_criteria,
                                                           0,
                                                           i)()

        stem_opath = os.path.join(self.cmdopts["collate_root"], self.kLeaf)

        # Write .csv to file
        core.utils.pd_csv_write(df, stem_opath + '.csv', index=False)

        BatchRangedGraph(inputy_stem_fpath=stem_opath,
                         output_fpath=os.path.join(self.cmdopts["graph_root"],
                                                   self.kLeaf + ".png"),
                         title="Swarm Adaptability",
                         xlabel=batch_criteria.graph_xlabel(self.cmdopts),
                         ylabel=vcs.method_ylabel(self.cmdopts["adaptability_cs_method"],
                                                  'adaptability'),
                         xticks=batch_criteria.graph_xticks(self.cmdopts)[1:],
                         xtick_labels=batch_criteria.graph_xticklabels(self.cmdopts)[1:]).generate()


class FlexibilityUnivarGenerator:
    """
    Calculates the flexibility of the swarm configuration across a univariate batched set of
    experiments within the same scenario from collated .csv data in the following ways:

    - Reactivity
    - Adaptability
    - Weight reactivity+adaptability
    """

    def __call__(self,
                 cmdopts: dict,
                 main_config: dict,
                 alpha_SAA: float,
                 alpha_PD: float,
                 batch_criteria: bc.IConcreteBatchCriteria):
        logging.info("Univariate flexbility from %s", cmdopts["collate_root"])

        ReactivityUnivar(cmdopts).generate(main_config, batch_criteria)
        AdaptabilityUnivar(cmdopts).generate(main_config, batch_criteria)

        title1 = r'Swarm Flexbility '
        title2 = r'($\alpha_{{F_{{R}}}}={0},\alpha_{{F_{{A}}}}={1}$)'.format(alpha_SAA,
                                                                             alpha_PD)
        w = common.WeightedPMUnivar(cmdopts=cmdopts,
                                    output_leaf='pm-flexibility',
                                    ax1_leaf=ReactivityUnivar.kLeaf,
                                    ax2_leaf=AdaptabilityUnivar.kLeaf,
                                    ax1_alpha=alpha_SAA,
                                    ax2_alpha=alpha_PD,
                                    title=title1 + title2)
        w.generate(batch_criteria)

################################################################################
# Bivariate Classes
################################################################################


class ReactivityBivar:
    """
    Calculates the reactivity of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data.

    """
    kLeaf = 'pm-reactivity'

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us.
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv

    def generate(self, main_config: dict, criteria: bc.BivarBatchCriteria):
        """
        Calculate the reactivity metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """
        self.__gen_heatmap(main_config, criteria)

    def __gen_heatmap(self, main_config: dict, criteria: bc.BivarBatchCriteria):
        """
        Generate a reactivity graph for a given controller in a given scenario by computing the
        value of the reactivity metric for each experiment within the batch, and plot
        a :class:`~core.graphs.heatmap.Heatmap` of the reactivity variable vs. the other one.

        Returns:
           The path to the `.csv` file used to generate the heatmap.
        """
        ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_csv)
        raw_df = core.utils.pd_csv_read(ipath)
        opath_stem = os.path.join(self.cmdopts["collate_root"], self.kLeaf)

        # Generate heatmap dataframe and write to file
        df = self.__gen_heatmap_df(main_config, raw_df, criteria)
        core.utils.pd_csv_write(df, opath_stem + ".csv", index=False)

        Heatmap(input_fpath=opath_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], self.kLeaf + ".png"),
                title='Swarm Reactivity',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()
        return opath_stem + '.csv'

    def __gen_heatmap_df(self,
                         main_config: dict,
                         raw_df: pd.DataFrame,
                         criteria: bc.BivarBatchCriteria):
        df = pd.DataFrame(columns=raw_df.columns, index=raw_df.index)

        exp_dirs = criteria.gen_exp_dirnames(self.cmdopts)
        for i in range(0, len(df.index)):
            for j in range(0, len(df.columns)):
                # We need to know which of the 2 variables was temporal variance, in order to
                # determine the correct dimension along which to compute the metric.
                if isinstance(criteria.criteria1, tv.TemporalVariance) or self.cmdopts['plot_primary_axis'] == '0':
                    val = vcs.ReactivityCS(main_config,
                                           self.cmdopts,
                                           criteria,
                                           j,  # exp0 in first row with i=0
                                           i)(exp_dirs)
                else:
                    val = vcs.ReactivityCS(main_config,
                                           self.cmdopts,
                                           criteria,
                                           i * len(df.columns),  # exp0 in first col with j=0
                                           i * len(df.columns) + j)(exp_dirs)

                df.iloc[i, j] = val
        return df


class AdaptabilityBivar:
    """
    Calculates the adaptability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data.

    """
    kLeaf = 'pm-adaptability'

    def __init__(self, cmdopts: tp.Dict[str, str], inter_perf_csv: str) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us.
        self.cmdopts = copy.deepcopy(cmdopts)
        self.inter_perf_csv = inter_perf_csv

    def generate(self, main_config: dict, criteria: bc.BivarBatchCriteria):
        """
        Calculate the adaptability metric for a given controller within a specific scenario, and
        generate a graph of the result.
        """
        self.__gen_heatmap(main_config, criteria)

    def __gen_heatmap(self, main_config: dict, criteria: bc.BivarBatchCriteria):
        """
        Generate a adaptability graph for a given controller in a given scenario by computing the
        value of the adaptability metric for each experiment within the batch, and plot
        a :class:`~core.graphs.heatmap.Heatmap` of the adaptability variable vs. the other one.

        Returns:
           The path to the `.csv` file used to generate the heatmap.
        """
        ipath = os.path.join(self.cmdopts["collate_root"], self.inter_perf_csv)
        raw_df = core.utils.pd_csv_read(ipath)
        opath_stem = os.path.join(self.cmdopts["collate_root"], self.kLeaf)

        # Generate heatmap dataframe and write to file
        df = self.__gen_heatmap_df(main_config, raw_df, criteria)
        core.utils.pd_csv_write(df, opath_stem + ".csv", index=False)

        Heatmap(input_fpath=opath_stem + '.csv',
                output_fpath=os.path.join(self.cmdopts["graph_root"], self.kLeaf + ".png"),
                title='Swarm Adaptability',
                xlabel=criteria.graph_xlabel(self.cmdopts),
                ylabel=criteria.graph_ylabel(self.cmdopts),
                xtick_labels=criteria.graph_xticklabels(self.cmdopts),
                ytick_labels=criteria.graph_yticklabels(self.cmdopts)).generate()
        return opath_stem + '.csv'

    def __gen_heatmap_df(self,
                         main_config: dict,
                         raw_df: pd.DataFrame,
                         criteria: bc.BivarBatchCriteria):
        df = pd.DataFrame(columns=raw_df.columns, index=raw_df.index)

        exp_dirs = criteria.gen_exp_dirnames(self.cmdopts)

        for i in range(0, len(df.index)):
            for j in range(0, len(df.columns)):
                # We need to know which of the 2 variables was temporal variance, in order to
                # determine the correct dimension along which to compute the metric.
                if isinstance(criteria.criteria1, tv.TemporalVariance) or self.cmdopts['plot_primary_axis'] == '0':
                    val = vcs.AdaptabilityCS(main_config,
                                             self.cmdopts,
                                             criteria,
                                             j,  # exp0 in first row with i=0
                                             i)(exp_dirs)
                else:
                    val = vcs.AdaptabilityCS(main_config,
                                             self.cmdopts,
                                             criteria,
                                             i * len(df.columns),  # exp0 in first col with j=0
                                             i * len(df.columns) + j)(exp_dirs)

                df.iloc[i, j] = val
        return df


class FlexibilityBivarGenerator:
    """
    Calculates the flexibility of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data in the following ways:

    - Reactivity
    - Adaptability
    - Weight reactivity+adaptability
    """

    def __call__(self,
                 cmdopts: dict,
                 main_config: dict,
                 alpha_SAA: float,
                 alpha_PD: float,
                 criteria: bc.IConcreteBatchCriteria):
        logging.info("Bivariate flexbility from %s", cmdopts["collate_root"])

        inter_perf_csv = main_config['perf']['inter_perf_csv']

        ReactivityBivar(cmdopts, inter_perf_csv).generate(main_config, criteria)
        AdaptabilityBivar(cmdopts, inter_perf_csv).generate(main_config, criteria)

        title1 = 'Swarm Flexbility '
        title2 = r'($\alpha_{{F_{{R}}}}={0},\alpha_{{F_{{A}}}}={1}$)'.format(alpha_SAA,
                                                                             alpha_PD)
        w = common.WeightedPMBivar(cmdopts=cmdopts,
                                   output_leaf='pm-flexibility',
                                   ax1_leaf=ReactivityBivar.kLeaf,
                                   ax2_leaf=AdaptabilityBivar.kLeaf,
                                   ax1_alpha=alpha_SAA,
                                   ax2_alpha=alpha_PD,
                                   title=title1 + title2)
        w.generate(criteria)


__api__ = [
    'AdaptabilityUnivar',
    'ReactivityUnivar'
]
