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

from graphs.stacked_line_graph import StackedLineGraph
from graphs.heatmap import Heatmap
from .temporal_variance_plot_defs import TemporalVariancePlotDefs


class BatchedIntraExpGraphGenerator:
    """
    Generates all intra-experiment graphs from a batch of experiments.

    Attributes:
        cmdopts: Dictionary of parsed cmdline attributes.
    """

    def __init__(self, cmdopts: tp.Dict[str, str]):
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
        batch_output_root = self.cmdopts["output_root"]
        batch_graph_root = self.cmdopts["graph_root"]
        batch_generation_root = self.cmdopts['generation_root']

        for item in os.listdir(batch_output_root):

            # Roots need to be modified for each experiment for correct behavior
            self.cmdopts["generation_root"] = os.path.join(batch_generation_root, item)
            self.cmdopts["output_root"] = os.path.join(batch_output_root, item)
            self.cmdopts["graph_root"] = os.path.join(batch_graph_root, item)

            if os.path.isdir(self.cmdopts["output_root"]) and main_config['sierra']['collate_csv_leaf'] != item:
                IntraExpGraphGenerator(main_config,
                                       controller_config,
                                       LN_config,
                                       HM_config,
                                       self.cmdopts)(batch_criteria)


class IntraExpGraphGenerator:
    """
    Generates graphs from averaged output data within a single experiment in a batch. Which graphs
    are generated is controlled by YAML configuration files parsed in
    :class:`~pipeline.stage4.PipelineStage4`.
    """

    def __init__(self,
                 main_config: dict,
                 controller_config: dict,
                 LN_config: dict,
                 HM_config: dict,
                 cmdopts: tp.Dict[str, str]):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config
        self.LN_config = LN_config
        self.HM_config = HM_config
        self.controller_config = controller_config

        self.cmdopts["output_root"] = os.path.join(self.cmdopts["output_root"],
                                                   self.main_config['sierra']['avg_output_leaf'])

        os.makedirs(self.cmdopts["graph_root"], exist_ok=True)

    def __call__(self, batch_criteria):
        """
        Runs the following to generate graphs for each experiment in the batch:

        #. :class:`~pipeline.stage4.intra_exp_graph_generator.LinegraphsGenerator` to generate
           linegraphs for each experiment in the batch.

        #. :class:`~pipeline.stage4.intra_exp_graph_generator.HeatmapsGenerator` to generate
           heatmaps for each experiment in the batch.
        """
        LN_targets, HM_targets = self.__calc_intra_targets(batch_criteria)

        LinegraphsGenerator(self.cmdopts["output_root"],
                            self.cmdopts["graph_root"],
                            LN_targets).generate()

        HeatmapsGenerator(self.cmdopts["output_root"],
                          self.cmdopts["graph_root"],
                          HM_targets).generate()

    def __calc_intra_targets(self, batch_criteria):
        """
        Use YAML configuration for controllers and intra-experiment graphs to what graphs should be
        generated.
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
                    [keys.extend(l) for l in controller['graphs_inherit']]  # optional
                if self.cmdopts['gen_vc_plots']:  # optional
                    extra_graphs = TemporalVariancePlotDefs(self.cmdopts)(batch_criteria,
                                                                          self.main_config)

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
        exp_output_root: Absolute path to root directory for experiment simulation outputs.
        exp_output_root: Absolute path to root directory for experiment graph outputs.
        targets: Dictionary of lists of dictionaries specifying what graphs should be
                 generated.
    """

    def __init__(self, exp_output_root: str, exp_graph_root: str, targets: list):

        self.exp_output_root = exp_output_root
        self.exp_graph_root = exp_graph_root
        self.targets = targets

    def generate(self):
        logging.info("Heatmaps from %s", self.exp_output_root)

        # For each category of heatmaps we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                Heatmap(input_fpath=os.path.join(self.exp_output_root,
                                                 graph['src_stem'] + '.csv'),
                        output_fpath=os.path.join(self.exp_graph_root,
                                                  graph['src_stem'] + '-hm.png'),
                        title=graph['title'],
                        xlabel='Y',
                        ylabel='X',
                        xtick_labels=None,
                        ytick_labels=None).generate()


class LinegraphsGenerator:
    """
    Generates linegrahs from averaged output data within a single experiment.

    Attributes:
        exp_output_root: Absolute path to experiment simulation output directory.
        exp_graph_root: Absolutae path to experiment graph output directory.
        targets: Dictionary of lists of dictiaries specifying what graphs should be
                 generated.
    """

    def __init__(self, exp_output_root: str, exp_graph_root: str, targets: list):

        self.exp_output_root = exp_output_root
        self.exp_graph_root = exp_graph_root
        self.targets = targets

    def generate(self):
        logging.info("Linegraphs from %s", self.exp_output_root)

        # For each category of linegraphs we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                output_fpath = os.path.join(self.exp_graph_root,
                                            graph['dest_stem'] + '.png')
                try:
                    StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root,
                                                                   graph['src_stem']),
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
