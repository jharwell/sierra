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


import os
import logging
import typing as tp
import time
import datetime
import yaml

from core.pipeline.stage3.exp_csv_averager import BatchedExpCSVAverager
from core.pipeline.stage3.exp_imagizer import BatchedExpImagizer


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

    def run(self, main_config: dict, cmdopts: tp.Dict[str, str]):
        self.__run_averaging(main_config, cmdopts)

        if cmdopts['project_imagizing']:
            intra_HM_config = yaml.load(open(os.path.join(cmdopts['core_config_root'],
                                                          'intra-graphs-hm.yaml')),
                                        yaml.FullLoader)

            project_intra_HM = os.path.join(cmdopts['project_config_root'],
                                            'intra-graphs-hm.yaml')

            if os.path.exists(project_intra_HM):
                logging.info("Stage3: Loading additional intra-experiment heatmap config for project '%s'",
                             cmdopts['project'])
                project_dict = yaml.load(open(project_intra_HM), yaml.FullLoader)
                for category in project_dict:
                    if category not in intra_HM_config:
                        intra_HM_config.update({category: project_dict[category]})
                    else:
                        intra_HM_config[category]['graphs'].extend(project_dict[category]['graphs'])

            self.__run_imagizing(main_config, intra_HM_config, cmdopts)

    # Private functions
    def __run_averaging(self, main_config, cmdopts):
        template_input_leaf, _ = os.path.splitext(
            os.path.basename(cmdopts['template_input_file']))
        avg_params = {
            'template_input_leaf': template_input_leaf,
            'no_verify_results': cmdopts['no_verify_results'],
            'gen_stddev': cmdopts['gen_stddev'],
            'project_imagizing': cmdopts['project_imagizing']
        }
        logging.info("Stage3: Averaging batched experiment outputs in %s...",
                     cmdopts['output_root'])
        start = time.time()
        BatchedExpCSVAverager()(main_config, avg_params, cmdopts['output_root'])
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        logging.info("Stage3: Averaging complete in %s", str(sec))

    def __run_imagizing(self, main_config: dict, intra_HM_config: dict, cmdopts: dict):
        logging.info("Stage3: Imagizing .csvs...")
        start = time.time()
        BatchedExpImagizer()(main_config,
                             intra_HM_config,
                             cmdopts['output_root'])
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        logging.info("Stage3: Imagizing complete: %s", str(sec))


__api__ = [
    'PipelineStage1'
]
