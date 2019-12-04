# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
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
import pickle
import typing as tp
import logging

from core.xml_luigi import XMLLuigi
from core.variables import physics_engines
from core.variables import batch_criteria as bc
from core.variables import constant_density
import core.generators.generator_factory as gf
import core.generators.scenario_generator_parser as sgp


class ExpDefCommonGenerator:
    """
    Base class for generating sets of changes to a template input file that will form the definition
    for a single experiment within a batch (a separate step from writing out a set of files from the
    generated changes).

    Attributes:
        template_input_file: Path(relative to current dir or absolute) to the template XML
                             configuration file.
        exp_def_fname: Path to file to use for pickling experiment definitions.
        cmdopts: Dictionary containing parsed cmdline options.
    """

    def __init__(self,
                 template_input_file: str,
                 exp_def_fpath: str,
                 cmdopts: tp.Dict[str, str]):

        self.template_input_file = os.path.abspath(template_input_file)
        self.cmdopts = cmdopts
        self.exp_def_fpath = exp_def_fpath

    def generate(self):
        """
        Generates XML changes to simulation input files that are common to all simulations

        - visualizations
        - threading
        - simulation time parameters

        """
        # create an object that will edit the XML file
        xml_luigi = XMLLuigi(self.template_input_file)

        # Setup simulation visualizations
        self.__generate_visualization(xml_luigi)

        # Setup threading
        self.__generate_threading(xml_luigi)

        # Setup robot sensors/actuators
        self.__generate_sa(xml_luigi)

        # Setup simulation time parameters
        self.__generate_time(xml_luigi, self.exp_def_fpath)

        # Setup physics
        self.__generate_physics(xml_luigi)

        return xml_luigi

    def __generate_physics(self, xml_luigi: XMLLuigi):
        """
        Generates XML changes for the specified physics engines configuration for the
        simulation.

        Does not write generated changes to the simulation definition pickle file.


        """
        # This will need to change when I get to the point of mixing 2D and 3D physics engines
        pe = physics_engines.factory(self.cmdopts, [self.cmdopts['arena_dim']])

        [xml_luigi.tag_remove(a[0], a[1]) for a in pe.gen_tag_rmlist()[0]]
        [xml_luigi.tag_add(a[0], a[1], a[2]) for a in pe.gen_tag_addlist()[0]]

    def __generate_sa(self, xml_luigi: XMLLuigi):
        """
        Generates XML changes to disable selected sensors/actuators, which are computationally
        expensive in large swarms, but not that costly if the # robots is small.

        Does not write generated changes to the simulation definition pickle file.
        """
        if not self.cmdopts["with_robot_rab"]:
            xml_luigi.tag_remove(".//media", "range_and_bearing", noprint=True)
            xml_luigi.tag_remove(".//actuators", "range_and_bearing", noprint=True)
            xml_luigi.tag_remove(".//sensors", "range_and_bearing", noprint=True)

        if not self.cmdopts["with_robot_leds"]:
            xml_luigi.tag_remove(".//actuators", "leds", noprint=True)

        if not self.cmdopts["with_robot_battery"]:
            xml_luigi.tag_remove(".//sensors", "battery", noprint=True)
            xml_luigi.tag_remove(".//entity/foot-bot", "battery", noprint=True)

    def __generate_time(self, xml_luigi: XMLLuigi, exp_def_fpath: str):
        """
        Generate XML changes to setup simulation time parameters.

        Writes generated changes to the simulation definition pickle file.
        """
        setup = __import__("core.variables.{0}".format(
            self.cmdopts["time_setup"].split(".")[0]), fromlist=["*"])
        tsetup_inst = getattr(setup, "factory")(self.cmdopts["time_setup"])()

        for a in tsetup_inst.gen_attr_changelist()[0]:
            xml_luigi.attr_change(a[0], a[1], a[2])

        # Write time setup info to file for later retrieval
        with open(exp_def_fpath, 'ab') as f:
            pickle.dump(tsetup_inst.gen_attr_changelist()[0], f)

    def __generate_threading(self, xml_luigi: XMLLuigi):
        """
        Generates XML changes to set the # of cores for a simulation to use, which may be less than
        the total # available on the system, depending on the experiment definition and user
        preferences.

        Does not write generated changes to the simulation definition pickle file.
        """

        xml_luigi.attr_change(".//system",
                              "threads",
                              str(self.cmdopts["n_threads"]))

        # This whole tree can be missing and that's fine
        if xml_luigi.has_tag(".//loop_functions/convergence"):
            xml_luigi.attr_change(".//loop_functions/convergence",
                                  "n_threads",
                                  str(self.cmdopts["n_threads"]))

    def __generate_visualization(self, xml_luigi: XMLLuigi):
        """
        Generates XML changes to remove visualization elements from input file, if configured to do
        so. This dependent on cmdline parameters, as visualization definitions should be left in if
        ARGoS should output simulation frames for video creation.

        Does not write generated changes to the simulation definition pickle file.
        """
        if not self.cmdopts["with_rendering"]:
            xml_luigi.tag_remove(".", "./visualization", noprint=True)  # ARGoS visualizations


