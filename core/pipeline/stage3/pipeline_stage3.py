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
import logging
import time
import datetime

# 3rd party packages
import yaml

# Project packages
from core.pipeline.stage3.statistics_calculator import BatchExpParallelCalculator
from core.pipeline.stage3.imagizer import BatchExpParallelImagizer
import core.utils
import core.variables.batch_criteria as bc


class PipelineStage3:
    """
    Implements stage 3 of the experimental pipeline.

    Processes results of simulation runs within an experiment/within multiple experiments
    together, according to configuration. Currently this includes:

    - Averaging simulation results.
    - Generating image files from project metric collection for later use in video rendering in stage
      4.

    This stage is idempotent.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def run(self, main_config: dict, cmdopts: dict, criteria: bc.IConcreteBatchCriteria):
        self._run_statistics(main_config, cmdopts, criteria)

        if cmdopts['project_imagizing']:
            intra_HM_config = yaml.load(open(os.path.join(cmdopts['core_config_root'],
                                                          'intra-graphs-hm.yaml')),
                                        yaml.FullLoader)

            project_intra_HM = os.path.join(cmdopts['project_config_root'],
                                            'intra-graphs-hm.yaml')

            if core.utils.path_exists(project_intra_HM):
                self.logger.info("Loading additional intra-experiment heatmap config for project '%s'",
                                 cmdopts['project'])
                project_dict = yaml.load(open(project_intra_HM), yaml.FullLoader)
                for category in project_dict:
                    if category not in intra_HM_config:
                        intra_HM_config.update({category: project_dict[category]})
                    else:
                        intra_HM_config[category]['graphs'].extend(project_dict[category]['graphs'])

            self._run_imagizing(main_config, intra_HM_config, cmdopts, criteria)

    # Private functions
    def _run_statistics(self,
                        main_config: dict,
                        cmdopts: dict, criteria:
                        bc.IConcreteBatchCriteria):
        self.logger.info("Generating statistics from experiment outputs in %s...",
                         cmdopts['batch_output_root'])
        start = time.time()
        BatchExpParallelCalculator(main_config, cmdopts)(criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Statistics generation complete in %s", str(sec))

    def _run_imagizing(self,
                       main_config: dict,
                       intra_HM_config: dict,
                       cmdopts: dict,
                       criteria: bc.IConcreteBatchCriteria):
        self.logger.info("Imagizing .csvs in %s...",
                         cmdopts['batch_output_root'])
        start = time.time()
        BatchExpParallelImagizer(main_config, cmdopts)(intra_HM_config, criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Imagizing complete: %s", str(sec))


__api__ = [
    'PipelineStage3'
]
