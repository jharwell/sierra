# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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
"""
Classes for generating graphs within a single experiment in a batch.
"""

import os
import copy
import logging
import typing as tp

from core.graphs.stacked_line_graph import StackedLineGraph
from core.graphs.heatmap import Heatmap
from core.pipeline.stage4.flexibility_plots import FlexibilityPlotsCSVGenerator, FlexibilityPlotsDefinitionsGenerator
import core.utils


class BatchedIntraExpGraphGenerator:
    """
    Generates all intra-experiment graphs from a batch of experiments.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.
    """

    def __init__(self, cmdopts: dict) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)

    def __call__(self,
                 main_config: dict,
                 controller_config: dict,
                 LN_config: dict,
                 HM_config: dict,
                 batch_criteria):
        """
        Generate all intra-experiment graphs for all experiments in the batch.
        """
        exp_to_gen = core.utils.exp_range_calc(self.cmdopts,
                                               self.cmdopts['batch_output_root'],
                                               batch_criteria)

        for exp in exp_to_gen:
            exp = os.path.split(exp)[1]
            cmdopts = copy.deepcopy(self.cmdopts)
            cmdopts["exp_input_root"] = os.path.join(self.cmdopts['batch_input_root'], exp)
            cmdopts["exp_output_root"] = os.path.join(self.cmdopts['batch_output_root'], exp)
            cmdopts["exp_graph_root"] = os.path.join(self.cmdopts['batch_graph_root'], exp)

            if os.path.isdir(cmdopts["exp_output_root"]) and main_config['sierra']['collate_csv_leaf'] != exp:
                IntraExpGraphGenerator(main_config,
                                       controller_config,
                                       LN_config,
                                       HM_config,
                                       cmdopts)(batch_criteria)


class IntraExpGraphGenerator:
    """
    Generates graphs from averaged output data within a single experiment in a batch. Which graphs
    are generated is controlled by YAML configuration files parsed in
    :class:`~core.pipeline.stage4.pipeline_stage4.PipelineStage4`.
    """

    def __init__(self,
                 main_config: dict,
                 controller_config: dict,
                 LN_config: dict,
                 HM_config: dict,
                 cmdopts: dict) -> None:
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.LN_config = LN_config
        self.HM_config = HM_config
        self.controller_config = controller_config

        self.exp_avgd_root = os.path.join(self.cmdopts["exp_output_root"],
                                          self.main_config['sierra']['avg_output_leaf'])
        self.exp_model_root = os.path.join(self.cmdopts["exp_output_root"],
                                           'models')

        core.utils.dir_create_checked(self.cmdopts["exp_graph_root"], exist_ok=True)

    def __call__(self, batch_criteria):
        """
        Runs the following to generate graphs for each experiment in the batch:

        #. :class:`~core.pipeline.stage4.intra_exp_graph_generator.LinegraphsGenerator` to
           generate linegraphs for each experiment in the batch.

        #. :class:`~core.pipeline.stage4.intra_exp_graph_generator.HeatmapsGenerator` to
           generate heatmaps for each experiment in the batch.
        """
        if self.cmdopts['gen_vc_plots'] and batch_criteria.is_univar():
            logging.info('Flexibility plots from %s', self.cmdopts['exp_output_root'])
            FlexibilityPlotsCSVGenerator(self.main_config, self.cmdopts)(batch_criteria)

        LN_targets, HM_targets = self.__calc_intra_targets()

        LinegraphsGenerator(self.exp_avgd_root,
                            self.cmdopts["exp_graph_root"],
                            self.exp_model_root,
                            LN_targets).generate()

        HeatmapsGenerator(self.exp_avgd_root,
                          self.cmdopts["exp_graph_root"],
                          HM_targets).generate()

    def __calc_intra_targets(self):
        """
        Use YAML configuration for controller the controller and intra-experiment graphs to
        calculate what graphs should be generated.
        """
        keys = []
        extra_graphs = []
        for category in list(self.controller_config.keys()):
            if category not in self.cmdopts['controller']:
                continue
            for controller in self.controller_config[category]['controllers']:
                if controller['name'] not in self.cmdopts['controller']:
                    continue

                # valid to specify no graphs, and only to inherit graphs
                keys = controller.get('graphs', [])
                if 'graphs_inherit' in controller:
                    for inherit in controller['graphs_inherit']:
                        keys.extend(inherit)   # optional
                if self.cmdopts['gen_vc_plots']:  # optional
                    extra_graphs = FlexibilityPlotsDefinitionsGenerator()()

        LN_keys = [k for k in self.LN_config if k in keys]
        logging.debug("Enabled linegraph categories: %s", LN_keys)

        HM_keys = [k for k in self.HM_config if k in keys]
        logging.debug("Enabled heatmap categories: %s", HM_keys)

        LN_targets = [self.LN_config[k] for k in LN_keys]
        LN_targets.append({'graphs': extra_graphs})
        HM_targets = [self.HM_config[k] for k in HM_keys]

        return LN_targets, HM_targets


