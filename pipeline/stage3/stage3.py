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
import yaml
from .exp_csv_averager import BatchedExpCSVAverager
from .exp_video_renderer import BatchedExpVideoRenderer


class PipelineStage3:
    """
    Implements stage 3 of the experimental pipeline.

    Processes results of simulation runs within an experiment/within multiple experiments
    together. This stage is idempotent.
    """

    def __init__(self, cmdopts: dict):
        self.cmdopts = cmdopts
        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')),
                                     yaml.FullLoader)

    def run(self):
        tasks = self.cmdopts['results_process_tasks']
        if 'average' in tasks or 'all' in tasks:
            self.__run_averaging()

        if 'render' in tasks or 'all' in tasks:
            self.__run_rendering()

    # Private functions
    def __run_rendering(self):
        if not self.cmdopts['with_rendering']:
            return

        render_opts = {
            'cmd_opts': self.cmdopts['render_cmd_opts'],
            'ofile_leaf': self.cmdopts['render_cmd_ofile'],
        }
        logging.info("Stage3: Rendering videos for batched experiment in %s...",
                     self.cmdopts['generation_root'])
        BatchedExpVideoRenderer()(self.main_config, render_opts, self.cmdopts['output_root'])
        logging.info("Stage3: Rendering complete")

    def __run_averaging(self):
        template_input_leaf, _ = os.path.splitext(
            os.path.basename(self.cmdopts['template_input_file']))
        avg_params = {
            'template_input_leaf': template_input_leaf,
            'no_verify_results': self.cmdopts['no_verify_results'],
            'gen_stddev': self.cmdopts['gen_stddev'],
        }
        logging.info("Stage3: Averaging batched experiment outputs in %s...",
                     self.cmdopts['generation_root'])
        BatchedExpCSVAverager()(self.main_config, avg_params, self.cmdopts['output_root'])
        logging.info("Stage3: Averaging complete")
