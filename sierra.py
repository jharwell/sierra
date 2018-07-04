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

import argparse
import os
from exp_pipeline import ExpPipeline
from batched_exp_input_generator import BatchedExpInputGenerator
import batch_criteria

if __name__ == "__main__":
    # check python version
    import sys
    if sys.version_info < (3, 0):
        # restriction: cannot use Python 2.x to run this code
        raise RuntimeError("Python 3.x should must be used to run this code.")

    parser = argparse.ArgumentParser()
    parser.add_argument("--template-config-file",
                        help="The template configuration file for the experiment.")

    # upgrade: check to make sure I really need code path; I don't think I do.
    parser.add_argument("--n_sims",
                        help="How many experiments to run in parallel/average. Defaults to 100. Specify 0 to just average CSVs and create graphs " +
                        "without generating config files or running experiments.", type=int, default=100)
    parser.add_argument("--generation-root",
                        help="Root directory to save generated files. Defaults to ~/generated-inputs.",
                        default=os.path.expanduser("~/generated-inputs"))

    # upgrade: think about adding a save CSV path
    parser.add_argument("--output-root",
                        help="Root directory for saving simulation outputs (sort of a scratch dir). Defaults to ~/output",
                        default=os.path.expanduser("~/output"))
    parser.add_argument("--graph-save-root",
                        help="Root directory for saving generated graph files. Defaults to ~/generated-graphs.",
                        default=os.path.expanduser("~/generated-graphs"))

    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument("--generate-only",
                           help="Only generate the config files and command file. Do not run simulations or average data.",
                           action="store_true")
    run_group.add_argument("--run-only",
                           help="Only run the experiments on previously generated set of input files. No data averaging.",
                           action="store_true")
    run_group.add_argument("--average-only",
                           help="Only perform CSV averaging on a previously run set of experiments.",
                           action="store_true")

    parser.add_argument("exp_type",
                        help="Experiment to run. Options are: [stateless]")
    parser.add_argument("--personal",
                        help="Include if running on a personal computer (otherwise runs supercomputer commands).",
                        action="store_true")
    parser.add_argument("--random-seed-min",
                        help="The minimum random seed number", type=int)
    parser.add_argument("--random-seed-max",
                        help="The maximum random seed number", type=int)
    parser.add_argument("--batch",
                        help="Run a batch of experiments instead of a single one.",
                        action="store_true")
    parser.add_argument("--batch-criteria",
                        help="Name of criteria to use to generate the batched experiments.")
    args = parser.parse_args()

    input_generator = None
    pipeline = None

    criteria = []
    module = __import__(str("experiments." + args.exp_type), fromlist=["*"])

    if args.batch:
        input_generator = BatchedExpInputGenerator(args.template_config_file,
                                                   args.generation_root,
                                                   args.output_root,
                                                   getattr(batch_criteria,
                                                           str(args.batch_criteria))().gen_list(),
                                                   getattr(module, "BaseInputGenerator"),
                                                   args.n_sims,
                                                   args.random_seed_min,
                                                   args.random_seed_max)
    else:
        input_generator = getattr(module, "BaseInputGenerator")(args.template_config_file,
                                                                args.generation_root,
                                                                args.output_root,
                                                                args.n_sims,
                                                                args.random_seed_min,
                                                                args.random_seed_max)
    pipeline = ExpPipeline(args, input_generator)
    pipeline.run()
