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

from core.pipeline.stage3.exp_csv_averager import BatchedExpCSVAverager
from core.pipeline.stage3.exp_video_renderer import BatchedExpVideoRenderer


class PipelineStage3:
    """
    Implements stage 3 of the experimental pipeline.

    Processes results of simulation runs within an experiment/within multiple experiments
    together. This stage is idempotent.
    """

    def run(self, main_config: dict, cmdopts: tp.Dict[str, str]):
        tasks = cmdopts['results_process_tasks']
        if 'average' in tasks or 'all' in tasks:
            self.__run_averaging(main_config, cmdopts)

        if 'render' in tasks or 'all' in tasks:
            self.__run_rendering(main_config, cmdopts)

    # Private functions
    def __run_rendering(self, main_config, cmdopts):
        if not cmdopts['with_rendering']:
            return

        render_opts = {
            'cmd_opts': cmdopts['render_cmd_opts'],
            'ofile_leaf': cmdopts['render_cmd_ofile'],
        }
        logging.info("Stage3: Rendering videos for batched experiment in %s...",
                     cmdopts['generation_root'])
        BatchedExpVideoRenderer()(main_config, render_opts, cmdopts['output_root'])
        logging.info("Stage3: Rendering complete")

    def __run_averaging(self, main_config, cmdopts):
        template_input_leaf, _ = os.path.splitext(
            os.path.basename(cmdopts['template_input_file']))
        avg_params = {
            'template_input_leaf': template_input_leaf,
            'no_verify_results': cmdopts['no_verify_results'],
            'gen_stddev': cmdopts['gen_stddev'],
        }
        logging.info("Stage3: Averaging batched experiment outputs in %s...",
                     cmdopts['generation_root'])
        BatchedExpCSVAverager()(main_config, avg_params, cmdopts['output_root'])
        logging.info("Stage3: Averaging complete")