class HeatmapsGenerator:
    """
    Generates heatmaps from averaged output data within a single experiment.

    Attributes:
        avgd_output_root: Absolute path to root directory for experiment simulation outputs.
        targets: Dictionary of lists of dictionaries specifying what graphs should be
                 generated.
    """

    def __init__(self, exp_avgd_root: str, exp_graph_root: str, targets: list) -> None:

        self.exp_avgd_root = exp_avgd_root
        self.exp_graph_root = exp_graph_root
        self.targets = targets

    def generate(self):
        logging.info("Heatmaps from %s", self.exp_avgd_root)

        # For each category of heatmaps we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                Heatmap(input_fpath=os.path.join(self.exp_avgd_root,
                                                 graph['src_stem'] + '.csv'),
                        output_fpath=os.path.join(self.exp_graph_root,
                                                  graph['src_stem'] + '-hm.png'),
                        title=graph['title'],
                        xlabel='X',
                        ylabel='Y').generate()


class LinegraphsGenerator:
    """
    Generates linegraphs from averaged output data within a single experiment.

    Attributes:
        exp_avgd_root: Absolute path to experiment simulation output directory.
        exp_graph_root: Absolute path to experiment graph output directory.
        targets: Dictionary of lists of dictionaries specifying what graphs should be
                 generated.
    """

    def __init__(self,
                 exp_avgd_root: str,
                 exp_graph_root: str,
                 exp_model_root: str,
                 targets: list) -> None:

        self.exp_avgd_root = exp_avgd_root
        self.exp_graph_root = exp_graph_root
        self.exp_model_root = exp_model_root
        self.targets = targets

    def generate(self):
        logging.info("Linegraphs from %s", self.exp_avgd_root)

        # For each category of linegraphs we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                output_fpath = os.path.join(self.exp_graph_root,
                                            graph['dest_stem'] + '.png')
                try:
                    StackedLineGraph(input_csv_fpath=os.path.join(self.exp_avgd_root,
                                                                  graph['src_stem'] + '.csv'),
                                     input_stddev_fpath=os.path.join(self.exp_avgd_root,
                                                                     graph['src_stem'] + '.stddev'),
                                     input_model_fpath=os.path.join(self.exp_model_root,
                                                                    graph['dest_stem'] + '.model'),
                                     output_fpath=output_fpath,
                                     cols=graph['cols'],
                                     title=graph['title'],
                                     legend=graph['legend'],
                                     xlabel=graph['xlabel'],
                                     ylabel=graph['ylabel'],
                                     linestyles=graph.get('styles', None),
                                     dashes=graph.get('dashes', None)).generate()
                except KeyError:
                    raise KeyError('Check that the generated {0}.csv file contains the columns {1}'.format(
                        graph['src_stem'],
                        graph['cols']))


__api__ = ['BatchedIntraExpGraphGenerator',
           'IntraExpGraphGenerator',
           'LinegraphsGenerator',
           'HeatmapsGenerator']
