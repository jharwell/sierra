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
from xml_luigi import XMLLuigi
import generators.generator_factory as gf
import generators.scenario_generator_parser as sgp
import variables as ev


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
      criteria(BatchCriteria): BatchCriteria derived object instance created from cmdline definition.
      controller_name(str): Name of controller generator to use.
      scenario_basename(str): Name of scenario generator to use.
    """

    def __init__(self, batch_config_template, criteria, controller_name, scenario_basename, cmdopts):
        if batch_config_template is not None:
            assert os.path.isfile(
                batch_config_template), \
                "The path '{}' (which should point to the main config file) did not point to a file".format(
                    batch_config_template)
            self.batch_config_template = os.path.abspath(batch_config_template)
            # will get the main name and extension of the config file (without the full absolute
            # path)
            self.batch_config_leaf, self.batch_config_extension = os.path.splitext(
                os.path.basename(self.batch_config_template))
        else:
            self.batch_config_template = None
            self.batch_config_leaf = None
            self.batch_config_extension = None

        self.batch_generation_root = os.path.abspath(cmdopts['generation_root'])
        assert self.batch_generation_root.find(" ") == -1, \
            ("ARGoS (apparently) does not work with input file paths with spaces. Please make sure the " +
             "batch generation root directory '{}' does not have any spaces in it").format(self.batch_generation_root)

        self.batch_output_root = os.path.abspath(cmdopts['output_root'])

        self.controller_name = controller_name
        self.scenario_basename = scenario_basename
        self.criteria = criteria
        self.cmdopts = cmdopts

    def generate(self):
        """
        Generates and saves all the input files for all experiments in the batch.
        """
        # Scaffold the batched experiment and verify nothing is horrendously wrong
        self.criteria.scaffold_exps(XMLLuigi(self.batch_config_template),
                                    self.batch_config_leaf,
                                    self.cmdopts)

        # Pickle experiment definitions in the actual batched experiment directory for later
        # retrieval
        self.criteria.pickle_exp_defs(self.cmdopts)

        # Create and run generators
        exp_defs = self.criteria.gen_attr_changelist()
        for i in range(0, len(exp_defs)):
            generator = self.__create_exp_generator(exp_defs[i], i)
            print("-- Applying changes from generator '{0}' to exp{1}".format(self.cmdopts['joint_generator'],
                                                                              i))

            generator.generate()

    def __create_exp_generator(self, exp_def, exp_num):
        """
        Create the generator for a particular experiment from the scenario+controller definitions
        specified on the command line.

        exp_def(set): Set of XML changes to apply to the template input file for the experiment.
        exp_num(int): Experiment number in the batch
        """
        # Need to get per-experiment arena dimensions from batch criteria, as they are different
        # for each experiment
        from_bivar_bc1 = (self.criteria.is_bivar() and isinstance(self.criteria.criteria1,
                                                                  ev.constant_density.ConstantDensity))
        from_bivar_bc2 = (self.criteria.is_bivar() and isinstance(self.criteria.criteria2,
                                                                  ev.constant_density.ConstantDensity))
        from_univar_bc = (self.criteria.is_univar() and isinstance(self.criteria,
                                                                   ev.constant_density.ConstantDensity))
        if from_univar_bc:
            self.cmdopts["arena_dim"] = self.criteria.arena_dims()[exp_num]
            eff_scenario_name = self.criteria.exp_scenario_name(exp_num)
        elif from_bivar_bc1 or from_bivar_bc2:
            self.cmdopts["arena_dim"] = self.criteria.arena_dims()[exp_num]
            eff_scenario_name = self.criteria.exp_scenario_name(exp_num)
        else:
            kw = sgp.ScenarioGeneratorParser.reparse_str(self.scenario_basename)
            self.cmdopts["arena_dim"] = (kw['arena_x'], kw['arena_y'])
            eff_scenario_name = self.scenario_basename

        exp_generation_root = os.path.join(self.batch_generation_root,
                                           self.criteria.gen_exp_dirnames(self.cmdopts)[exp_num])
        exp_output_root = os.path.join(self.batch_output_root,
                                       self.criteria.gen_exp_dirnames(self.cmdopts)[exp_num])

        scenario = gf.ScenarioGeneratorFactory(controller=self.controller_name,
                                               scenario=eff_scenario_name,
                                               template_input_file=os.path.join(exp_generation_root,
                                                                                self.batch_config_leaf),
                                               generation_root=exp_generation_root,
                                               exp_output_root=exp_output_root,
                                               exp_def_fname="exp_def.pkl",
                                               cmdopts=self.cmdopts)

        controller = gf.ControllerGeneratorFactory(controller=self.controller_name,
                                                   config_root=self.cmdopts['config_root'],
                                                   template_input_file=os.path.join(exp_generation_root,
                                                                                    self.batch_config_leaf),
                                                   generation_root=exp_generation_root,
                                                   exp_output_root=exp_output_root,
                                                   exp_def_fname="exp_def.pkl",
                                                   cmdopts=self.cmdopts)

        self.cmdopts['joint_generator'] = '+'.join([controller.__class__.__name__,
                                                    scenario.__class__.__name__])

        return gf.BivarGeneratorFactory(scenario=scenario,
                                        controller=controller,
                                        template_input_file=os.path.join(exp_generation_root,
                                                                         self.batch_config_leaf),
                                        generation_root=exp_generation_root,
                                        exp_output_root=exp_output_root,
                                        exp_def_fname="exp_def.pkl",
                                        cmdopts=self.cmdopts)
