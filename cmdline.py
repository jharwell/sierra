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


class Cmdline:
    def init(self):
        """
        Defines the command line arguments for sierra. Returns a parser with the definitions.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("--template-config-file",
                            help="The template configuration file for the experiment.")

        parser.add_argument("--n_sims",
                            help="""How many should be averaged together to form a single experiment. Use=stage1. Default=100.""",
                            type=int,
                            default=100)
        parser.add_argument("--n_threads",
                            help="""How many ARGoS simulation threads to use for each simulation in
                            each experiment. Use=stage1. Default=8.""",
                            type=int,
                            default=8)

        parser.add_argument("--sierra-root",
                            help="""Root directory for all sierra generated/created files. Subdirectories for controllers, scenarios,
                            experiment/simulation inputs/outputs will be created in this directory
                            as needed. Can persist between invocations of sierra.""")
        parser.add_argument("--generation-root",
                            help="""Root directory to save generated experiment input files, or the directory which will contain
                            directories for each experiment's input files, for batch
                            mode. Use=stage[1,2,3]. Default=<sierra_root>/<controller>/<scenario>/exp-inputs. You
                            should almost never have to change this.""")
        parser.add_argument("--output-root",
                            help="""Root directory for saving simulation outputs a single experiment, or
                            the root directory which will contain directories for each experiment's
                            outputs for batch mode). Use=stage[3,4,5]. Defaults to
                            <sierra_root>/<controller>/<scenario>/exp-outputs. You should almost never
                            have to change this.""")
        parser.add_argument("--graph-root",
                            help="""Root directory for saving generated graph files for a single experiment, or the root directory
                            which will contain directories for each experiment's generated graphs
                            for batch
                            mode. Use=stage[4,5]. Defaults=<sierra_root>/<controller>/<scenario>/generated-graphs. You
                            should almost never have to change this.""")

        run_group = parser.add_mutually_exclusive_group()
        run_group.add_argument("--exp-inputs-only",
                               help="""Only generate the config files and command file for an
                               experiment/set of experiments (stage1).""",
                               action="store_true")
        run_group.add_argument("--exp-run-only",
                               help="""Only run the experiments on previously generated set of input
                               files for an experiment/set of experiments (stage2).""",
                               action="store_true")
        run_group.add_argument("--exp-average-only",
                               help="""Only perform CSV averaging on a previously run experiment/set
                               of experiments (stage3).""",
                               action="store_true")
        run_group.add_argument("--exp-graphs-only",
                               help="""Only perform graph generation on a previous run
                               experiments/set of experiments (stage4).""",
                               action="store_true")
        run_group.add_argument("--cc-graphs-only",
                               help="""Only perform graph generation for comparing controllers (stage5). It is assumed that if this
                               option is passed that the # experiments/batch criteria is the same
                               for all controllers that will be compared. This is NOT part of the
                               default pipeline.""",
                               action="store_true")
        parser.add_argument("--comp-controllers",
                            help="""Comma separated list of controllers to compare within <sierra
                            oot>. Specify 'all' to compare all controllers in <sierra root>. Only used
                            if --cc-graphs-only is passed. Default=all.""",
                            default="all")
        parser.add_argument("--generator",
                            help="""Experiment generator to use, which is a combination of
                            controller+scenario configuration. Full specification is [depth0, depth1,
                            depth2].<controller>.<scenario>.AxB, where A and B are the scenario
                            dimensions (which can be any non-negative integer values).

                            However, the dimensions can be omitted for some batch criteria.

                            Valid controllers can be found in the [depth0,depth1,depth2] files in the
                            generators/ directory.


                            Scenario options are: [RN, SS, DS, QS, PL], which correspond to [random,
                            single source, dual source, quad source, powerlaw block distributions].

                            The generator can be omitted if only running stages [4,5], but must be
                            present if any of the other stages will be running, or sierra will crash.
                            """)

        parser.add_argument("--no-msi",
                            help="Include if running on a personal computer (otherwise runs supercomputer commands).",
                            action="store_true")

        parser.add_argument("--batch-criteria",
                            help='''\
                            Name of criteria to use to generate the batched experiments. Options are
                            specified as <filename>.<class name> as found in the variables/
                            directory.''')
        parser.add_argument("--batch-exp-num",
                            help='''\
                            Experiment number from the batch to run. Ignored if --batch-criteria is not
                            passed.
                            ''')
        parser.add_argument("--time-setup",
                            help='''The base simulation setup to use, which sets duration and metric
                            reporting interval. For options, pppsee time_setup.py''',
                            default="time_setup.T5000")
        parser.add_argument("--n-physics-engines",
                            help='''The # of physics engines to use during simulation (yay
                            ARGoS!). Possible values are [1,4,16] currently, arranged in a uniform grid.''',
                            default=1)
        return parser
