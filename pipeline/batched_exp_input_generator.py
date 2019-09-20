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
from generators.generator_factory import ControllerGeneratorFactory
import batch_utils as butils


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
                                  experiment will get a directory within this root to store
                                  the xml input files for the simulation runs comprising an
                                  experiment; directory name determined by the batch criteria used.
      batch_output_root(str): Root directory for all experiment outputs (relative to current dir or
                              absolute). Each experiment will get a directory 'exp<n>' in this
                              directory for its outputs.
      batch_criteria(list): List of sets, where each entry in the inner list is a list of tuples
                            of changes to make to the main template XML file for each experiment.
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
        self.exp_generator_pair = exp_generator_pair
        self.batch_criteria = batch_criteria
        self.sim_opts = sim_opts
        self.sim_opts['n_exp'] = len(self.batch_criteria)
        self.sim_opts['generation_root'] = self.batch_generation_root

    def generate(self):
        """
        Generates and saves all the input files for all experiments in the batch.
        """

        # create experiment input XML templates
        xml_luigi = XMLLuigi(self.batch_config_template)
        exp_defs = list(self.batch_criteria)  # Needs to be a list for indexing

        # Cleanup temporary pkl files (we may have crashed last time we ran)
        self.__cleanup_pkl_files(exp_defs)

        # Create temporary pkl files to use during directory creation (needed for extraction of
        # correct directory naming scheme based on batch criteria)
        for i in range(0, len(exp_defs)):
            pkl_path = '/tmp/sierra_pkl{0}.pkl'.format(i)
            with open(pkl_path, 'ab') as f:
                pickle.dump(exp_defs[i], f)

        for i in range(0, len(exp_defs)):
            self.__scaffold_exp(xml_luigi, exp_defs[i], i)

        exp_dirnames = butils.exp_dirnames(self.sim_opts)
        assert len(exp_defs) == len(exp_dirnames),\
            "FATAL: Size of batch criteria({0}) != # exp dirs ({1}): possibly caused by duplicate "\
            "named exp dirs... ".format(len(exp_defs),
                                        len(exp_dirnames))

        # Pickle experiment definitions for later retrieval in experiment directories
        self.__pkl_exp_defs(exp_defs)

        # Cleanup temporary pkl files after experiment directory creation
        self.__cleanup_pkl_files(exp_defs)

        # Create and run generators
        for i in range(0, len(exp_defs)):
            generator = self.__create_exp_generator(exp_defs[i], i)
            generator.generate()

    def __cleanup_pkl_files(self, exp_defs):
        """
        Cleanup the temporary .pkl files written as part of experiment scaffolding.
        """
        for i in range(0, len(exp_defs)):
            pkl_path = '/tmp/sierra_pkl{0}.pkl'.format(i)
            if os.path.exists(pkl_path):
                os.remove(pkl_path)

    def __scaffold_exp(self, xml_luigi, exp_def, exp_num):
        """
        Scaffold an experiment within the batch:

        - Create experiment directories for each experiment in the batch
        - Write the ARGoS input file for the experiment to the experiment directory after the
          changes for the batch criteria have been applied. This file becomes the template config
          file for each experiment to which the scenario+controllers changes are then applied.
        """
        exp_dirname = butils.exp_dirname(self.sim_opts, exp_num, True)
        exp_generation_root = os.path.join(self.batch_generation_root, str(exp_dirname))
        os.makedirs(exp_generation_root, exist_ok=True)

        for path, attr, value in exp_def:
            xml_luigi.attribute_change(path, attr, value)

        xml_luigi.output_filepath = os.path.join(exp_generation_root, self.batch_config_leaf)
        xml_luigi.write()

    def __pkl_exp_defs(self, exp_defs):
        """
        Pickle experiment changes to a .pkl file in the experiment root for each experiment in the
        batch for retrieval in later stages.
        """
        for i in range(0, len(exp_defs)):
            exp_dirname = butils.exp_dirname(self.sim_opts, i, True)
            with open(os.path.join(self.batch_generation_root,
                                   exp_dirname,
                                   'exp_def.pkl'), 'ab') as f:
                pickle.dump(exp_defs[i], f)

    def __create_exp_generator(self, exp_def, exp_num):
        """
        Create the generator for a particular experiment from the batch criteria+controller
        definitions specified on the command line.

        exp_def(set): Set of XML changes to apply to the template input file for the experiment.
        exp_num(int): Experiment number in the batch
        """
        self.sim_opts["arena_dim"] = None
        scenario = None
        # The scenario dimensions were specified on the command line
        # Format of '(<decomposition depth>.<controller>.[SS,DS,QS,RN,PL]>'
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

        exp_generation_root = os.path.join(self.batch_generation_root,
                                           butils.exp_dirname(self.sim_opts, exp_num))
        exp_output_root = os.path.join(self.batch_output_root,
                                       butils.exp_dirname(self.sim_opts, exp_num))

        controller_name = self.exp_generator_pair[0]
        scenario_name = 'generators.' + scenario

        # Scenarios come from a canned set, which is why we have to look up their generator
        # class rather than being able to create the class on the fly as with controllers.
        scenario = ScenarioGeneratorFactory(controller=controller_name,
                                            scenario=scenario_name,
                                            template_config_file=os.path.join(exp_generation_root,
                                                                              self.batch_config_leaf),
                                            generation_root=exp_generation_root,
                                            exp_output_root=exp_output_root,
                                            exp_def_fname="exp_def.pkl",
                                            sim_opts=self.sim_opts)

        controller = ControllerGeneratorFactory(controller=controller_name,
                                                config_root=self.sim_opts['config_root'],
                                                template_config_file=os.path.join(exp_generation_root,
                                                                                  self.batch_config_leaf),
                                                generation_root=exp_generation_root,
                                                exp_output_root=exp_output_root,
                                                exp_def_fname="exp_def.pkl",
                                                sim_opts=self.sim_opts)

        print("-- Created joint generator class '{0}'".format('+'.join([controller.__class__.__name__,
                                                                        scenario.__class__.__name__])))

        return GeneratorPairFactory(scenario=scenario,
                                    controller=controller,
                                    template_config_file=os.path.join(exp_generation_root,
                                                                      self.batch_config_leaf),
                                    generation_root=exp_generation_root,
                                    exp_output_root=exp_output_root,
                                    exp_def_fname="exp_def.pkl",
                                    sim_opts=self.sim_opts)
