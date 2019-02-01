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
import pickle
from pipeline.xml_luigi import XMLLuigi
from generators.generator_factory import GeneratorPairFactory
from generators.generator_factory import ScenarioGeneratorFactory


class BatchedExpInputGenerator:

    """
    Class for generating:

    1. A set of ARGoS simulation input files from a template for a set of experiments.
    2. A command file with commands to run each simulation suitable for input into GNU Parallel for
       a set of experiments .
    3. An experiment definition file for each experiment, containing what values of the batch
       criteria are present in the input files.

    Attributes:
      batch_config_template(str): Path (relative to current dir or absolute) to the root template
                                  XML configuration file.
      batch_generation_root(str): Root directory for all generated XML input files all experiments
                                  should be stored (relative to current dir or absolute). Each
                                  experiment will get a directory 'exp<n>' within this root to store
                                  the xml input files for the simulation runs comprising an
                                  experiment.
      batch_output_root(str): Root directory for all experiment outputs (relative to current dir or
                              absolute). Each experiment will get a directory 'exp<n>' in this
                              directory for its outputs.
      batch_criteria(list): List of lists, where each entry in the inner list is a list of tuples
                            pairs to be replaced in the main template XML file for each experiment.
      exp_generator_pair(tuple): Pair of class names to use when creating the new generator
                                 (scenario + controller changes).
    """

    def __init__(self, batch_config_template, batch_generation_root, batch_output_root, batch_criteria,
                 exp_generator_pair, sim_opts):
        assert os.path.isfile(
            batch_config_template), \
            "The path '{}' (which should point to the main config file) did not point to a file".format(
                batch_config_template)
        self.batch_config_template = os.path.abspath(batch_config_template)

        # will get the main name and extension of the config file (without the full absolute path)
        self.batch_config_leaf, self.batch_config_extension = os.path.splitext(
            os.path.basename(self.batch_config_template))

        self.batch_generation_root = os.path.abspath(batch_generation_root)
        assert self.batch_generation_root.find(" ") == -1, \
            ("ARGoS (apparently) does not support running configuration files with spaces in the path. Please make sure the " +
             "batch generation root directory '{}' does not have any spaces in it").format(self.batch_generation_root)

        self.batch_output_root = os.path.abspath(batch_output_root)
        self.batch_criteria = batch_criteria
        self.sim_opts = sim_opts
        self.exp_generator_pair = exp_generator_pair

    def generate(self):
        """Generates and saves all the input files for all experiments"""

        # create experiment input XML templates
        xml_luigi = XMLLuigi(self.batch_config_template)
        exp_num = 0

        # Apply changes generated from batch criteria to the template input file, and generate the
        # set of input files for experiment; each file then becomes the "templae" config file for
        # generating controller/scenario changes.
        #
        # Also write changes to pickle file for later retrieval.
        for exp_def in self.batch_criteria:
            exp_generation_root = "{0}/exp{1}".format(self.batch_generation_root, exp_num)
            os.makedirs(exp_generation_root, exist_ok=True)

            for path, attr, value in exp_def:
                xml_luigi.attribute_change(path, attr, value)
            xml_luigi.output_filepath = exp_generation_root + "/" + self.batch_config_leaf
            xml_luigi.write()

            with open(os.path.join(exp_generation_root, 'exp_def.pkl'), 'ab') as f:
                pickle.dump(exp_def, f)
            exp_num += 1

        # Create and run generators
        exp_num = 0
        for exp_def in self.batch_criteria:
            self.sim_opts["arena_dim"] = None
            scenario = None
            # The scenario dimensions were specified on the command line
            # Format of '(generators.<decomposition depth>.<controller>.[SS,DS,QS,RN,PL]>'
            if "Generator" not in self.exp_generator_pair[1]:
                try:
                    x, y = self.exp_generator_pair[1].split('.')[1][2:].split('x')
                except ValueError:
                    print("FATAL: Scenario dimensions should be specified on cmdline, but they were not")
                    raise
                scenario = self.exp_generator_pair[1].split(
                    '.')[0] + "." + self.exp_generator_pair[1].split('.')[1][:2] + "Generator"
                self.sim_opts["arena_dim"] = (int(x), int(y))
            else:  # Scenario dimensions should be obtained from batch criteria
                for c in exp_def:
                    if c[0] == ".//arena" and c[1] == "size":
                        x, y, z = c[2].split(',')
                        self.sim_opts["arena_dim"] = (int(x), int(y))
                scenario = self.exp_generator_pair[1]

            exp_generation_root = "{0}/exp{1}".format(self.batch_generation_root, exp_num)
            exp_output_root = "{0}/exp{1}".format(self.batch_output_root, exp_num)

            controller_name = 'generators.' + self.exp_generator_pair[0] + "Generator"
            scenario_name = 'generators.' + scenario
            scenario = ScenarioGeneratorFactory(controller=controller_name,
                                                scenario=scenario_name,
                                                template_config_file=os.path.join(exp_generation_root,
                                                                                  self.batch_config_leaf),
                                                generation_root=exp_generation_root,
                                                exp_output_root=exp_output_root,
                                                exp_def_fname="exp_def.pkl",
                                                sim_opts=self.sim_opts)

            print("-- Created joint generator class '{0}'".format('+'.join([self.exp_generator_pair[0],
                                                                            scenario.__class__.__name__])))

            g = GeneratorPairFactory(scenario=scenario,
                                     controller=controller_name,
                                     template_config_file=os.path.join(exp_generation_root,
                                                                       self.batch_config_leaf),
                                     generation_root=exp_generation_root,
                                     exp_output_root=exp_output_root,
                                     exp_def_fname="exp_def.pkl",
                                     sim_opts=self.sim_opts)
            g.generate()
            exp_num += 1
