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

# Core packages
import os
import logging
import typing as tp
import time
import datetime

# 3rd party packages
import yaml
import matplotlib as mpl

# Project packages
from core.pipeline.stage4.graph_collator import MultithreadCollator
from core.pipeline.stage4.intra_exp_graph_generator import BatchedIntraExpGraphGenerator
from core.pipeline.stage4.exp_model_runner import BatchedIntraExpModelRunner
from core.pipeline.stage4.exp_model_runner import InterExpModelRunner

from core.pipeline.stage4.inter_exp_graph_generator import InterExpGraphGenerator
from core.pipeline.stage4.exp_video_renderer import BatchedExpVideoRenderer
import core.plugin_manager

mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.rcParams['figure.max_open_warning'] = 10000
mpl.rcParams['axes.formatter.limits'] = (-4, 4)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
mpl.use('Agg')


class PipelineStage4:
    """
    Implements stage 4 of the experimental pipeline.

    Generates end-result experimental deliverables within single experiment (intra-experiment) and
    across experiments in a batch (inter-experiment) according to configuration. Currently this
    includes:

    - Graph generation controlled via YAML config files.
    - Video rendering controlled via YAML config files.


    This stage is idempotent.

    Attributes:
        cmdopts: Dictionary of parsed cmdline options.

        controller_config: YAML configuration file found in
                           ``<project_config_root>/controllers.yaml``. Contains configuration for
                           what categories of graphs should be generated for what controllers, for
                           all categories of graphs in both inter- and intra-experiment graph
                           generation.

        inter_LN_config: YAML configuration file found in
                         ``<project_config_root>/inter-graphs-line.yaml`` Contains configuration for
                         categories of linegraphs that can potentially be generated for all
                         controllers `across` experiments in a batch. Which linegraphs are actually
                         generated for a given controller is controlled by
                         ``<project_config_root>/controllers.yaml``.

        intra_LN_config: YAML configuration file found in
                         ``<project_config_root>/intra-graphs-line.yaml`` Contains configuration for
                         categories of linegraphs that can potentially be generated for all
                         controllers `within` each experiment in a batch. Which linegraphs are
                         actually generated for a given controller in each experiment is controlled
                         by ``<project_config_root>/controllers.yaml``.

        intra_HM_config: YAML configuration file found in
                         ``<project_config_root>/intra-graphs-hm.yaml`` Contains configuration for
                         categories of heatmaps that can potentially be generated for all
                         controllers `within` each experiment in a batch. Which heatmaps are
                         actually generated for a given controller in each experiment is controlled
                         by ``<project_config_root>/controllers.yaml``.

    """

    def __init__(self, main_config: dict, cmdopts: dict) -> None:
        self.cmdopts = cmdopts

        self.main_config = main_config
        self.controller_config = yaml.load(open(os.path.join(self.cmdopts['project_config_root'],
                                                             'controllers.yaml')),
                                           yaml.FullLoader)
        self.logger = logging.getLogger(__name__)
        self._load_LN_config()
        self._load_HM_config()
        self._load_models()

    def run(self, batch_criteria):
        """
        Runs simulation deliverable generation, ``.csv`` collation for inter-experiment graph
        generation, and inter-experiment graph generation, as configured on the cmdline.

        Video generation: If images have previously been created, then the following is run:

        #. :class:`~core.pipeline.stage4.exp_video_renderer.BatchedExpVideoRenderer` to render
           videos for each experiment in the batch, or a subset.

        Intra-experiment graph generation: if intra-experiment graphs should be generated,
        according to cmdline configuration, the following is run:

        #. Model generation for each enabled and loaded model.

        #. :class:`~core.pipeline.stage4.intra_exp_graph_generator.BatchedIntraExpGraphGenerator` to
           generate graphs for each experiment in the batch, or a subset.


        Inter-experiment graph generation: if inter-experiment graphs should be generated according
        to cmdline configuration, the following is run:

        #. :class:`~core.pipeline.stage4.graph_collator.UnivarGraphCollator` or
           :class:`~core.pipeline.stage4.graph_collator.BivarGraphCollator` as appropriate
           (depending on which type of :class:`~core.variables.batch_criteria.BatchCriteria` was
           specified on the cmdline).

        #. Model generation for each enabled and loaded model.

        #. :class:`~core.pipeline.stage4.inter_exp_graph_generator.InterExpGraphGenerator`
           to perform graph generation from collated ``.csv`` files.
        """
        if self.cmdopts['project_rendering'] or self.cmdopts['argos_rendering']:
            self._run_rendering()

        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'intra':
            if len(self.models_intra) > 0 and not self.cmdopts['models_disable']:
                self._run_intra_models(batch_criteria)

            self._run_intra_graph_generation(batch_criteria)

        # Collation must be after intra-experiment graph generation, so that all .csv files to
        # be collated have been generated/modified according to parameters.
        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'inter':
            self._run_collation(batch_criteria)

            if len(self.models_inter) > 0 and not self.cmdopts['models_disable']:
                self._run_inter_models(batch_criteria)

            self._run_inter_graph_generation(batch_criteria)

    def _load_models(self):
        project_models = os.path.join(self.cmdopts['project_config_root'], 'models.yaml')
        self.models_intra = []
        self.models_inter = []

        if not core.utils.path_exists(project_models):
            return

        self.logger.info("Loading models for project '%s'", self.cmdopts['project'])

        self.models_config = yaml.load(open(project_models), yaml.FullLoader)
        pm = core.plugin_manager.ModelPluginManager()
        pm.initialize(os.path.join(self.cmdopts['project_model_root']))

        # All models present in the .yaml file are enabled/set to run unconditionally
        for module_name in pm.available_plugins():
            # No models specified--nothing to do
            if self.models_config.get('models') is None or self.models_config['models'] is None:
                continue

            for conf in self.models_config['models']:
                if conf['pyfile'] == module_name:
                    module = pm.load_plugin(module_name)
                    for avail in module.available_models('intra'):
                        model = getattr(module, avail)(self.main_config, conf)
                        self.models_intra.append(model)
                    for avail in module.available_models('inter'):
                        model = getattr(module, avail)(self.main_config, conf)
                        self.models_inter.append(model)

        if len(self.models_intra) > 0:
            self.logger.info("Loaded %s intra-experiment models for project '%s'",
                             len(self.models_intra),
                             self.cmdopts['project'])

        if len(self.models_inter) > 0:
            self.logger.info("Loaded %s inter-experiment models for project '%s'",
                             len(self.models_inter),
                             self.cmdopts['project'])

    def _load_LN_config(self):
        self.inter_LN_config = yaml.load(open(os.path.join(self.cmdopts['core_config_root'],
                                                           'inter-graphs-line.yaml')),
                                         yaml.FullLoader)
        self.intra_LN_config = yaml.load(open(os.path.join(self.cmdopts['core_config_root'],
                                                           'intra-graphs-line.yaml')),
                                         yaml.FullLoader)
        project_inter_LN = os.path.join(self.cmdopts['project_config_root'],
                                        'inter-graphs-line.yaml')
        project_intra_LN = os.path.join(self.cmdopts['project_config_root'],
                                        'intra-graphs-line.yaml')

        if core.utils.path_exists(project_intra_LN):
            self.logger.info("Loading additional intra-experiment linegraph config for project '%s'",
                             self.cmdopts['project'])
            project_dict = yaml.load(open(project_intra_LN), yaml.FullLoader)

            for category in project_dict:
                if category not in self.intra_LN_config:
                    self.intra_LN_config.update({category: project_dict[category]})
                else:
                    self.intra_LN_config[category]['graphs'].extend(
                        project_dict[category]['graphs'])

                self.intra_LN_config.update({category: project_dict[category]})

        if core.utils.path_exists(project_inter_LN):
            self.logger.info("Loading additional inter-experiment linegraph config for project '%s'",
                             self.cmdopts['project'])
            project_dict = yaml.load(open(project_inter_LN), yaml.FullLoader)
            for category in project_dict:
                if category not in self.inter_LN_config:
                    self.inter_LN_config.update({category: project_dict[category]})
                else:
                    self.inter_LN_config[category]['graphs'].extend(
                        project_dict[category]['graphs'])

    def _load_HM_config(self):
        self.intra_HM_config = yaml.load(open(os.path.join(self.cmdopts['core_config_root'],
                                                           'intra-graphs-hm.yaml')),
                                         yaml.FullLoader)

        project_intra_HM = os.path.join(self.cmdopts['project_config_root'],
                                        'intra-graphs-hm.yaml')

        if core.utils.path_exists(project_intra_HM):
            self.logger.info("Loading additional intra-experiment heatmap config for project '%s'",
                             self.cmdopts['project'])
            project_dict = yaml.load(open(project_intra_HM), yaml.FullLoader)
            for category in project_dict:
                if category not in self.intra_HM_config:
                    self.intra_HM_config.update({category: project_dict[category]})
                else:
                    self.intra_HM_config[category]['graphs'].extend(
                        project_dict[category]['graphs'])

    def _calc_inter_LN_targets(self):
        """
        Use YAML configuration for controllers and inter-experiment graphs to what ``.csv`` files
        need to be collated/what graphs should be generated.
        """
        keys = []
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

        filtered_keys = [k for k in self.inter_LN_config if k in keys]
        targets = [self.inter_LN_config[k] for k in filtered_keys]

        self.logger.debug("Enabled linegraph categories: %s", filtered_keys)
        return targets

    def _run_rendering(self):
        """
        Render captured ARGoS frames and/or frames created by imagizing in stage 3 into videos.
        """
        render_opts = {
            'cmd_opts': self.cmdopts['render_cmd_opts'],
            'argos_rendering': self.cmdopts['argos_rendering'],
            'project_rendering': self.cmdopts['project_rendering']
        }
        self.logger.info("Rendering videos...")
        start = time.time()
        BatchedExpVideoRenderer()(self.main_config, render_opts, self.cmdopts['batch_output_root'])
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Rendering complete in %s", str(sec))

    def _run_intra_models(self, batch_criteria):
        self.logger.info("Running intra-experiment models...")
        start = time.time()
        BatchedIntraExpModelRunner(self.cmdopts,
                                   self.models_intra)(self.main_config,
                                                      batch_criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Intra-experiment models finished in %s", str(sec))

    def _run_inter_models(self, batch_criteria):
        self.logger.info("Running inter-experiment models...")
        start = time.time()
        InterExpModelRunner(self.cmdopts,
                            self.models_inter)(self.main_config,
                                               batch_criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Inter-experiment models finished in %s", str(sec))

    def _run_intra_graph_generation(self, batch_criteria):
        """
        Generate intra-experiment graphs (duh).
        """
        self.logger.info("Generating intra-experiment graphs...")
        start = time.time()
        BatchedIntraExpGraphGenerator(self.cmdopts)(self.main_config,
                                                    self.controller_config,
                                                    self.intra_LN_config,
                                                    self.intra_HM_config,
                                                    batch_criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Intra-experiment graph generation complete: %s", str(sec))

    def _run_collation(self, batch_criteria):
        targets = self._calc_inter_LN_targets()

        if not self.cmdopts['no_collate']:
            self.logger.info("Collating inter-experiment .csv files...")
            start = time.time()
            MultithreadCollator(self.main_config, self.cmdopts)(batch_criteria, targets)
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            self.logger.info("Collating inter-experiment .csv files complete: %s", str(sec))

    def _run_inter_graph_generation(self, batch_criteria):
        """
        Generate inter-experiment graphs (duh).
        """
        targets = self._calc_inter_LN_targets()

        self.logger.info("Generating inter-experiment graphs...")
        start = time.time()
        InterExpGraphGenerator(self.main_config, self.cmdopts, targets)(batch_criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Inter-experiment graph generation complete: %s", str(sec))


__api__ = [
    'PipelineStage4'


]
