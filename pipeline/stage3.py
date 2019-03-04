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
import os


class PipelineStage3:

    """
    Implements stage 3 of the experimental pipeline:

    Average the .csv results of simulation runs within an experiment/within multiple experiments
    together.

    """

    def __init__(self, cmdopts):
        self.cmdopts = cmdopts

    def run(self):
        template_config_leaf, template_config_ext = os.path.splitext(
            os.path.basename(self.cmdopts['template_config_file']))

        if self.cmdopts['criteria_category'] is not None:
            print(
                "- Stage3: Averaging batched experiment outputs for '{0}'...".format(self.cmdopts['generator']))
            averager = BatchedExpCSVAverager(template_config_leaf,
                                             self.cmdopts['output_root'],
                                             self.cmdopts['no_verify_results'])
        else:
            print(
                "- Stage3: Averaging single experiment outputs for '{0}'...".format(self.cmdopts['generator']))
            averager = ExpCSVAverager(template_config_leaf,
                                      self.cmdopts['output_root'],
                                      self.cmdopts['no_verify_results'])

        averager.average_csvs()
        print("- Stage3: Averaging complete")
