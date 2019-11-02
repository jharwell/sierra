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


import os
import logging
from generators.exp_generator import BatchedExpDefGenerator
from generators.exp_creator import BatchedExpCreator


class PipelineStage1:
    """
    Implements stage 1 of the pipeline: Generate a set of XML configuration files from
    a template suitable for input into ARGoS that contain user-specified modifications.
    """

    def __init__(self, controller, scenario, batch_criteria, cmdopts):
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

        logging.info("Stage1: Generating input files for batched experiment in {0}...".format(
            self.cmdopts['generation_root']))
        logging.debug("Using '{0}'".format(self.cmdopts['time_setup']))
        logging.debug("Using {0} physics engines".format(self.cmdopts['physics_n_engines']))
        self.creator.create(self.generator)

        logging.info("Stage1: {0} input files generated in {1} experiments.".format(
            sum([len(files) for r, d, files in os.walk(self.cmdopts['generation_root'])]),
            sum([len(d) for r, d, files in os.walk(self.cmdopts['generation_root'])])))

        # Computed during input generation and needed later for graph generation; not part of
        # default cmdopts dict so we grab it here
        # self.cmdopts['arena_dim'] = self.generator.cmdopts['arena_dim']
