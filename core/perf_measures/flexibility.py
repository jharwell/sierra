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
from core.perf_measures import vcs
import core.variables.batch_criteria as bc
import core.perf_measures.common as common

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

    def generate(self, main_config: dict, batch_criteria: bc.UnivarBatchCriteria):
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
                                                         i)()

        stem_opath = os.path.join(self.cmdopts["collate_root"], self.kLeaf)

        # Write .csv to file
        df.to_csv(stem_opath + '.csv', sep=';', index=False)
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

    def generate(self, main_config: dict, batch_criteria: bc.UnivarBatchCriteria):
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
                                                           i)()

        stem_opath = os.path.join(self.cmdopts["collate_root"], self.kLeaf)

        # Write .csv to file
        df.to_csv(stem_opath + '.csv', sep=';', index=False)

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
                 batch_criteria: bc.UnivarBatchCriteria):
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

    def __init__(self, cmdopts: tp.Dict[str, str]) -> None:
        raise NotImplementedError

    def generate(self, main_config: dict, batch_criteria: bc.BivarBatchCriteria):
        raise NotImplementedError


class AdaptabilityBivar:
    """
    Calculates the adaptability of the swarm configuration across a bivariate batched set of
    experiments within the same scenario from collated .csv data.

    """
    kLeaf = 'pm-adaptability'

    def __init__(self, cmdopts: tp.Dict[str, str]) -> None:
        raise NotImplementedError

    def generate(self, main_config: dict, batch_criteria: bc.BivarBatchCriteria):
        raise NotImplementedError


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
                 batch_criteria: bc.BivarBatchCriteria):
        logging.info("Biivariate flexbility from %s", cmdopts["collate_root"])

        ReactivityBivar(cmdopts).generate(main_config, batch_criteria)
        AdaptabilityBivar(cmdopts).generate(main_config, batch_criteria)

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
        w.generate(batch_criteria)


__api__ = [
    'AdaptabilityUnivar',
    'ReactivityUnivar'
]
