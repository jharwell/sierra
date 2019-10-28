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


import os
import typing as tp
import yaml
import logging
from .univar_comparator import UnivarComparator
from .bivar_comparator import BivarComparator


class PipelineStage5:

    """

    Implements stage 5 of the experimental pipeline: comparing controllers that have been tested
    with the same batch criteria using different performance measures across scenarios and within
    the same scenario

    Attributes:
        controllers: List of controllers to compare.
        norm_comp: Should comparisons be normalized against a controller of primary interest?
        cmdopts: Dictionary of parsed cmdline parameters.
        main_config Dictionary of parsed main YAML configuration.
        stage5_config: Dictionary of parsed stage5 YAML configuration.
        output_roots: Dictionary containing output directories for intra- and inter-scenario graph
                      generation.
    """

    def __init__(self, cmdopts: tp.Dict[str, str]):
        self.controllers = cmdopts['controller_comp_list']
        self.norm_comp = cmdopts['normalize_comparisons']
        self.cmdopts = cmdopts
        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')))
        self.stage5_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                         'stage5.yaml')))
        self.output_roots = {
            'cc_graphs': os.path.join(self.cmdopts['sierra_root'], "cc-graphs"),
            'cc_csvs': os.path.join(self.cmdopts['sierra_root'], "cc-csvs"),
        }

        for v in self.output_roots.values():
            os.makedirs(v, exist_ok=True)

    def run(self, cli_args):

        self.controllers = self.controllers.split(',')
        self.__verify_controllers(self.controllers)

        logging.info("Stage5: Inter-batch controller comparison of {0}...".format(self.controllers))

        if cli_args.bc_univar:
            UnivarComparator()(controllers=self.controllers,
                               graph_config=self.stage5_config,
                               output_roots=self.output_roots,
                               cmdopts=self.cmdopts,
                               cli_args=cli_args,
                               main_config=self.main_config,
                               norm_comp=self.norm_comp)
        else:
            BivarComparator()(controllers=self.controllers,
                              graph_config=self.stage5_config,
                              output_roots=self.output_roots,
                              cmdopts=self.cmdopts,
                              cli_args=cli_args,
                              main_config=self.main_config,
                              norm_comp=self.norm_comp)
        logging.info("Stage5: Inter-batch controller comparison complete")

    def __verify_controllers(self, controllers):
        """
        Verify that all controllers have run the same set of experiments before doing the
        comparison. If they have not, it is not `necessarily` an error, but probably should be
        looked at, so it is only a warning, not fatal.
        """
        for t1 in controllers:
            for t2 in controllers:
                for item in os.listdir(os.path.join(self.cmdopts['sierra_root'], t1)):
                    path1 = os.path.join(self.cmdopts['sierra_root'], t1, item,
                                         'exp-outputs',
                                         self.main_config['sierra']['collate_csv_leaf'])
                    path2 = os.path.join(self.cmdopts['sierra_root'], t2, item,
                                         'exp-outputs',
                                         self.main_config['sierra']['collate_csv_leaf'])
                    if os.path.isdir(path1) and not os.path.exists(path2):
                        print("WARN: {0} does not exist".format(path2))
                    if os.path.isdir(path2) and not os.path.exists(path1):
                        print("WARN: {0} does not exist".format(path1))
