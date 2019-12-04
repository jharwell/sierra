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
import random
import typing as tp
import logging

from core.xml_luigi import XMLLuigi
from core.variables import batch_criteria as bc


class SimDefUniqueGenerator:
    """
    Generate XML changes unique to a simulation within an experiment.

    These include:
    - Random seeds for each simulation.
    - Output directories for each simulation.

    Attributes:
        sim_num: The simulation # in the experiment.
        sim_output_dir: Directory for simulation outputs in experiment root.
        cmdopts: Dictionary containing parsed cmdline options.
    """

    def __init__(self,
                 sim_num: int,
                 exp_output_root: str,
                 sim_output_dir: str,
                 cmdopts: tp.Dict[str, str]):

        self.exp_output_root = exp_output_root
        self.sim_output_dir = sim_output_dir
        self.cmdopts = cmdopts
        self.sim_num = sim_num

    def generate(self, xml_luigi: XMLLuigi, random_seeds):
        # Setup simulation random seed
        SimDefUniqueGenerator.__generate_random(xml_luigi, random_seeds[self.sim_num])

        # Setup simulation logging/output
        self.__generate_output(xml_luigi)

    @staticmethod
    def __generate_random(xml_luigi, random_seed):
        """
        Generate XML changes for random seeding for a specific simulation in an experiment during
        the input generation process.
        """

        # set the random seed in the config file
        xml_luigi.attr_change(".//experiment", "random_seed", str(random_seed))
        if xml_luigi.has_tag('.//params/rng'):
            xml_luigi.attr_change(".//params/rng", "seed", str(random_seed))
        else:
            xml_luigi.tag_add(".//params", "rng", {"seed": str(random_seed)})

    def __generate_output(self, xml_luigi: XMLLuigi):
        """
        Generates XML changes for a specific simulation in an experiment during the input
        generation process.
        """
        frames_fpath = os.path.join(self.exp_output_root, self.sim_output_dir, "frames")

        xml_luigi.attr_change(
            ".//controllers/*/params/output", "output_dir", self.sim_output_dir)

        xml_luigi.attr_change(
            ".//controllers/*/params/output", "output_root", self.exp_output_root)
        xml_luigi.attr_change(
            ".//loop_functions/output", "output_dir", self.sim_output_dir)
        xml_luigi.attr_change(
            ".//loop_functions/output", "output_root", self.exp_output_root)
        xml_luigi.attr_change(
            ".//qt-opengl/frame_grabbing",
            "directory", frames_fpath, noprint=True)  # probably will not be present


