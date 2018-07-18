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
from intra_exp_graph_generator import IntraExpGraphGenerator
from csv_collator import CSVCollator
from batched_intra_exp_graph_generator import BatchedIntraExpGraphGenerator
from inter_exp_graph_generator import InterExpGraphGenerator
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
    4. Generate a user-defined set of graphs based on the averaged results for each
       experiment, and possibly across experiments for batches
    """

    def __init__(self, args, input_generator):
        self.args = args
        self.input_generator = input_generator

    def generate_inputs(self):
        print("- Generating input files for '{0}'...".format(self.args.generator))
        self.input_generator.generate()
        print("- Input files generated.")

    def run_experiments(self):
        if self.args.batch:
            runner = BatchedExpRunner(self.args.generation_root)
        else:
            runner = ExpRunner(self.args.generation_root, False)

        runner.run(no_msi=self.args.no_msi)

    def average_results(self):
        template_config_leaf, template_config_ext = os.path.splitext(
            os.path.basename(self.args.template_config_file))

        if self.args.batch:
            averager = BatchedExpCSVAverager(template_config_leaf, self.args.output_root)
        else:
            averager = ExpCSVAverager(template_config_leaf, self.args.output_root)

        print("- Averaging outputs for '{0}'...".format(self.args.generator))
        averager.average_csvs()
        print("- Averaging output complete")

    def generate_graphs(self):
        targets = [('block-transport-stats.csv',
                    'n_collected',
                    'blocks-collected.csv'),
                   ('block-transport-stats.csv',
                    'avg_transporters',
                    'blocks-avg-transporters.csv'),
                   ('block-transport-stats.csv',
                    'avg_transport_time',
                    'blocks-avg-transport-time.csv'),
                   ('block-transport-stats.csv',
                    'avg_initial_wait_time',
                    'blocks-initial-wait-time.csv'),
                   ('block-acquisition-stats.csv',
                    'avg_acquiring_goal',
                    'block-acquisition.csv'),
                   ('block-acquisition-stats.csv',
                    'avg_vectoring_to_goal',
                    'block-acquisition-vectoring.csv'),
                   ('block-acquisition-stats.csv',
                    'avg_exploring_for_goal',
                    'block-acquisition-exploring.csv'),
                   ('cache-acquisition-stats.csv',
                    'avg_acquiring_goal',
                    'cache-acquisition.csv'),
                   ('cache-acquisition-stats.csv',
                    'avg_vectoring_to_goal',
                    'cache-acquisition-vectoring.csv'),
                   ('cache-acquisition-stats.csv',
                    'avg_exploring_for_goal',
                    'cache-acquisition-exploring.csv'),
                   ('cache-lifecycle-stats.csv',
                    'n_created',
                    'cache-lifecycle-avg-created.csv'),
                   ('cache-lifecycle-stats.csv',
                    'n_depleted',
                    'cache-lifecycle-avg-depleted.csv'),
                   ('cache-lifecycle-stats.csv',
                    'n_created',
                    'cache-lifecycle-avg-created.csv'),
                   ('cache-lifecycle-stats.csv',
                    'n_depleted',
                    'cache-lifecycle-avg-depleted.csv'),
                   ('cache-utilization-stats.csv',
                    'avg_blocks',
                    'cache-avg-blocks.csv'),
                   ('cache-utilization-stats.csv',
                    'avg_pickups',
                    'cache-avg-pickups.csv'),
                   ('cache-utilization-stats.csv',
                    'avg_drops',
                    'cache-avg-drops.csv'),
                   ('cache-utilization-stats.csv',
                    'avg_penalty',
                    'cache-avg-penalty.csv'),
                   ]

        if self.args.batch:
            CSVCollator(self.args.output_root, targets)()
            intra_exp = BatchedIntraExpGraphGenerator(self.args.output_root, self.args.graph_root)
        else:

            intra_exp = IntraExpGraphGenerator(self.args.output_root, self.args.graph_root)
        print("- Generating intra-experiment graphs...")
        intra_exp()
        print("- Intra-experiment graph generation complete")

        if self.args.batch:
            print("- Generating inter-experiment graphs...")
            InterExpGraphGenerator(self.args.output_root, self.args.graph_root)()
            print("- Inter-experiment graph generation complete")

    def run(self):

        if not any([self.args.run_only, self.args.average_only, self.args.graphs_only]):
            self.generate_inputs()

        if not any([self.args.inputs_only, self.args.average_only, self.args.graphs_only]):
            self.run_experiments()

        if not any([self.args.inputs_only, self.args.run_only, self.args.graphs_only]):
            self.average_results()

        if not any([self.args.inputs_only, self.args.run_only, self.args.average_only]):
            self.generate_graphs()
