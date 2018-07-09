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
from xml_helper import XMLHelper


class BatchedExpInputGenerator:

    """
    Class for generating:

    1. A set of ARGoS simulation input files from a template for a set of experiments.
    2. A command file with commands to run each simulation suitable for input into GNU Parallel for
       a set of experiments .
    3. An experiment definition file for each experiment, containing what values of the batch
       criteria are present in the input files.

    Attributes:
      batch_config_template(str): Path (relative to current dir or absolute) to the root template XML configuration
                                  file.
      batch_generation_root(str): Root directory for all generated XML input files all experiments should be stored
                                  (relative to current dir or absolute). Each experiment will get a directory 'exp<n>'
                                  within this root to store the xml input files for the simulation runs comprising an
                                  experiment.
      batch_output_root(str): Root directory for all experiment outputs (relative to current dir or absolute). Each
                              experiment will get a directory 'exp<n>' in this directory for its outputs.
      batch_criteria(list): List of lists, where each entry in the inner list is a list of (xml tag, value) pairs to be
                            replaced in the main template XML file for each experiment.
      exp_generator_cname(class): Class name of experiment input generator to use.
      n_sims(int): Number of simulations to run in parallel.
      n_threads(int): Number of ARGoS simulation threads to use.
      random_seed_min(int): Minimum random seed for the experiment. Defaults to 1.
      random_seed_max(int): Maximum random seed for the experiment. Defaults to 10 * n_s.
    """

    def __init__(self, batch_config_template, batch_generation_root, batch_output_root, batch_criteria,
                 exp_generator_cname, n_sims, n_threads, random_seed_min=None, random_seed_max=None):
        assert os.path.isfile(
            batch_config_template), "The path '{}' (which should point to the main config file) did not point to a file".format(batch_config_template)
        self.batch_config_template = os.path.abspath(batch_config_template)

        # will get the main name and extension of the config file (without the full absolute path)
        self.batch_config_leaf, self.batch_config_extension = os.path.splitext(
            os.path.basename(self.batch_config_template))

        self.batch_generation_root = os.path.abspath(batch_generation_root)
        assert self.batch_generation_root.find(" ") == -1, ("ARGoS (apparently) does not support running configuration files with spaces in the path. Please make sure the " +
                                                            "batch generation root directory '{}' does not have any spaces in it").format(self.batch_generation_root)

        self.batch_output_root = os.path.abspath(batch_output_root)
        self.batch_criteria = batch_criteria
        self.n_sims = n_sims
        self.n_threads = n_threads
        self.random_seed_min = random_seed_min
        self.random_seed_max = random_seed_max
        self.exp_generator_cname = exp_generator_cname

    def generate(self):
        """Generates and saves all the input files for all experiments"""

        # create experiment input XML templates
        xml_helper = XMLHelper(self.batch_config_template)
        exp_num = 0
        for exp_def in self.batch_criteria:
            exp_generation_root = "{0}/exp{1}".format(self.batch_generation_root, exp_num)
            os.makedirs(exp_generation_root, exist_ok=True)

            for xml_tag, attr in exp_def:
                xml_helper.set_attribute(xml_tag, attr)
            xml_helper.output_filepath = exp_generation_root + "/" + self.batch_config_leaf
            xml_helper.write()
            with open(exp_generation_root + '/exp_def.txt', 'w') as f:
                f.write(str(exp_def))
            exp_num += 1

        # Create and run generators
        exp_num = 0
        for exp_def in self.batch_criteria:
            exp_generation_root = "{0}/exp{1}".format(self.batch_generation_root, exp_num)
            exp_output_root = "{0}/exp{1}".format(self.batch_output_root, exp_num)
            g = self.exp_generator_cname(exp_generation_root + "/" + self.batch_config_leaf,
                                         exp_generation_root, exp_output_root, self.n_sims,
                                         self.n_threads, self.random_seed_min, self.random_seed_max)
            g.generate()
            exp_num += 1
