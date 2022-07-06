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
Classes for implementing stage 4 of the experimental pipeline: generating
deliverables.
"""

# Core packages
import os
import typing as tp
import time
import datetime
import logging

# 3rd party packages
import yaml

# Project packages
from sierra.core.pipeline.stage4.graph_collator import GraphParallelCollator
from sierra.core.pipeline.stage4.intra_exp_graph_generator import BatchIntraExpGraphGenerator
from sierra.core.pipeline.stage4.model_runner import IntraExpModelRunner
from sierra.core.pipeline.stage4.model_runner import InterExpModelRunner
import sierra.core.variables.batch_criteria as bc

from sierra.core.pipeline.stage4.video_renderer import BatchExpParallelVideoRenderer
import sierra.core.plugin_manager as pm
from sierra.core import types, config, utils


class PipelineStage4:
    """Generates end-result experimental deliverables within single experiment
    (intra-experiment) and across experiments in a batch (inter-experiment).

    Currently this includes:

    - Graph generation controlled via YAML config files.

    - Video rendering controlled via YAML config files.

    This stage is idempotent.

    Attributes:
        cmdopts: Dictionary of parsed cmdline options.

        controller_config: YAML configuration file found in
                           ``<project_config_root>/controllers.yaml``. Contains
                           configuration for what categories of graphs should be
                           generated for what controllers, for all categories of
                           graphs in both inter- and intra-experiment graph
                           generation.

        inter_LN_config: YAML configuration file found in
                         ``<project_config_root>/inter-graphs-line.yaml``
                         Contains configuration for categories of linegraphs
                         that can potentially be generated for all controllers
                         `across` experiments in a batch. Which linegraphs are
                         actually generated for a given controller is controlled
                         by ``<project_config_root>/controllers.yaml``.

        intra_LN_config: YAML configuration file found in
                         ``<project_config_root>/intra-graphs-line.yaml``
                         Contains configuration for categories of linegraphs
                         that can potentially be generated for all controllers
                         `within` each experiment in a batch. Which linegraphs
                         are actually generated for a given controller in each
                         experiment is controlled by
                         ``<project_config_root>/controllers.yaml``.

        intra_HM_config: YAML configuration file found in
                         ``<project_config_root>/intra-graphs-hm.yaml`` Contains
                         configuration for categories of heatmaps that can
                         potentially be generated for all controllers `within`
                         each experiment in a batch. Which heatmaps are actually
                         generated for a given controller in each experiment is
                         controlled by
                         ``<project_config_root>/controllers.yaml``.

    """

    def __init__(self,
                 main_config: types.YAMLDict,
                 cmdopts: types.Cmdopts) -> None:
        self.cmdopts = cmdopts

        self.main_config = main_config
        with open(os.path.join(self.cmdopts['project_config_root'],
                               config.kYAML['controllers'])) as f:
            self.controller_config = yaml.load(f, yaml.FullLoader)
        self.logger = logging.getLogger(__name__)

        # Load YAML config
        loader = pm.module_load_tiered(project=self.cmdopts['project'],
                                       path='pipeline.stage4.yaml_config_loader')
        graphs_config = loader.YAMLConfigLoader()(self.cmdopts)
        self.intra_LN_config = graphs_config['intra_LN']
        self.intra_HM_config = graphs_config['intra_HM']
        self.inter_LN_config = graphs_config['inter_LN']

        if self.cmdopts['models_enable']:
            self._load_models()

    def run(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """Runs experiment deliverable generation, CSV collation for
        inter-experiment graph generation, and inter-experiment graph
        generation.

        Video generation: If images have previously been created, then the
        following is run:

        #. :class:`~sierra.core.pipeline.stage4.video_renderer.BatchExpParallelVideoRenderer`
           to render videos for each experiment in the batch, or a subset.

        Intra-experiment graph generation: if intra-experiment graphs should be
        generated, according to cmdline configuration, the following is run:

        #. Model generation for each enabled and loaded model.

        #. :class:`~sierra.core.pipeline.stage4.intra_exp_graph_generator.BatchIntraExpGraphGenerator`
           to generate graphs for each experiment in the batch, or a subset.

        Inter-experiment graph generation: if inter-experiment graphs should be
        generated according to cmdline configuration, the following is run:

        #. :class:`~sierra.core.pipeline.stage4.graph_collator.UnivarGraphCollator`
           or
           :class:`~sierra.core.pipeline.stage4.graph_collator.BivarGraphCollator`
           as appropriate (depending on which type of
           :class:`~sierra.core.variables.batch_criteria.BatchCriteria` was
           specified on the cmdline).

        #. Model generation for each enabled and loaded model.

        #. :class:`~sierra.core.pipeline.stage4.inter_exp_graph_generator.InterExpGraphGenerator`
           to perform graph generation from collated CSV files.

        """
        if self.cmdopts['project_rendering'] or self.cmdopts['platform_vc']:
            self._run_rendering(criteria)

        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'intra':
            if criteria.is_univar() and self.cmdopts['models_enable']:
                self._run_intra_models(criteria)

            self._run_intra_graph_generation(criteria)

        # Collation must be after intra-experiment graph generation, so that all
        # .csv files to be collated have been generated/modified according to
        # parameters.
        if self.cmdopts['exp_graphs'] == 'all' or self.cmdopts['exp_graphs'] == 'inter':
            self._run_collation(criteria)

            if criteria.is_univar() and self.cmdopts['models_enable']:
                self._run_inter_models(criteria)

            self._run_inter_graph_generation(criteria)

    def _load_models(self) -> None:
        project_models = os.path.join(self.cmdopts['project_config_root'],
                                      'models.yaml')
        self.models_intra = []
        self.models_inter = []

        if not utils.path_exists(project_models):
            self.logger.debug("No models to load for project '%s': %s does not exist",
                              self.cmdopts['project'],
                              project_models)
            return

        self.logger.info("Loading models for project '%s'",
                         self.cmdopts['project'])

        self.models_config = yaml.load(open(project_models), yaml.FullLoader)
        pm.models.initialize(self.cmdopts['project'],
                             self.cmdopts['project_model_root'])

        # All models present in the .yaml file are enabled/set to run
        # unconditionally
        available = pm.models.available_plugins()
        self.logger.debug("Project %s has %d available model plugins",
                          self.cmdopts['project'],
                          len(available))

        for module_name in pm.models.available_plugins():
            # No models specified--nothing to do
            if self.models_config.get('models') is None:
                continue

            for conf in self.models_config['models']:
                if conf['pyfile'] == module_name:

                    self.logger.debug("Model %s enabled by configuration",
                                      module_name)
                    pm.models.load_plugin(module_name)
                    model_name = f'models.{module_name}'
                    module = pm.models.get_plugin_module(model_name)
                    self.logger.debug(("Configured model %s has %d "
                                       "intra-experiment models"),
                                      model_name,
                                      len(module.available_models('intra')))

                    self.logger.debug(("Configured model %s has %d "
                                       "inter-experiment models"),
                                      model_name,
                                      len(module.available_models('inter')))

                    for avail in module.available_models('intra'):
                        model = getattr(module, avail)(self.main_config, conf)
                        self.models_intra.append(model)

                    for avail in module.available_models('inter'):
                        model = getattr(module, avail)(self.main_config, conf)
                        self.models_inter.append(model)
                else:
                    self.logger.debug("Model %s disabled by configuration",
                                      module_name)

        if len(self.models_intra) > 0:
            self.logger.info("Loaded %s intra-experiment models for project '%s'",
                             len(self.models_intra),
                             self.cmdopts['project'])

        if len(self.models_inter) > 0:
            self.logger.info("Loaded %s inter-experiment models for project '%s'",
                             len(self.models_inter),
                             self.cmdopts['project'])

    def _calc_inter_LN_targets(self) -> tp.List[types.YAMLDict]:
        """
        Use YAML configuration for controllers and inter-experiment graphs to
        what CSV files need to be collated/what graphs should be generated.
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

        self.logger.debug("Loaded linegraph categories: %s", keys)
        filtered_keys = [k for k in self.inter_LN_config if k in keys]
        targets = [self.inter_LN_config[k] for k in filtered_keys]

        self.logger.debug("Enabled linegraph categories: %s", filtered_keys)
        return targets

    def _run_rendering(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Render captured frames and/or frames created by imagizing in stage 3
        into videos.
        """
        self.logger.info("Rendering videos...")
        start = time.time()
        BatchExpParallelVideoRenderer(self.main_config, self.cmdopts)(criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Rendering complete in %s", str(sec))

    def _run_intra_models(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("Running %d intra-experiment models...",
                         len(self.models_intra))
        start = time.time()
        IntraExpModelRunner(self.cmdopts,
                            self.models_intra)(self.main_config,
                                               criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Intra-experiment models finished in %s", str(sec))

    def _run_inter_models(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self.logger.info("Running %d inter-experiment models...",
                         len(self.models_inter))
        start = time.time()

        runner = InterExpModelRunner(self.cmdopts, self.models_inter)
        runner(self.main_config, criteria)

        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Inter-experiment models finished in %s", str(sec))

    def _run_intra_graph_generation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate intra-experiment graphs (duh).
        """
        self.logger.info("Generating intra-experiment graphs...")
        start = time.time()
        BatchIntraExpGraphGenerator(self.cmdopts)(self.main_config,
                                                  self.controller_config,
                                                  self.intra_LN_config,
                                                  self.intra_HM_config,
                                                  criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info(
            "Intra-experiment graph generation complete: %s", str(sec))

    def _run_collation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        targets = self._calc_inter_LN_targets()

        if not self.cmdopts['skip_collate']:
            self.logger.info("Collating inter-experiment .csv files...")
            start = time.time()
            GraphParallelCollator(
                self.main_config, self.cmdopts)(criteria, targets)
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            self.logger.info(
                "Collating inter-experiment .csv files complete: %s", str(sec))

    def _run_inter_graph_generation(self, criteria: bc.IConcreteBatchCriteria) -> None:
        """
        Generate inter-experiment graphs (duh).
        """
        targets = self._calc_inter_LN_targets()

        self.logger.info("Generating inter-experiment graphs...")
        start = time.time()

        generator = pm.module_load_tiered(project=self.cmdopts['project'],
                                          path='pipeline.stage4.inter_exp_graph_generator')
        generator.InterExpGraphGenerator(self.main_config,
                                         self.cmdopts,
                                         targets)(criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)

        self.logger.info(
            "Inter-experiment graph generation complete: %s", str(sec))


__api__ = [
    'PipelineStage4'
]
