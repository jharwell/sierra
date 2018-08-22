"""
 Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

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

from pipeline.stage1 import PipelineStage1
from pipeline.stage2 import PipelineStage2
from pipeline.stage3 import PipelineStage3
from pipeline.stage4 import PipelineStage4
from pipeline.stage5 import PipelineStage5


class ExpPipeline:

    """
    Automation for running ARGoS robotic simulation experiments in parallel

    Implements the following pipeline for single OR batched experiments:

    1. Generate a set of XML configuration files from a template suitable for
       input into ARGoS that contain user-specified modifications.
    2. Run the specified  # of experiments in parallel using GNU Parallel on
       the provided set of hosts on MSI (or on a single personal computer for testing).
    3. Average the .csv results of the simulation runs together.
    4. Generate a user-defined set of graphs based on the averaged results for each
       experiment, and possibly across experiments for batches.
    5. Compare controllers that have been tested with the same experiment batch across different
       performance measures.
    """

    def __init__(self, args, input_generator):
        self.args = args
        self.input_generator = input_generator

    def generate_inputs(self):
        PipelineStage1(self.args, self.input_generator).run()

    def run_experiments(self):
        PipelineStage2(self.args).run()

    def average_results(self):
        PipelineStage3(self.args).run()

    def generate_graphs(self):
        PipelineStage4(self.args).run()

    def compare_controllers(self):
        if self.args.comp_controllers is not "all":
            PipelineStage5(self.args, self.args.comp_controllers).run()
        else:
            PipelineStage5(self.args, None).run()

    def run(self):

        if not any([self.args.exp_run_only, self.args.exp_average_only, self.args.exp_graphs_only,
                    self.args.comp_graphs_only]):
            self.generate_inputs()

        if not any([self.args.exp_inputs_only, self.args.exp_average_only, self.args.exp_graphs_only,
                    self.args.comp_graphs_only]):
            self.run_experiments()

        if not any([self.args.exp_inputs_only, self.args.exp_run_only, self.args.exp_graphs_only,
                    self.args.comp_graphs_only]):
            self.average_results()

        if not any([self.args.exp_inputs_only, self.args.exp_run_only, self.args.exp_average_only,
                    self.args.comp_graphs_only]):
            self.generate_graphs()

        # not part of default pipeline
        if self.args.comp_graphs_only:
            self.compare_controllers()
