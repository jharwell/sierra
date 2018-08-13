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

    Average the .csv results of the simulation runs together.
    """

    def __init__(self, args):
        self.args = args

    def run(self):
        template_config_leaf, template_config_ext = os.path.splitext(
            os.path.basename(self.args.template_config_file))

        if self.args.batch_criteria is not None:
            print(
                "- Averaging batched experiment outputs for '{0}'...".format(self.args.generator))
            averager = BatchedExpCSVAverager(template_config_leaf, self.args.output_root)
        else:
            print(
                "- Averaging single experiment outputs for '{0}'...".format(self.args.generator))
            averager = ExpCSVAverager(template_config_leaf, self.args.output_root)

        averager.average_csvs()
        print("- Averaging complete")
