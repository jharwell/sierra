"""
 Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

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
import random
import pickle
from pipeline.xml_luigi import XMLLuigi, InvalidElementError
from variables import time_setup, physics_engines, block_distribution


class ExpInputGenerator:

    """
    Base class for generating:

    1. A set of ARGoS simulation input files from a template for a *single* experiment.
    2. A command file with commands to run each simulation suitable for input into GNU Parallel for
       a *single* experiment.

    Attributes:
      template_config_path(str): Path(relative to current dir or absolute) to the template XML
                                 configuration file.
      generation_root(str): Where generated XML input files for ARGoS for this experiment should be
                            stored(relative to current dir or absolute).
      exp_output_root(str): Root directory for simulation outputs for this experiment (sort of a
                            scratch directory). Can be relative or absolute.
      exp_def_fname(str): Name of file to use for pickling experiment definitions.
      sim_opts(dict): Dictionary containing the following keys:
                      n_sims : # of simulations to run in parallel
                      n_threads: # of ARGoS threads to use for each parallel simulation
                      tsetup: Name of class in time_setup.py to use for simulation time setup.
                      n_physics_engines: # of ARGoS physics engines to use.
                      arena_dim: (X,Y) dimensions of the arena.
                      with_robot_rab(bool): Should the range and bearing sensors/actuators be
                                            enabled?
                      with_robot_leds(bool): Should the LED actuators be enabled?
                      with_robot_battery(bool): Should the battery sensor be enabled?
    """

    def __init__(self, template_config_file, generation_root, exp_output_root, exp_def_fname,
                 sim_opts):
        assert os.path.isfile(template_config_file), \
            "The path '{}' (which should point to the main config file) did not point to a file".format(
                template_config_file)
        self.template_config_file = os.path.abspath(template_config_file)

        # will get the main name and extension of the config file (without the full absolute path)
        self.main_config_name, self.main_config_extension = os.path.splitext(
            os.path.basename(self.template_config_file))

        # where the generated config and command files should be stored
        self.generation_root = os.path.abspath(generation_root)

        assert self.generation_root.find(" ") == -1, \
            ("ARGoS (apparently) does not support running configuration files with spaces in the " +
             "Please make sure the configuration file save path '{}' does not have any spaces in it").format(self.generation_root)

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.sim_opts = sim_opts
        self.exp_def_fpath = os.path.join(self.generation_root, exp_def_fname)

        self.random_seed_min = 1
        self.random_seed_max = 10 * self.sim_opts["n_sims"]

        # where the commands file will be stored
        self.commands_fpath = os.path.abspath(
            os.path.join(self.generation_root, "commands.txt"))

        # to be formatted like: self.config_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.config_name_format = format_base + self.main_config_extension
        self.output_name_format = format_base + "_output"

    def generate_common_defs(self):
        """
        Generates simulation definitions common to all simulations:

        - visualizations
        - threading
        - robot sensor/actuators
        - simulation time parameters

        This only generates base definitions, but does not actually generate any modified input
        files.
        """
        # create an object that will edit the XML file
        xml_luigi = XMLLuigi(self.template_config_file)

        # make the save path
        os.makedirs(self.generation_root, exist_ok=True)

        # Clear out commands_path if it already exists
        if os.path.exists(self.commands_fpath):
            os.remove(self.commands_fpath)

        # Setup simulation visualizations
        self._generate_visualization_defs(xml_luigi)

        # Setup threading
        self._generate_threading_defs(xml_luigi)

        # Setup robot sensors/actuators
        self._generate_sa_defs(xml_luigi)

        # Setup simulation time parameters
        self._generate_time_defs(xml_luigi)

        return xml_luigi

    def generate_inputs(self, xml_luigi):
        """
        Generates and saves the input files for all simulation runs within the experiment.
        """
        random_seeds = self._generate_random_seeds()
        for exp_num in range(self.sim_opts["n_sims"]):
            self._create_sim_input_file(random_seeds, xml_luigi, exp_num)
            self._add_sim_to_command_file(os.path.join(self.generation_root,
                                                       self.config_name_format.format(
                                                           self.main_config_name, exp_num)))

    def generate_physics_defs(self, xml_luigi):
        """Generates definitions for physics engines configuration for the simulation.

        This cannot be done as part of generate_common_defs(), as this class is reused for
        generators for BOTH controller and scenario, and the arena dimensions are None for
        configuring controllers.

        """
        pe = physics_engines.PhysicsEngines(self.sim_opts["n_physics_engines"],
                                            self.sim_opts["physics_iter_per_tick"],
                                            "uniform_grid",
                                            self.sim_opts["arena_dim"])
        [xml_luigi.tag_remove(a[0], a[1]) for a in pe.gen_tag_rmlist()[0]]
        [xml_luigi.tag_add(a[0], a[1], a[2]) for a in pe.gen_tag_addlist()[0]]

    def generate_block_count_defs(self, xml_luigi):
        """
        Generates definitions for # blocks in the simulation from command line overrides.
        """
        bd = block_distribution.Quantity([self.sim_opts['n_blocks']])
        [xml_luigi.attribute_change(a[0], a[1], a[2]) for a in bd.gen_attr_changelist()[0]]
        rms = bd.gen_tag_rmlist()

        if len(rms):
            [xml_luigi.tag_remove(a) for a in rms[0]]

    def _generate_time_defs(self, xml_luigi):
        """
        Setup simulation time parameters and write them to the pickle file for retrieval during
        graph generation later.
        """
        setup = __import__("variables.{0}".format(
            self.sim_opts["time_setup"].split(".")[0]), fromlist=["*"])
        tsetup_inst = getattr(setup, "Factory")(self.sim_opts["time_setup"])()
        for a in tsetup_inst.gen_attr_changelist()[0]:
            xml_luigi.attribute_change(a[0], a[1], a[2])

        # Write time setup  info to file for later retrieval
        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(tsetup_inst.gen_attr_changelist()[0], f)

    def _generate_sa_defs(self, xml_luigi):
        """
        Disable selected sensors/actuators, which are computationally expensive in large swarms, but
        not that costly if the # robots is small.
        """
        if not self.sim_opts["with_robot_rab"]:
            xml_luigi.tag_remove(".//media", "range_and_bearing")
            xml_luigi.tag_remove(".//actuators", "range_and_bearing")
            xml_luigi.tag_remove(".//sensors", "range_and_bearing")

        if not self.sim_opts["with_robot_leds"]:
            xml_luigi.tag_remove(".//actuators", "leds")

        if not self.sim_opts["with_robot_battery"]:
            xml_luigi.tag_remove(".//sensors", "battery")
            xml_luigi.tag_remove(".//entity/foot-bot", "battery")

    def _generate_threading_defs(self, xml_luigi):
        """
        Set the # of cores for a simulation to use, which may be less than the total # available on
        the system.
        """
        xml_luigi.attribute_change(".//system",
                                   "threads",
                                   str(self.sim_opts["n_threads"]))
        xml_luigi.attribute_change(".//loop_functions/convergence",
                                   "n_threads",
                                   str(self.sim_opts["n_threads"]))

    def _generate_visualization_defs(self, xml_luigi):
        """
        Remove visualization elements from input file, if configured to do so. It may be desired to
        leave them in if generating frames/video.
        """
        if self.sim_opts["with_visualizations"] == "none" or self.sim_opts["with_visualizations"] == "argos":
            xml_luigi.tag_remove("./loop_functions", "./visualization")

        if self.sim_opts["with_visualizations"] == "none" or self.sim_opts["with_visualizations"] == "fordyca":
            xml_luigi.tag_remove(".", "./visualization")

    def _generate_random_defs(self, xml_luigi, random_seeds, exp_num):
        """
        Generate random seed definitions for a specific simulation in an experiment during the
        input generation process. This cannot be done in init_sim_defs() because it is *not* common
        to all experiments; each experiment has their own random seed.
        """

        # get the random seed for this experiment
        random_seed = random_seeds[exp_num]

        # set the random seed in the config file
        xml_luigi.attribute_change(".//experiment", "random_seed", str(random_seed))

    def _generate_output_defs(self, xml_luigi, exp_num):
        """
        Generate output definitions for a specific simulation in an experiment during the input
        generation process. This cannot be done in init_sim_defs(), because it is *not* common to
        all experiments; each experiment logs/outputs to a unique directory.
        """
        output_dir = self.output_name_format.format(
            self.main_config_name, exp_num)
        xml_luigi.attribute_change(
            ".//controllers/*/params/output/sim", "output_dir", output_dir)
        xml_luigi.attribute_change(
            ".//controllers/*/params/output/sim", "output_root", self.exp_output_root)
        xml_luigi.attribute_change(
            ".//loop_functions/output/sim", "output_dir", output_dir)
        xml_luigi.attribute_change(
            ".//loop_functions/output/sim", "output_root", self.exp_output_root)

    def _create_sim_input_file(self, random_seeds, xml_luigi, exp_num):
        """
        Write the input files for a particular simulation run.
        """

        # create a new name for this experiment's config file
        new_config_name = self.config_name_format.format(
            self.main_config_name, exp_num)

        # Setup simulation random seed
        self._generate_random_defs(xml_luigi, random_seeds, exp_num)

        # Setup simulation logging/output
        self._generate_output_defs(xml_luigi, exp_num)

        save_path = os.path.join(self.generation_root, new_config_name)
        xml_luigi.output_filepath = save_path
        open(save_path, 'w').close()  # create an empty file

        # save the config file to the correct place
        xml_luigi.write()

    def _add_sim_to_command_file(self, xml_fname):
        """Adds the command to run a particular simulation definition to the command file."""

        # Specify ARGoS invocation in generated command file per cmdline arguments.
        parts = self.sim_opts['exec_method'].split('.')

        if 1 == len(parts):
            argos_cmd = 'argos3'
        else:
            argos_cmd = 'argos3-' + parts[1]

        with open(self.commands_fpath, "a") as commands_file:
            commands_file.write(
                argos_cmd + ' -c "{}" --log-file /dev/null --logerr-file /dev/null\n'.format(xml_fname))

    def _generate_random_seeds(self):
        """Generates random seeds for experiments to use."""
        try:
            return random.sample(range(self.random_seed_min, self.random_seed_max + 1), self.sim_opts["n_sims"])
        except ValueError:
            # create a new error message that clarifies the previous one
            raise ValueError("Too few seeds for the required experiment amount; change the random seed parameters") from None
