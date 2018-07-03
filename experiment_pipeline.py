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

from csv_averager import CSVAverager
from experiment_runner import ExperimentRunner


class ExperimentPipeline:

    """
    Automation for running ARGoS robotic simulation experiments in parallel.

    Implements the following pipeline:

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
            print("- Generating input files for {} simulations....".format(self.args.n_sims))
            self.input_generator.generate()
            print("- Experiment input files generated.")

    def run_experiments(self):
        # Run simulations!
        runner = ExperimentRunner(self.args.generation_root)

        if not self.args.average_only:
            runner.run(personal=self.args.personal)

    def average_results(self):
        # Average results
        averager = CSVAverager(self.args.template_config_file, self.args.exp_output_root)
        averager.average_csvs()

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
