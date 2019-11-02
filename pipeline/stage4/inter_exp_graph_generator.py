# Copyright 2018 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
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
#


import os
import copy
import yaml
from perf_measures.scalability_univar import ScalabilityUnivar
from perf_measures.scalability_bivar import ScalabilityBivar
import perf_measures.self_organization as pmso
import perf_measures.block_collection as pmbc
import perf_measures.reactivity as pmr
import perf_measures.adaptability as pma
from .inter_exp_linegraphs import InterExpLinegraphs


class InterExpGraphGenerator:
    """
    Generates graphs from collated .csv data across a batch of experiments.

    Attributes:
    """

    def __init__(self, main_config, cmdopts, targets, batch_criteria):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.batch_criteria = batch_criteria
        self.main_config = main_config

        collate_csv_leaf = self.main_config['sierra']['collate_csv_leaf']
        collate_graph_leaf = self.main_config['sierra']['collate_graph_leaf']
        self.cmdopts["collate_root"] = os.path.abspath(os.path.join(self.cmdopts["output_root"],
                                                                    collate_csv_leaf))
        self.cmdopts["graph_root"] = os.path.abspath(os.path.join(self.cmdopts["graph_root"],
                                                                  collate_graph_leaf))
        self.targets = targets
        os.makedirs(self.cmdopts["graph_root"], exist_ok=True)

    def __call__(self):
        if not self.batch_criteria.is_bivar():
            self.__gen_for_univar_bc()
        else:
            self.__gen_for_bivar_bc()

    # Private functions
    def __gen_for_univar_bc(self):
        InterExpLinegraphs(self.cmdopts["collate_root"],
                           self.cmdopts["graph_root"],
                           self.targets).generate()

        if self.batch_criteria.pm_query('blocks-collected'):
            pmbc.BlockCollectionUnivar(self.cmdopts,
                                       self.main_config['sierra']['perf']['inter_perf_csv']).generate(self.batch_criteria)

        if self.batch_criteria.pm_query('scalability'):
            ScalabilityUnivar().generate(self.main_config['sierra']['perf']['inter_perf_csv'],
                                         self.main_config['sierra']['perf']['ca_in_csv'],
                                         self.cmdopts,
                                         self.batch_criteria)

        if self.batch_criteria.pm_query('self-org'):
            pmso.SelfOrganizationFLUnivar(self.cmdopts,
                                          self.main_config['sierra']['perf']['inter_perf_csv'],
                                          self.main_config['sierra']['perf']['ca_in_csv']).generate(self.batch_criteria)

        if self.batch_criteria.pm_query('reactivity'):
            pmr.ReactivityUnivar(self.cmdopts).generate(self.batch_criteria)

        if self.batch_criteria.pm_query('adaptability'):
            pma.AdaptabilityUnivar(self.cmdopts).generate(self.batch_criteria)

    def __gen_for_bivar_bc(self):
        if self.batch_criteria.pm_query('blocks-collected'):
            pmbc.BlockCollectionBivar(self.cmdopts,
                                      self.main_config['sierra']['perf']['inter_perf_csv']).generate(self.batch_criteria)

        if self.batch_criteria.pm_query('scalability'):
            ScalabilityBivar().generate(self.cmdopts, self.batch_criteria)

        if self.batch_criteria.pm_query('self-org'):
            pmso.SelfOrganizationFLBivar(self.cmdopts,
                                         self.main_config['sierra']['perf']['inter_perf_csv'],
                                         self.main_config['sierra']['perf']['ca_in_csv']).generate(self.batch_criteria)

        if self.batch_criteria.pm_query('reactivity'):
            pmr.ReactivityBivar(self.cmdopts).generate(self.batch_criteria)

        if self.batch_criteria.pm_query('adaptability'):
            pma.AdaptabilityBivar(self.cmdopts).generate(self.batch_criteria)
