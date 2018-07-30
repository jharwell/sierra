"""
Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the terms of the GNU
  General Public License as published by the Free Software Foundation, either version 3 of the
  License, or (at your option) any later version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""

import argparse
import os
from pipeline.exp_pipeline import ExpPipeline
from pipeline.batched_exp_input_generator import BatchedExpInputGenerator
from generators.factory import GeneratorFactory


def get_input_generator(args):
    """Get the input generator to use to create experiment/batch inputs."""
    if not any([args.graphs_only, args.run_only, args.average_only]):

        # To ease the ache in my typing fingers
        abbrev_dict = {"SS": "single_source", "PL": "powerlaw", "RN": "random"}

        # The two generator class names from which should be created a new class for my scenario +
        # controller changes.
        if 2 == len(args.generator.split('.')[0]):
            generator_pair = ("generators." + args.generator.split('.')[0] + ".BaseGenerator",
                              "generators." + abbrev_dict[args.generator.split('.')[1][:2]] +
                              "." + args.generator.split('.')[1])
        else:
            generator_pair = ("generators." + args.generator.split('.')[0] + ".BaseGenerator",)

        if args.batch_criteria is not None:
            criteria = __import__("exp_variables.{0}".format(
                args.batch_criteria.split(".")[0]), fromlist=["*"])
            return BatchedExpInputGenerator(args.template_config_file,
                                            args.generation_root,
                                            args.output_root,
                                            getattr(criteria, args.batch_criteria.split(
                                                ".")[1])().gen_attr_changelist(),
                                            generator_pair,
                                            args.n_sims,
                                            args.n_threads,
                                            args.time_setup)
        else:
            return GeneratorFactory(generator_pair,
                                    args.template_config_file,
                                    args.generation_root,
                                    args.output_root,
                                    args.n_sims,
                                    args.n_threads,
                                    args.time_setup)


def define_cmdline():
    """Define the command line arguments for sierra. Returns a parser with the definitions."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-config-file",
                        help="The template configuration file for the experiment.")

    parser.add_argument("--n_sims",
                        help="How many simulations to run in a single experiment in parallel. Defaults to 100.", type=int, default=100)
    parser.add_argument("--n_threads",
                        help="How many ARGoS simulation threads to use. Defaults to 4.",
                        type=int,
                        default=4)

    # upgrade: think about adding a save CSV path
    parser.add_argument("--sierra-root",
                        help="Root directory for all sierra generate/created files. Subdirectories " +
                        "for each pipeline stage will be automatically created in this directory " +
                        "unless the corresponding option is explicitly passed to override.")

    parser.add_argument("--generation-root",
                        help="Root directory to save generated files. Defaults to <sierra_root>/generated-inputs.")
    parser.add_argument("--output-root",
                        help="Root directory for saving simulation outputs (sort of a scratch dir). Defaults to <sierra_root>/output")
    parser.add_argument("--graph-root",
                        help="Root directory for saving generated graph files. Defaults to <sierra_root>/generated-graphs.")
    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument("--inputs-only",
                           help="Only generate the config files and command file for an experiment/set of experiments.",
                           action="store_true")
    run_group.add_argument("--run-only",
                           help="Only run the experiments on previously generated set of input files for an experiment/set of experiments.",
                           action="store_true")
    run_group.add_argument("--average-only",
                           help="Only perform CSV averaging on a previously run experiment/set of experiments.",
                           action="store_true")
    run_group.add_argument("--graphs-only",
                           help="Only perform graph generation on a previous run experiments/set of experiments.",
                           action="store_true")
    parser.add_argument("--generator",
                        help="Experiment generator to use. Options are: " +
                        "[stateless.*, stateful.*] (specifics can be found in generators/*.py)")

    parser.add_argument("--no-msi",
                        help="Include if running on a personal computer (otherwise runs supercomputer commands).",
                        action="store_true")

    parser.add_argument("--batch-criteria",
                        help='''\
                        Name of criteria to use to generate the batched experiments. Options are
                        specified as <filename>.<class name> as found in the exp_variables/ directory.''')
    parser.add_argument("--time-setup",
                        help='''The base simulation setup to use, which sets duration and metric
                        reporting interval. Options are: time_setup.[Default, Long, Short]''',
                        default="time_setup.Default")
    return parser


if __name__ == "__main__":
    # check python version
    import sys
    if sys.version_info < (3, 0):
        # restriction: cannot use Python 2.x to run this code
        raise RuntimeError("Python 3.x should must be used to run this code.")

    parser = define_cmdline()
    args = parser.parse_args()

    if args.generation_root is None:
        args.generation_root = os.path.join(args.sierra_root, "generated-inputs")

    if args.output_root is None:
        args.output_root = os.path.join(args.sierra_root, "outputs")

    if args.graph_root is None:
        args.graph_root = os.path.join(args.sierra_root, "generated-graphs")

    pipeline = ExpPipeline(args, get_input_generator(args))
    pipeline.run()
