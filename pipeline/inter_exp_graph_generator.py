"""
Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""

import os
import copy
import yaml
from pipeline.inter_exp_linegraphs import InterExpLinegraphs
from perf_measures.scalability_univar import ScalabilityUnivar
from perf_measures.scalability_bivar import ScalabilityBivar
from perf_measures.self_organization import SelfOrganizationUnivar
from perf_measures.self_organization import SelfOrganizationBivar
from perf_measures.block_collection import BlockCollectionUnivar
from perf_measures.block_collection import BlockCollectionBivar
from perf_measures.reactivity import ReactivityUnivar
from perf_measures.reactivity import ReactivityBivar
from perf_measures.adaptability import AdaptabilityUnivar
from perf_measures.adaptability import AdaptabilityBivar


class InterExpGraphGenerator:
    """
    Generates graphs from collated .csv data across a batch of experiments.

    Attributes:
    """

    def __init__(self, cmdopts, targets, batch_criteria):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.batch_criteria = batch_criteria

        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')))

        self.cmdopts["collate_root"] = os.path.abspath(os.path.join(self.cmdopts["output_root"],
                                                                    self.main_config['sierra']['collate_csv_leaf']))
        self.cmdopts["graph_root"] = os.path.abspath(os.path.join(self.cmdopts["graph_root"],
                                                                  self.main_config['sierra']['collate_graph_leaf']))
        self.controller_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                             'controllers.yaml')))
        self.linegraph_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                            'inter-graphs-line.yaml')))
        self.targets = targets
        os.makedirs(self.cmdopts["graph_root"], exist_ok=True)

    def __call__(self):
        if isinstance(self.cmdopts['perf_measures'], list):
            components = self.cmdopts['perf_measures'][0].split(',')
        else:
            components = self.cmdopts['perf_measures']

        if not self.batch_criteria.is_bivar():
            self.__gen_for_univar_bc(components)
        else:
            self.__gen_for_bivar_bc(components)

    # Private functions
    def __gen_for_univar_bc(self, components):
        if "all" in components or "sp" in components:
            BlockCollectionUnivar(self.cmdopts,
                                  self.main_config['sierra']['perf']['inter_perf_csv']).generate(self.batch_criteria)

        if "all" in components or "line" in components:
            InterExpLinegraphs(self.cmdopts["collate_root"],
                               self.cmdopts["graph_root"],
                               self.targets).generate()

        if "all" in components or "ss" in components:
            ScalabilityUnivar().generate(self.cmdopts, self.batch_criteria)

        if "all" in components or "so" in components:
            SelfOrganizationUnivar(self.cmdopts,
                                   self.main_config['sierra']['perf']['inter_perf_csv'],
                                   self.main_config['sierra']['perf']['ca_in_csv']).generate(self.batch_criteria)

        if "all" in components or "sr" in components:
            ReactivityUnivar(self.cmdopts).generate(self.batch_criteria)

        if "all" in components or "sa" in components:
            AdaptabilityUnivar(self.cmdopts).generate(self.batch_criteria)

    def __gen_for_bivar_bc(self, components):
        if "all" in components or "sp" in components:
            BlockCollectionBivar(self.cmdopts,
                                 self.main_config['sierra']['perf']['inter_perf_csv']).generate(self.batch_criteria)
        if "all" in components or "ss" in components:
            ScalabilityBivar().generate(self.cmdopts, self.batch_criteria)

        if "all" in components or "line" in components:

            InterExpLinegraphs(self.cmdopts["collate_root"],
                               self.cmdopts["graph_root"],
                               self.targets).generate()

        if "all" in components or "so" in components:
            SelfOrganizationBivar(self.cmdopts,
                                  self.main_config['sierra']['perf']['inter_perf_csv'],
                                  self.main_config['sierra']['perf']['ca_in_csv']).generate(self.batch_criteria)

        if "all" in components or "sr" in components:
            ReactivityBivar(self.cmdopts).generate(self.batch_criteria)

        if "all" in components or "sa" in components:
            AdaptabilityBivar(self.cmdopts).generate(self.batch_criteria)
