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

import os
import random
import argparse
import subprocess
import re
from csv_class import CSV
from xml_file_generator import XMLFileGenerator
from base_graph_generator import BaseGraphGenerator
from csv_averager import CSVAverager
from experiment_runner import ExperimentRunner


class ExperimentPipeline:

    """
    Automation for running C++ based robotic simulation experiments in parallel.

    Implements the following pipeline:

    1. Generates a set of XML configuration files from a template suitable for
       input into ARGoS that contain user-specified modifications.
    2. Run the specified  # of experiments in parallel using GNU Parallel on
       the provided set of hosts on MSI (or on a single personal computer for testing).
    3. Average the .csv results of the experimental runs together.
    4. Generate a user-defined set of graphs based on the averaged results.
    """
    def run(args):
        # Generate simulation inputs
        file_generator = XMLFileGenerator(args.config_path, args.code_path,
                                          args.config_save_path,
                                          args.output_save_path, args.n_sims,
                                          args.random_seed_min,
                                          args.random_seed_max,
                                          args.remove_both_visuals)
        file_generator.generate_xml_files()

        # Run simulations!
        runner = ExperimentRunner(args.config_path, args.code_path,
                                  args.config_save_path, args.output_save_path,
                                  args.n_sims)

        if (runner.n_sims > 0):
            if not args.only_run:
                runner.generate_xml_files()
            if not args.do_not_run:
                runner.run_experiments(personal=args.personal)

        # Average results
        averager = CSVAverager(args.config_path, args.output_save_path)
        if not args.do_not_average:
            averager.average_csvs()

        # Finally, generate graphs
        graph_generator = BaseGraphGenerator(args.output_save_path, args.graph_save_path)

if __name__ == "__main__":
    # check python version
    import sys
    if sys.version_info < (3, 0):
        # restriction: cannot use Python 2.x to run this code
        raise RuntimeError("Python 3.x should be usued to run this code.")

    parser = argparse.ArgumentParser()
    parser.add_argument("config-path",
                        help="The configuration file for the experiment to be run")

    # upgrade: check to make sure I really need code path; I don't think I do.
    parser.add_argument("code-path",
                        help="Path to directory for code is to run the experiment.")
    parser.add_argument("n_sims",
                        help="How many experiments to run (specify 0 to just average CSVs and create graphs " +
                        "without generating config files or running experiments).", type=int)
    parser.add_argument("--config-save-path",
                        help="Where to save the generated config files.")
    # upgrade: think about adding a save CSV path
    parser.add_argument("--output-save-path",
                        help="Where to save the generated output.")
    parser.add_argument("--graph-save-path",
                        help="Where to save the generated graph files.")

    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument("--do-not-run",
                           help="Include to only generate the config files and command file, not run them",
                           action="store_true")
    run_group.add_argument("--only-run",
                           help="Include to only run the config files, not generate them",
                           action="store_true")
    parser.add_argument("--do-not-average",
                        help="Include to not average the CSVs",
                        action="store_true")
    parser.add_argument("--personal",
                        help="Include if running parallel on a personal computer (otherwise runs supercomputer commands)",
                        action="store_true")
    parser.add_argument("--random-seed-min",
                        help="The minimum random seed number", type=int)
    parser.add_argument("--random-seed-max",
                        help="The maximum random seed number", type=int)
    parser.add_argument("--remove-both-visuals",
                        help="include to remove the loop function visualization (in addition to the argos visualization)",
                        action="store_true")
    args = parser.parse_args()

    pipeline = ExperimentPipeline(args)
    pipeline.run()
