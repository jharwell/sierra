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
Contains main class implementing stage 4 of the experimental pipeline.
"""

import os
import logging
import typing as tp
import time
import datetime

import yaml
import matplotlib as mpl

from core.pipeline.stage4.csv_collator import UnivarCSVCollator
from core.pipeline.stage4.csv_collator import BivarCSVCollator
from core.pipeline.stage4.intra_exp_graph_generator import BatchedIntraExpGraphGenerator
from core.pipeline.stage4.inter_exp_graph_generator import InterExpGraphGenerator
mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.rcParams['figure.max_open_warning'] = 10000
mpl.rcParams['axes.formatter.limits'] = (-4, 4)
mpl.use('Agg')


class PipelineStage4:
    """
    Implements stage 4 of the experimental pipeline.

    Generates graphs within single experiment (intra-experiment) and across experiments in a batch
    (inter-experiment). Graph generation controlled via YAML config files. This stage is
    idempotent.

    Attributes:
        cmdopts: Dictionary of parsed cmdline options.

        controller_config: YAML configuration file found in
                           ``<plugin_config_root>/controllers.yaml``. Contains configuration for
                           what categories of graphs should be generated for what controllers, for
                           all categories of graphs in both inter- and intra-experiment graph
                           generation.

        inter_LN_config: YAML configuration file found in
                         ``<plugin_config_root>/inter-graphs-line.yaml`` Contains configuration for
                         categories of linegraphs that can potentially be generated for all
                         controllers `across` experiments in a batch. Which linegraphs are actually
                         generated for a given controller is controlled by
                         ``<plugin_config_root>/controllers.yaml``.

        intra_LN_config: YAML configuration file found in
                         ``<plugin_config_root>/intra-graphs-line.yaml`` Contains configuration for
                         categories of linegraphs that can potentially be generated for all
                         controllers `within` each experiment in a batch. Which linegraphs are
                         actually generated for a given controller in each experiment is controlled
                         by ``<plugin_config_root>/controllers.yaml``.

        intra_HM_config: YAML configuration file found in
                         ``<plugin_config_root>/intra-graphs-hm.yaml`` Contains configuration for
                         categories of heatmaps that can potentially be generated for all
                         controllers `within` each experiment in a batch. Which heatmaps are
                         actually generated for a given controller in each experiment is controlled
                         by ``<plugin_config_root>/controllers.yaml``.

    """

    def __init__(self, main_config: dict, cmdopts: tp.Dict[str, str]):
        self.cmdopts = cmdopts

        self.main_config = main_config
        self.controller_config = yaml.load(open(os.path.join(self.cmdopts['plugin_config_root'],
                                                             'controllers.yaml')),
                                           yaml.FullLoader)

        self.inter_LN_config = yaml.load(open(os.path.join(self.cmdopts['core_config_root'],
                                                           'inter-graphs-line.yaml')),
                                         yaml.FullLoader)
        self.intra_LN_config = yaml.load(open(os.path.join(self.cmdopts['core_config_root'],
                                                           'intra-graphs-line.yaml')),
                                         yaml.FullLoader)
        self.intra_HM_config = yaml.load(open(os.path.join(self.cmdopts['core_config_root'],
                                                           'intra-graphs-hm.yaml')),
                                         yaml.FullLoader)

        plugin_inter_LN = os.path.join(self.cmdopts['plugin_config_root'],
                                       'inter-graphs-line.yaml')
        plugin_intra_LN = os.path.join(self.cmdopts['plugin_config_root'],
                                       'intra-graphs-line.yaml')
        plugin_intra_HM = os.path.join(self.cmdopts['plugin_config_root'],
                                       'intra-graphs-hm.yaml')
        if os.path.exists(plugin_intra_LN):
            logging.info("Stage4: Loading additional intra-experiment linegraph config for plugin '%s'",
                         self.cmdopts['plugin'])
            plugin_dict = yaml.load(open(plugin_intra_LN), yaml.FullLoader)

            for category in plugin_dict:
                if category not in self.intra_LN_config:
                    self.intra_LN_config.update({category: plugin_dict[category]})
                else:
                    self.intra_LN_config[category]['graphs'].extend(plugin_dict[category]['graphs'])

                self.intra_LN_config.update({category: plugin_dict[category]})

        if os.path.exists(plugin_intra_HM):
            logging.info("Stage4: Loading additional intra-experiment heatmap config for plugin '%s'",
                         self.cmdopts['plugin'])
            plugin_dict = yaml.load(open(plugin_intra_HM), yaml.FullLoader)
            for category in plugin_dict:
                if category not in self.intra_HM_config:
                    self.intra_HM_config.update({category: plugin_dict[category]})
                else:
                    self.intra_HM_config[category]['graphs'].extend(plugin_dict[category]['graphs'])

        if os.path.exists(plugin_inter_LN):
            logging.info("Stage4: Loading additional inter-experiment linegraph config for plugin '%s'",
                         self.cmdopts['plugin'])
            plugin_dict = yaml.load(open(plugin_inter_LN), yaml.FullLoader)
            for category in plugin_dict:
                if category not in self.inter_LN_config:
                    self.inter_LN_config.update({category: plugin_dict[category]})
                else:
                    self.inter_LN_config[category]['graphs'].extend(plugin_dict[category]['graphs'])

    def run(self, batch_criteria):
        """
        Runs intra-experiment graph generation, ``.csv`` collation for inter-experiment graph
        generation, and inter-experiment graph generation, as configured on the cmdline.

        Intra-experiment graph generation: if intra-experiment graphs should be generated,
        according to cmdline configuration, the following is run:

        #. :class:`pipeline.stage4.BatchedIntraExpGraphGenerator` to generate graphs for each
           experiment in the batch.

        Inter-experiment graph generation: if inter-experiment graphs should be generated according
        to cmdline configuration, the following is run:

        #. :class:`~pipeline.stage4.UnivarCSVCollator` or :class:`~pipeline.stage4.BivarCSVCollator`
           as appropriate (depending on which type of
           :class:`~variables.batch_criteria.BatchCriteria` was specified on the cmdline).

        #. :class:`~pipeline.stage4.InterExpGraphGenerator` to perform graph generation from
           collated ``.csv`` files.
        """
        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'intra':
            logging.info("Stage4: Generating intra-experiment graphs...")
            start = time.time()
            BatchedIntraExpGraphGenerator(self.cmdopts)(self.main_config,
                                                        self.controller_config,
                                                        self.intra_LN_config,
                                                        self.intra_HM_config,
                                                        batch_criteria)
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            logging.info("Stage4: Intra-experiment graph generation complete: %s", str(sec))

        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'inter':
            # Collation must be after intra-experiment graph generation, so that all .csv files to
            # be collated have been generated/modified according to parameters.
            targets = self.__calc_inter_LN_targets()
            if batch_criteria.is_univar():
                UnivarCSVCollator(self.main_config, self.cmdopts)(batch_criteria, targets)
            else:
                BivarCSVCollator(self.main_config, self.cmdopts)(batch_criteria, targets)

            logging.info("Stage4: Generating inter-experiment graphs...")
            start = time.time()
            InterExpGraphGenerator(self.main_config, self.cmdopts, targets)(batch_criteria)
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            logging.info("Stage4: Inter-experiment graph generation complete: %s", str(sec))

    def __calc_inter_LN_targets(self):
        """
        Use YAML configuration for controllers and inter-experiment graphs to what ``.csv`` files
        need to be collated/what graphs should be generated.
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

        filtered_keys = [k for k in self.inter_LN_config if k in keys]
        targets = [self.inter_LN_config[k] for k in filtered_keys]
        targets.append({'graphs': extra_graphs})

        logging.debug("Enabled linegraph categories: %s", filtered_keys)
        return targets
