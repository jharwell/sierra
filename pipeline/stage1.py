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

    def __init__(self, args, input_generator):
        self.args = args
        self.input_generator = input_generator

    def run(self):
        if self.args.batch_criteria is not None:
            print("- Generating input files for batched experiment '{0}' in {1}...".format(self.args.generator,
                                                                                           self.args.generation_root))

            print("-- Using time_setup.{0}".format(self.args.time_setup))
            self.input_generator.generate()
            print("- {0} Input files generated in {1} experiments.".format(
                sum([len(files) for r, d, files in os.walk(self.args.generation_root)]),
                sum([len(d) for r, d, files in os.walk(self.args.generation_root)])))
        else:
            print("- Generating input files for experiment '{0}' in {1}...".format(self.args.generator,
                                                                                   self.args.generation_root))
            print("-- Using time_setup.{0}".format(self.args.time_setup))
            self.input_generator.generate()
            print("- {0} Input files generated for experiment.".format(
                sum([len(files) for r, d, files in os.walk(self.args.generation_root)])))
