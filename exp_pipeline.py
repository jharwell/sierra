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

from exp_csv_averager import ExpCSVAverager
from batched_exp_csv_averager import BatchedExpCSVAverager
from exp_runner import ExpRunner
from batched_exp_runner import BatchedExpRunner
import os

class ExpPipeline:

    """
    Automation for running ARGoS robotic simulation experiments in parallel

    Implements the following pipeline for single OR batched experiments:

    1. Generate a set of XML configuration files from a template suitable for
       input into ARGoS that contain user-specified modifications.
    2. Run the specified  # of experiments in parallel using GNU Parallel on
       the provided set of hosts on MSI (or on a single personal computer for testing).
    3. Average the .csv results of the simulation runs together.
    4. Generate a user-defined set of pretty graphs based on the averaged results.
    """
    def __init__(self, args, input_generator):
        self.args = args
        self.input_generator = input_generator

    def generate_inputs(self):
        # Generate simulation inputs
        if not self.args.run_only and not self.args.average_only:
            print("- Generating input files for '{0}'...".format(self.args.exp_type))
            self.input_generator.generate()
            print("- Input files generated.")

    def run_experiments(self):
        if self.args.average_only:
            return

        if self.args.batch:
            runner = BatchedExpRunner(self.args.generation_root)
        else:
            runner = ExpRunner(self.args.generation_root)

        runner.run(personal=self.args.personal)

    def average_results(self):
        template_config_leaf, template_config_ext = os.path.splitext(
            os.path.basename(self.args.template_config_file))

        if self.args.batch:
            averager = BatchedExpCSVAverager(template_config_leaf, self.args.output_root)
        else:
            averager = ExpCSVAverager(template_config_leaf, self.args.output_root)

        print("- Averaging outputs for '{0}'...".format(self.args.exp_type))
        averager.average_csvs()
        print("- Averaging output complete")


    def run(self):
        assert self.args.n_sims > 0, ("Must specify at least 1 simulation!")

        self.generate_inputs()
        if self.args.generate_only:
            return

        self.run_experiments()
        if self.args.run_only:
            return

        self.average_results()

        # Finally, generate graphs
        # graph_generator = BaseGraphGenerator(self.args.exp_output_root, self.args.graph_save_path)
