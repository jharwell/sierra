# Copyright 2018 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""
Contains main class implementing stage  of the experimental pipeline.
"""


import os
import logging
from core.generators.exp_generator import BatchedExpDefGenerator
from core.generators.exp_creator import BatchedExpCreator


class PipelineStage1:
    """
    Implements stage 1 of the pipeline.

    Generates a set of XML configuration files from a template suitable for input into ARGoS that
    contain user-specified modifications. This stage is idempotent.

    """

    def __init__(self, controller, scenario, batch_criteria, cmdopts) -> None:
        self.generator = BatchedExpDefGenerator(batch_config_template=cmdopts['template_input_file'],
                                                controller_name=controller,
                                                scenario_basename=scenario,
                                                criteria=batch_criteria,
                                                cmdopts=cmdopts)
        self.creator = BatchedExpCreator(batch_config_template=cmdopts['template_input_file'],
                                         batch_generation_root=cmdopts['generation_root'],
                                         batch_output_root=cmdopts['output_root'],
                                         criteria=batch_criteria,
                                         cmdopts=cmdopts)

        self.cmdopts = cmdopts

    def run(self):
        """
        Run stage 1 of the experiment pipeline.
        """

        logging.info("Stage1: Generating input files for batched experiment in %s...",
                     self.cmdopts['generation_root'])
        logging.debug("Using '%s'", self.cmdopts['time_setup'])
        self.creator.create(self.generator)

        logging.info("Stage1: %d input files generated in %d experiments.",
                     sum([len(files) for r, d, files in os.walk(self.cmdopts['generation_root'])]),
                     sum([len(d) for r, d, files in os.walk(self.cmdopts['generation_root'])]))


__api__ = [
    'PipelineStage1'
]