class ExpCreator:
    """
    Create the experiment from the specified experiment definition by writing out simulation input
    files and setting up the necessary directory structure after the experiment has been generated.

    Attributes:
        template_input_file: Path(relative to current dir or absolute) to the template XML
                             configuration file.
        generation_root: Absolute path to experiment directory where generated XML input files for
                         ARGoS for this experiment should be written.
        exp_output_root: Absolute path to root directory for simulation outputs for this experiment
                         (sort of a scratch directory).
        cmdopts: Dictionary containing parsed cmdline options.
    """

    def __init__(self,
                 template_input_file: str,
                 exp_generation_root: str,
                 exp_output_root: str,
                 cmdopts: tp.Dict[str, str]):

        # will get the main name and extension of the config file (without the full absolute path)
        self.main_input_name, self.main_input_extension = os.path.splitext(
            os.path.basename(os.path.abspath(template_input_file)))

        # where the generated config and command files should be stored
        self.exp_generation_root = os.path.abspath(exp_generation_root)

        assert self.exp_generation_root.find(" ") == -1, \
            ("ARGoS(apparently) does not support input file paths with in the name--remove spaces"
             "from {0} and try again".format(self.exp_generation_root))

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.cmdopts = cmdopts

        self.random_seed_min = 1
        self.random_seed_max = 10 * self.cmdopts["n_sims"]

        # where the commands file will be stored
        self.commands_fpath = os.path.abspath(
            os.path.join(self.exp_generation_root, "commands.txt"))

    def from_def(self, exp_def: XMLLuigi):
        """
        Given a :class:`~xml_luigi.XMLLuigi` object containing all changes that should be made to all
        simulations in the experiment, use :class:`SimDefUniqueGenerator` to create addition changes
        unique to each simulation and then write out files to the filesystem.
        """
        os.makedirs(self.exp_generation_root, exist_ok=True)

        seeds = self.__generate_random_seeds()

        for sim_num in range(self.cmdopts['n_sims']):
            sim_output_dir = "{0}_{1}_output".format(self.main_input_name, sim_num)
            SimDefUniqueGenerator(sim_num,
                                  self.exp_output_root,
                                  sim_output_dir,
                                  self.cmdopts).generate(exp_def, seeds)

            # Finally, write out the simulation input file for ARGoS
            save_path = self.__get_sim_input_path(sim_num)
            open(save_path, 'w').close()  # create an empty file
            exp_def.write(save_path)

            if self.cmdopts['with_rendering']:
                frames_fpath = os.path.join(self.exp_output_root, sim_output_dir, "frames")
                os.makedirs(frames_fpath, exist_ok=True)

        # Clear out commands file if it exists
        if os.path.exists(self.commands_fpath):
            os.remove(self.commands_fpath)

        # Write the GNU Parallel commands input file
        with open(self.commands_fpath, 'w+') as cmds_file:
            for sim_num in range(self.cmdopts['n_sims']):
                self.__update_cmds_file(cmds_file, self.__get_sim_input_path(sim_num))

    def __get_sim_input_path(self, sim_num):
        """
        File is named as ``<template input file stem>_<sim_num>`` in the generation root.
        """
        return os.path.join(self.exp_generation_root,
                            "{0}_{1}".format(self.main_input_name, sim_num))

    def __update_cmds_file(self, cmds_file, sim_input_path):
        """Adds the command to run a particular simulation definition to the command file."""

        # Specify ARGoS invocation in generated command file per cmdline arguments. An option is
        # provided to tweak the exact name of the program used to invoke ARGoS so that different
        # versions compiled for different architectures/machines that exist on the same filesystem
        # can easily be run.
        if 'local' in self.cmdopts['exec_method']:
            argos_cmd = 'argos3'
        else:
            if self.cmdopts['hpc_env'] == 'MSI':
                argos_cmd = 'argos3-' + os.environ['MSICLUSTER']

        # When running ARGoS under Xvfb in order to headlessly render frames, we need to start a
        # per-instance Xvfb server that we tell ARGoS to use via the DISPLAY environment variable,
        # which will then be killed when the shell GNU parallel spawns to run each line in the
        # commands.txt file exits.
        xvfb_cmd = ""
        if self.cmdopts['with_rendering']:
            display_port = random.randint(0, 1000000)
            xvfb_cmd = "eval 'Xvfb :{0} -screen 0, 1600x1200x24 &' && DISPLAY=:{0} ".format(
                display_port)

        cmds_file.write(xvfb_cmd +
                        argos_cmd +
                        ' -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(
                            sim_input_path))

    def __generate_random_seeds(self):
        """Generates random seeds for experiments to use."""
        try:
            return random.sample(range(self.random_seed_min, self.random_seed_max + 1),
                                 self.cmdopts["n_sims"])
        except ValueError:
            # create a new error message that clarifies the previous one
            raise ValueError("# seeds < # sims: change the random seed parameters")


class BatchedExpCreator:
    """
    Class for generating experiment definitions for a batched experiment. Does not create the
    batched experiment after generation.

    Attributes:
        batch_config_template: Path (relative to current dir or absolute) to the root template
                               XML configuration file.
        batch_generation_root: Root directory for all generated XML input files all experiments should
                               be stored (relative to current dir or absolute). Each experiment will
                               get a directory within this root to store the xml input files for the
                               simulation runs comprising an experiment; directory name determined by
                               the batch criteria used.
        batch_output_root: Root directory for all experiment outputs (relative to current dir or
                           absolute). Each experiment will get a directory 'exp<n>' in this
                           directory for its outputs.
        criteria: :class:`~variables.batch_criteria.BatchCriteria` derived object instance created
                  from cmdline definition.
    """

    def __init__(self,
                 batch_config_template: str,
                 batch_generation_root: str,
                 batch_output_root: str,
                 criteria: bc.BatchCriteria,
                 cmdopts: tp.Dict[str, str]):

        self.batch_config_template = batch_config_template
        self.batch_config_leaf, _ = os.path.splitext(
            os.path.basename(self.batch_config_template))

        self.batch_generation_root = batch_generation_root
        self.batch_output_root = batch_output_root
        self.criteria = criteria
        self.cmdopts = cmdopts

    def create(self, generator):
        """
        """
        os.makedirs(self.batch_generation_root, exist_ok=True)

        # Scaffold the batched experiment, creating experiment directories and writing template XML
        # input files for each experiment in the batch with changes from the batch criteria added
        self.criteria.scaffold_exps(XMLLuigi(self.batch_config_template),
                                    self.batch_config_leaf,
                                    self.cmdopts)

        # Pickle experiment definitions in the actual batched experiment directory for later
        # retrieval
        self.criteria.pickle_exp_defs(self.cmdopts)

        # Run batched experiment generator (must be after scaffolding so the per-experiment template
        # files are in place)
        defs = generator.generate_defs()

        for i, defi in enumerate(defs):
            logging.debug("Applying generated scenario+controller changes to exp%s", i)
            exp_output_root = os.path.join(self.batch_output_root,
                                           self.criteria.gen_exp_dirnames(self.cmdopts)[i])
            exp_generation_root = os.path.join(self.batch_generation_root,
                                               self.criteria.gen_exp_dirnames(self.cmdopts)[i])

            ExpCreator(self.batch_config_template,
                       exp_generation_root,
                       exp_output_root,
                       self.cmdopts).from_def(defi)
