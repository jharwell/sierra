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

"""
Contains main class implementing stage 5 of the experimental pipeline.
"""

import os
import typing as tp
import logging
import yaml

from core.pipeline.stage5 import intra_scenario_comparator as isc
import core.root_dirpath_generator as rdg

import core.utils


class PipelineStage5:
    """
    Implements stage5 of the experimental pipeline: comparing controllers that have been tested with
    the same batch criteria using different performance measures within the same scenario, according
    to YAML configuration. This stage is idempotent.

    Attributes:
        cmdopts: Dictionary of parsed cmdline parameters.
        controllers: List of controllers to compare.
        main_config: Dictionary of parsed main YAML configuration.
        stage5_config: Dictionary of parsed stage5 YAML configuration.
        output_roots: Dictionary containing output directories for intra- and inter-scenario graph
                      generation.
    """

    def __init__(self, main_config: dict, cmdopts: tp.Dict[str, str]) -> None:
        self.cmdopts = cmdopts
        self.main_config = main_config
        self.stage5_config = yaml.load(open(os.path.join(self.cmdopts['project_config_root'],
                                                         'stage5.yaml')),
                                       yaml.FullLoader)
        self.controllers = self.cmdopts['controllers_list'].split(',')

        # We add the controller list to the directory path for the .csv and graph directories so
        # that multiple runs of stage5 with different controllers do not overwrite each other
        # (i.e. make stage5 idempotent).
        self.output_roots = {
            'cc_graphs': os.path.join(self.cmdopts['sierra_root'],
                                      self.cmdopts['project'],
                                      '+'.join(self.controllers) + "-cc-graphs"),
            'cc_csvs': os.path.join(self.cmdopts['sierra_root'],
                                    self.cmdopts['project'],
                                    '+'.join(self.controllers) + "-cc-csvs"),
        }

    def run(self, cli_args):
        """
        Runs :class:`UnivarIntraScenarioComparator` or :class:`BivarIntraScenarioComparator` as
        appropriate, depending on which type of
        :class:`~core.variables.batch_criteria.BatchCriteria` was selected on the cmdline.
        """
        # Create directories for controller .csv files and graphs
        for v in self.output_roots.values():
            core.utils.dir_create_checked(v, True)

        # Use nice controller names on graph legends if configured
        if self.cmdopts['controllers_legend'] is not None:
            legend = self.cmdopts['controllers_legend'].split(',')
        else:
            legend = self.controllers

        self.__verify_controllers(self.controllers, cli_args)

        logging.info("Stage5: Inter-batch controller comparison of %s...", self.controllers)

        if cli_args.bc_univar:
            comparator = isc.UnivarIntraScenarioComparator(
                self.controllers,
                self.output_roots['cc_csvs'],
                self.output_roots['cc_graphs'],
                self.cmdopts,
                cli_args,
                self.main_config)
        else:
            comparator = isc.BivarIntraScenarioComparator(
                self.controllers,
                self.output_roots['cc_csvs'],
                self.output_roots['cc_graphs'],
                self.cmdopts,
                cli_args,
                self.main_config)

        comparator(graphs=self.stage5_config['intra_scenario']['graphs'],
                   legend=legend,
                   comp_type=self.cmdopts['comparison_type'])

        logging.info("Stage5: Inter-batch controller comparison complete")

    def __verify_controllers(self, controllers, cli_args):
        """
        Verify that all controllers have run the same set of experiments before doing the
        comparison. If they have not, it is not `necessarily` an error, but probably should be
        looked at, so it is only a warning, not fatal.
        """
        for t1 in controllers:
            for item in os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                                self.cmdopts['project'],
                                                t1)):
                template_stem, scenario, _ = rdg.parse_batch_leaf(item)
                batch_leaf = rdg.gen_batch_leaf(cli_args.batch_criteria,
                                                template_stem,
                                                scenario)

                for t2 in controllers:
                    opts1 = rdg.regen_from_exp(sierra_rpath=self.cmdopts['sierra_root'],
                                               project=self.cmdopts['project'],
                                               batch_leaf=batch_leaf,
                                               controller=t1)
                    opts2 = rdg.regen_from_exp(sierra_rpath=self.cmdopts['sierra_root'],
                                               project=self.cmdopts['project'],
                                               batch_leaf=batch_leaf,
                                               controller=t2)
                    collate_root1 = os.path.join(opts1['output_root'],
                                                 self.main_config['sierra']['collate_csv_leaf'])
                    collate_root2 = os.path.join(opts2['output_root'],
                                                 self.main_config['sierra']['collate_csv_leaf'])

                    if scenario in collate_root1 and scenario not in collate_root2:
                        logging.warning("%s does not exist in %s", scenario, collate_root2)
                    if scenario in collate_root2 and scenario not in collate_root1:
                        logging.warning("%s does not exist in %s", scenario, collate_root1)


__api__ = [
    'PipelineStage5'
]
