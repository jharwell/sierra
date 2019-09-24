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

import os


class PipelineStage1:

    """
    Implements stage 1 of the experimental pipeline: Generate a set of XML configuration files from
    a template suitable for input into ARGoS that contain user-specified modifications.
    """

    def __init__(self, cmdopts, input_generator, batch_criteria):
        self.cmdopts = cmdopts
        self.input_generator = input_generator
        self.batch_criteria = batch_criteria

    def run(self):
        if self.batch_criteria is not None:
            print(
                "- Stage1: Generating input files for batched experiment in {0}...".format(self.cmdopts['generation_root']))

            print("-- Using '{0}'".format(self.cmdopts['time_setup']))
            print("-- Using {0} physics engines".format(self.cmdopts['n_physics_engines']))
            self.input_generator.generate()
            print("- Stage1: {0} input files generated in {1} experiments.".format(
                sum([len(files) for r, d, files in os.walk(self.cmdopts['generation_root'])]),
                sum([len(d) for r, d, files in os.walk(self.cmdopts['generation_root'])])))
        else:
            print(
                "- Stage1: Generating input files for experiment in {0}...".format(self.cmdopts['generation_root']))
            print("-- Using '{0}'".format(self.cmdopts['time_setup']))
            print("-- Using {0} physics engines".format(self.cmdopts['n_physics_engines']))
            self.input_generator.generate()
            print("- Stage1: {0} input files generated for experiment.".format(
                sum([len(files) for r, d, files in os.walk(self.cmdopts['generation_root'])])))

        # Computed during input generation and needed later for graph generation; not part of
        # default cmdopts dict so we grab it here
        self.cmdopts['arena_dim'] = self.input_generator.cmdopts['arena_dim']
