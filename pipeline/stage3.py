"""
 Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

from pipeline.exp_csv_averager import ExpCSVAverager
from pipeline.batched_exp_csv_averager import BatchedExpCSVAverager
from pipeline.exp_csv_averager import ExpCSVAverager
from pipeline.batched_exp_video_renderer import BatchedExpVideoRenderer
from pipeline.exp_video_renderer import ExpVideoRenderer
import os


class PipelineStage3:

    """
    Implements stage 3 of the experimental pipeline:

    Process results of simulation runs within an experiment/within multiple experiments
    together.

    """

    def __init__(self, cmdopts):
        self.cmdopts = cmdopts

    def run(self):
        if 'average' in self.cmdopts['results_process_tasks'] or 'all' in self.cmdopts['results_process_tasks']:
            self._run_averaging()

        if 'render' in self.cmdopts['results_process_tasks'] or 'all' in self.cmdopts['results_process_tasks']:
            self._run_rendering()

    def _run_rendering(self):
        if not self.cmdopts['with_rendering']:
            return
        if self.cmdopts['criteria_category'] is not None:
            print(
                "- Stage3: Rendering videos for batched experiment '{0}'...".format(self.cmdopts['generator']))
            renderer = BatchedExpVideoRenderer(self.cmdopts['output_root'],
                                               self.cmdopts['render_cmd_options'],
                                               self.cmdopts['render_cmd_ofile'])
        else:
            print(
                "- Stage3: Rendering single experiment video in '{0}'...".format(self.cmdopts['generator']))
            renderer = ExpVideoRenderer(self.cmdopts['output_root'],
                                        self.cmdopts['render_cmd_options'],
                                        self.cmdopts['render_cmd_ofile'])

        renderer.render()
        print("- Stage3: Rendering complete")

    def _run_averaging(self):
        template_config_leaf, template_config_ext = os.path.splitext(
            os.path.basename(self.cmdopts['template_config_file']))

        if self.cmdopts['criteria_category'] is not None:
            print(
                "- Stage3: Averaging batched experiment outputs for '{0}'...".format(self.cmdopts['generator']))
            averager = BatchedExpCSVAverager(template_config_leaf,
                                             self.cmdopts['output_root'],
                                             self.cmdopts['no_verify_results'],
                                             self.cmdopts['gen_stddev'])
        else:
            print(
                "- Stage3: Averaging single experiment outputs for '{0}'...".format(self.cmdopts['generator']))
            averager = ExpCSVAverager(template_config_leaf,
                                      self.cmdopts['no_verify_results'],
                                      self.cmdopts['gen_stddev'],
                                      self.cmdopts['output_root'])

        averager.run()
        print("- Stage3: Averaging complete")