class BatchedExpDefGenerator:
    """
    Class for generating experiment definitions for a batched experiment. Does not create the
    batched experiment after generation.

    Attributes:
        batch_config_template: Path (relative to current dir or absolute) to the root template
                               XML configuration file.

        batch_generation_root: Root directory for all generated XML input files all experiments
                               should be stored (relative to current dir or absolute). Each
                               experiment will get a directory within this root to store the xml
                               input files for the simulation runs comprising an experiment;
                               directory name determined by the batch criteria used.

        batch_output_root: Root directory for all experiment outputs (relative to current dir or
                           absolute). Each experiment will get a directory 'exp<n>' in this
                           directory for its outputs.

        criteria: :class:`~variables.batch_criteria.BatchCriteria` derived object instance created
                  from cmdline definition.
        controller_name: Name of controller generator to use.
        scenario_basename: Name of scenario generator to use.

    """

    def __init__(self,
                 batch_config_template: str,
                 criteria: bc.BatchCriteria,
                 controller_name: str,
                 scenario_basename: str,
                 cmdopts: tp.Dict[str, str]):
        assert os.path.isfile(
            batch_config_template), \
            "The path '{}' (which should point to the main config file) did not point to a file".format(
                batch_config_template)
        self.batch_config_template = os.path.abspath(batch_config_template)
        self.batch_config_leaf, _ = os.path.splitext(
            os.path.basename(self.batch_config_template))
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

    def generate_defs(self):
        """
        Generates and returns a list of experiment definitions which can used to create the batched
        experiment.
        """
        # Create and run generators
        exp_defs = self.criteria.gen_attr_changelist()
        defs = []
        for i in range(0, len(exp_defs)):
            generator = self.__create_exp_generator(i)
            defs.append(generator.generate())
            logging.debug("Generating scenario+controller changes from generator '{0}' for exp{1}".format(self.cmdopts['joint_generator'],
                                                                                                          i))

        return defs

    def __create_exp_generator(self, exp_num: int):
        """
        Create the generator for a particular experiment from the scenario+controller definitions
        specified on the command line.

        Arguments:
            exp_num: Experiment number in the batch
        """
        # Need to get per-experiment arena dimensions from batch criteria, as they are different
        # for each experiment
        from_bivar_bc1 = (self.criteria.is_bivar() and isinstance(self.criteria.criteria1,
                                                                  constant_density.ConstantDensity))
        from_bivar_bc2 = (self.criteria.is_bivar() and isinstance(self.criteria.criteria2,
                                                                  constant_density.ConstantDensity))
        from_univar_bc = (self.criteria.is_univar() and isinstance(self.criteria,
                                                                   constant_density.ConstantDensity))
        if from_univar_bc:
            self.cmdopts["arena_dim"] = self.criteria.arena_dims()[exp_num]
            eff_scenario_name = self.criteria.exp_scenario_name(exp_num)
            logging.debug("Obtained scenario dimensions '%s' from univariate batch criteria",
                          self.cmdopts['arena_dim'])
        elif from_bivar_bc1 or from_bivar_bc2:
            self.cmdopts["arena_dim"] = self.criteria.arena_dims()[exp_num]
            logging.debug("Obtained scenario dimensions '%s' bivariate batch criteria",
                          self.cmdopts['arena_dim'])
            eff_scenario_name = self.criteria.exp_scenario_name(exp_num)
        else:  # Defaultc case: scenario dimensions read from cmdline
            kw = sgp.ScenarioGeneratorParser.reparse_str(self.scenario_basename)
            self.cmdopts["arena_dim"] = (kw['arena_x'], kw['arena_y'], kw['arena_z'])
            logging.debug("Read scenario dimensions %s from cmdline spec",
                          self.cmdopts['arena_dim'])

            eff_scenario_name = self.scenario_basename

        exp_generation_root = os.path.join(self.batch_generation_root,
                                           self.criteria.gen_exp_dirnames(self.cmdopts)[exp_num])

        scenario = gf.ScenarioGeneratorfactory(controller=self.controller_name,
                                               scenario=eff_scenario_name,
                                               template_input_file=os.path.join(exp_generation_root,
                                                                                self.batch_config_leaf),
                                               exp_def_fpath=os.path.join(exp_generation_root,
                                                                          "exp_def.pkl"),
                                               cmdopts=self.cmdopts)

        controller = gf.ControllerGeneratorfactory(controller=self.controller_name,
                                                   config_root=self.cmdopts['plugin_config_root'],
                                                   cmdopts=self.cmdopts)

        self.cmdopts['joint_generator'] = '+'.join([controller.__class__.__name__,
                                                    scenario.__class__.__name__])

        return gf.JointGeneratorfactory(scenario=scenario,
                                        controller=controller)
