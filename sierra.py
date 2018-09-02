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


def get_generator_pair(args):
    """Get the (controller, scenario) generator pair as a string tuple"""
    # To ease the ache in my typing fingers
    abbrev_dict = {"SS": "single_source",
                   "PL": "powerlaw",
                   "RN": "random"}

    if args.generator is None:
        return None
    elif 1 == len(args.generator.split('.')):
        return ("generators." + args.generator + ".BaseGenerator",)
    else:
        return ("generators." + args.generator.split('.')[0] + ".BaseGenerator",
                "generators." + abbrev_dict[args.generator.split('.')[1][:2]] +
                "." + args.generator.split('.')[1])


def get_input_generator(args):
    """Get the input generator to use to create experiment/batch inputs."""
    if not any([args.exp_graphs_only, args.exp_run_only, args.exp_average_only]):

        # The two generator class names from which should be created a new class for my scenario +
        # controller changes.
        generator_pair = get_generator_pair(args)

        if args.batch_criteria is not None:
            criteria = __import__("variables.{0}".format(
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
                                    template_config_file=args.template_config_file,
                                    generation_root=args.generation_root,
                                    exp_output_root=args.output_root,
                                    n_sims=args.n_sims,
                                    n_threads=args.n_threads,
                                    tsetup=args.time_setup,
                                    exp_def_fname="exp_def.pkl")


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
                        "for controllers, scenarios, experiment/simulation inputs/outputs will be" +
                        "created in this directory as needed. Can persist between invocations.")
    parser.add_argument("--generation-root",
                        help="""Root directory to save generated experiment input files, or the
                        directory which will contain directories for each experiment's input files,
                        for batch mode. Defaults to
                        <sierra_root>/<controller>/<scenario>/exp-inputs. You should almost never
                        have to change this.""")
    parser.add_argument("--output-root",
                        help="""Root directory for saving simulation outputs a single experiment, or
                        the root directory which will contain directories for each experiment's
                        outputs for batch mode). Defaults to
                        <sierra_root>/<controller>/<scenario>/exp-outputs. You should almost never
                        have to change this.""")
    parser.add_argument("--graph-root",
                        help="""Root directory for saving generated graph files for a single
                        experiment, or the root directory which will contain directories for each
                        experiment's generated graphs for batch mode. Defaults to
                        <sierra_root>/<controller>/<scenario>/generated-graphs. You should almost
                        never have to change this.""")

    run_group = parser.add_mutually_exclusive_group()
    run_group.add_argument("--exp-inputs-only",
                           help="""Only generate the config files and command file for an
                           experiment/set of experiments.""",
                           action="store_true")
    run_group.add_argument("--exp-run-only",
                           help="""Only run the experiments on previously generated set of input
                           files for an experiment/set of experiments.""",
                           action="store_true")
    run_group.add_argument("--exp-average-only",
                           help="Only perform CSV averaging on a previously run experiment/set of experiments.",
                           action="store_true")
    run_group.add_argument("--exp-graphs-only",
                           help="Only perform graph generation on a previous run experiments/set of experiments.",
                           action="store_true")
    run_group.add_argument("--comp-graphs-only",
                           help="""Only perform graph generation for comparing controllers. All
                           controllers within <sierra_root> will be compared, so it is assumed that
                           if this option is passed that the # experiments/batch criteria is the
                           same for all. This is NOT part of the default pipeline.""",
                           action="store_true")
    parser.add_argument("--comp-controllers",
                        help="""Comma separated list of controllers to compare within <sierra
                        oot>. Specify 'all' to compare all controllers in <sierra root>. Only used
                        if --comp-graphs-only is passed. Default=all.""",
                        default="all")
    parser.add_argument("--generator",
                        help="""Experiment generator to use. Must be specified as < controller > or
                        < controller > . < scenario > .
                        Controller options are: [stateless, stateful, depth1]
                        Scenario options are: [RND{10x10, 20x20, 40x40},
                                              SS{12x6, 24x12, 48x24},
                                              PL{10x10, 20x20, 40x40}]
                        """)

    parser.add_argument("--no-msi",
                        help="Include if running on a personal computer (otherwise runs supercomputer commands).",
                        action="store_true")

    parser.add_argument("--batch-criteria",
                        help='''\
                        Name of criteria to use to generate the batched experiments. Options are
                        specified as <filename>.<class name> as found in the variables/ directory.''')
    parser.add_argument("--time-setup",
                        help='''The base simulation setup to use, which sets duration and metric
                        reporting interval. For options, see time_setup.py''',
                        default="time_setup.T5000")
    return parser


if __name__ == "__main__":
    # check python version
    import sys
    if sys.version_info < (3, 0):
        # restriction: cannot use Python 2.x to run this code
        raise RuntimeError("Python 3.x should must be used to run this code.")

    parser = define_cmdline()
    args = parser.parse_args()

    pair = get_generator_pair(args)

    # If the user specified a controller + scenario combination for the generator, use it to
    # determine directory names. If they only specified the controller part, then they *MUST* be
    # using batch criteria, and so use the batch criteria to uniquely specify directory names.
    #
    # Also, add the template file leaf to the root directory path to help track what experiment was
    # run.

    if pair is not None:
        if 2 == len(pair):
            controller = pair[0].split('.')[1]
            scenario = pair[1].split('.')[2]
        else:
            controller = pair[0].split('.')[1]
            scenario = args.batch_criteria.split('.')[1]

        template, ext = os.path.splitext(os.path.basename(args.template_config_file))

        print("- Controller={0}, Scenario={1}".format(controller, scenario))

        if args.generation_root is None:
            args.generation_root = os.path.join(args.sierra_root,
                                                controller,
                                                template + '-' + scenario,
                                                "exp-inputs")

        if args.output_root is None:
            args.output_root = os.path.join(args.sierra_root,
                                            controller,
                                            template + '-' + scenario,
                                            "exp-outputs")

        if args.graph_root is None:
            args.graph_root = os.path.join(args.sierra_root,
                                           controller,
                                           template + '-' + scenario,
                                           "graphs")

        generator = get_input_generator(args)
    else:
        generator = None

    pipeline = ExpPipeline(args, generator)
    pipeline.run()
