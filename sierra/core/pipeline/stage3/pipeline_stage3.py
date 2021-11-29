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
Contains main class implementing stage 3 of the experimental pipeline.
"""

# Core packages
import os
import time
import datetime
import typing as tp
import logging  # type: tp.Any

# 3rd party packages
import yaml

# Project packages
from sierra.core.pipeline.stage3.statistics_calculator import BatchExpParallelCalculator
from sierra.core.pipeline.stage3.run_collator import ExperimentalRunParallelCollator
from sierra.core.pipeline.stage3.imagizer import BatchExpParallelImagizer
import sierra.core.utils
import sierra.core.variables.batch_criteria as bc
from sierra.core import types


class PipelineStage3:
    """Implements stage 3 of the experimental pipeline.

    Processes results of :term:`Experimental Runs <Experimental Run>` within a
    single :term:`Experiment` and across multiple experiments together,
    according to configuration. Currently this includes:

    - Averaging results for generating per-experiment graphs during stage 4.

    - Collating results across experiments for generating inter-experiment
      graphs during stage 4.

    - Generating image files from project metric collection for later use in
      video rendering in stage 4.

    This stage is idempotent.

    """

    def __init__(self, main_config: dict, cmdopts: types.Cmdopts) -> None:
        self.logger = logging.getLogger(__name__)
        self.main_config = main_config
        self.cmdopts = cmdopts

    def run(self, criteria: bc.IConcreteBatchCriteria) -> None:
        self._run_statistics(self.main_config, self.cmdopts, criteria)
        self._run_run_collation(self.main_config, self.cmdopts, criteria)

        if self.cmdopts['project_imagizing']:
            intra_HM_config = yaml.load(open(os.path.join(self.cmdopts['core_config_root'],
                                                          'intra-graphs-hm.yaml')),
                                        yaml.FullLoader)

            project_intra_HM = os.path.join(self.cmdopts['project_config_root'],
                                            'intra-graphs-hm.yaml')

            if sierra.core.utils.path_exists(project_intra_HM):
                self.logger.info("Loading additional intra-experiment heatmap config for project '%s'",
                                 self.cmdopts['project'])
                project_dict = yaml.load(
                    open(project_intra_HM), yaml.FullLoader)
                for category in project_dict:
                    if category not in intra_HM_config:
                        intra_HM_config.update(
                            {category: project_dict[category]})
                    else:
                        intra_HM_config[category]['graphs'].extend(
                            project_dict[category]['graphs'])

            self._run_imagizing(
                self.main_config, intra_HM_config, self.cmdopts, criteria)

    # Private functions
    def _run_statistics(self,
                        main_config: dict,
                        cmdopts: types.Cmdopts, criteria:
                        bc.IConcreteBatchCriteria):
        self.logger.info("Generating statistics from experiment outputs in %s...",
                         cmdopts['batch_output_root'])
        start = time.time()
        BatchExpParallelCalculator(main_config, cmdopts)(criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Statistics generation complete in %s", str(sec))

    def _run_run_collation(self,
                           main_config: dict,
                           cmdopts: types.Cmdopts, criteria:
                           bc.IConcreteBatchCriteria):
        if not self.cmdopts['no_collate']:
            self.logger.info("Collating experiment run outputs into %s...",
                             cmdopts['batch_stat_collate_root'])
            start = time.time()
            ExperimentalRunParallelCollator(main_config, cmdopts)(criteria)
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            self.logger.info(
                "Experimental run output collation complete in %s", str(sec))

    def _run_imagizing(self,
                       main_config: dict,
                       intra_HM_config: dict,
                       cmdopts: types.Cmdopts,
                       criteria: bc.IConcreteBatchCriteria):
        self.logger.info("Imagizing .csvs in %s...",
                         cmdopts['batch_output_root'])
        start = time.time()
        BatchExpParallelImagizer(main_config, cmdopts)(
            intra_HM_config, criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Imagizing complete: %s", str(sec))


__api__ = [
    'PipelineStage3'
]
