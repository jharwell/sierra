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
import pickle
import typing as tp
from xml_luigi import XMLLuigi
from variables import time_setup, physics_engines, block_distribution, dynamic_cache, static_cache


class ExpInputGenerator:

    """
    Base class for generating:

    - A set of ARGoS simulation input files from a template for a *single* experiment (i.e. a set
      inputs for a set of simulation runs which will eventually be averaged together).

    - A command file with commands to run each simulation suitable for input into GNU Parallel for
      a *single* experiment.

    Attributes:
        template_input_file: Path(relative to current dir or absolute) to the template XML
                             configuration file.
        generation_root: Absolute path to experiment directory where generated XML input files for
                         ARGoS for this experiment should be written.
        exp_output_root: Absolute path to root directory for simulation outputs for this experiment
                         (sort of a scratch directory).
        exp_def_fname: Name of file to use for pickling experiment definitions.
        cmdopts: Dictionary containing parsed cmdline options.
    """

    def __init__(self,
                 template_input_file: str,
                 exp_generation_root: str,
                 exp_output_root: str,
                 exp_def_fname: str,
                 cmdopts: tp.Dict[str, str]):
        assert os.path.isfile(template_input_file), \
            "The path '{}' (which should point to the main config file) did not point to a file".format(
                template_input_file)
        self.template_input_file = os.path.abspath(template_input_file)

        # will get the main name and extension of the config file (without the full absolute path)
        self.main_input_name, self.main_input_extension = os.path.splitext(
            os.path.basename(self.template_input_file))

        # where the generated config and command files should be stored
        self.exp_generation_root = os.path.abspath(exp_generation_root)

        assert self.exp_generation_root.find(" ") == -1, \
            ("ARGoS (apparently) does not support running configuration files with spaces in the " +
             "Please make sure the configuration file save path '{}' does not have any spaces in it").format(self.exp_generation_root)

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.cmdopts = cmdopts
        self.exp_def_fpath = os.path.join(self.exp_generation_root, exp_def_fname)

        self.random_seed_min = 1
        self.random_seed_max = 10 * self.cmdopts["n_sims"]

        # where the commands file will be stored
        self.commands_fpath = os.path.abspath(
            os.path.join(self.exp_generation_root, "commands.txt"))

        # to be formatted like: self.config_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.config_name_format = format_base + self.main_input_extension
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
        xml_luigi = XMLLuigi(self.template_input_file)

        # make the save path
        os.makedirs(self.exp_generation_root, exist_ok=True)

        # Clear out commands_path if it already exists
        if os.path.exists(self.commands_fpath):
            os.remove(self.commands_fpath)

        # Setup simulation visualizations
        self.__generate_visualization_defs(xml_luigi)

        # Setup threading
        self.__generate_threading_defs(xml_luigi)

        # Setup robot sensors/actuators
        self.__generate_sa_defs(xml_luigi)

        # Setup simulation time parameters
        self.__generate_time_defs(xml_luigi)

        return xml_luigi

    def generate_inputs(self, xml_luigi: XMLLuigi):
        """
        Generates and saves the input files for all simulation runs within the experiment.
        """
        random_seeds = self.__generate_random_seeds()
        for exp_num in range(self.cmdopts["n_sims"]):
            self.__create_sim_input_file(random_seeds, xml_luigi, exp_num)
            self.__add_sim_to_command_file(os.path.join(self.exp_generation_root,
                                                        self.config_name_format.format(
                                                            self.main_input_name, exp_num)),
                                           exp_num)

            if self.cmdopts['with_rendering']:
                sim_output_dir = self.output_name_format.format(self.main_input_name, exp_num)
                frames_fpath = os.path.join(self.exp_output_root, sim_output_dir, "frames")
                os.makedirs(frames_fpath, exist_ok=True)

    def generate_physics_defs(self, xml_luigi: XMLLuigi):
        """
        Generates definitions for physics engines configuration for the simulation.

        This cannot be done as part of generate_common_defs(), as this class is reused for
        generators for BOTH controller and scenario, and the arena dimensions are None for
        configuring controllers.

        """
        # This will need to change when I get to the point of mixing 2D and 3D physics engines
        pe = physics_engines.Factory(self.cmdopts, self.cmdopts['arena_dim'])

        [xml_luigi.tag_remove(a[0], a[1]) for a in pe.gen_tag_rmlist()[0]]
        [xml_luigi.tag_add(a[0], a[1], a[2]) for a in pe.gen_tag_addlist()[0]]

    def generate_dynamic_cache_defs(self, xml_luigi, arena_dim):
        cache = dynamic_cache.DynamicCache([arena_dim])

        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in cache.gen_attr_changelist()[0]]
        rms = cache.gen_tag_rmlist()
        if rms:  # non-empty
            [xml_luigi.tag_remove(a) for a in rms[0]]

    def generate_static_cache_defs(self, xml_luigi, arena_dim):
        # If they specified how many blocks to use for static cache respawn, use that.
        # Otherwise use the floor of 2.
        if self.cmdopts['static_cache_blocks'] is None:
            cache = static_cache.StaticCache([2], [arena_dim])
        else:
            cache = static_cache.StaticCache([self.cmdopts['static_cache_blocks']],
                                             [arena_dim])

        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in cache.gen_attr_changelist()[0]]
        rms = cache.gen_tag_rmlist()
        if len(rms):
            [xml_luigi.tag_remove(a) for a in rms[0]]

    def generate_block_count_defs(self, xml_luigi: XMLLuigi):
        """
        Generates definitions for # blocks in the simulation from command line overrides.
        """
        if self.cmdopts['n_blocks'] is not None:
            bd = block_distribution.Quantity([self.cmdopts['n_blocks']])
        else:
            n_blocks = int(xml_luigi.attr_get('.//manifest', 'n_cube')) + \
                int(xml_luigi.attr_get('.//manifest', 'n_ramp'))
            bd = block_distribution.Quantity([n_blocks])

        [xml_luigi.attr_change(a[0], a[1], a[2]) for a in bd.gen_attr_changelist()[0]]
        rms = bd.gen_tag_rmlist()

        if len(rms):
            [xml_luigi.tag_remove(a) for a in rms[0]]

        # Write time setup  info to file for later retrieval
        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(bd.gen_attr_changelist()[0], f)

    def __generate_time_defs(self, xml_luigi: XMLLuigi):
        """
        Setup simulation time parameters and write them to the pickle file for retrieval during
        graph generation later.
        """
        setup = __import__("variables.{0}".format(
            self.cmdopts["time_setup"].split(".")[0]), fromlist=["*"])
        tsetup_inst = getattr(setup, "Factory")(self.cmdopts["time_setup"])()

        for a in tsetup_inst.gen_attr_changelist()[0]:
            xml_luigi.attr_change(a[0], a[1], a[2])

        # Write time setup  info to file for later retrieval
        with open(self.exp_def_fpath, 'ab') as f:
            pickle.dump(tsetup_inst.gen_attr_changelist()[0], f)

    def __generate_sa_defs(self, xml_luigi: XMLLuigi):
        """
        Disable selected sensors/actuators, which are computationally expensive in large swarms, but
        not that costly if the # robots is small.
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

    def __generate_threading_defs(self, xml_luigi: XMLLuigi):
        """
        Set the # of cores for a simulation to use, which may be less than the total # available on
        the system.
        """

        xml_luigi.attr_change(".//system",
                              "threads",
                              str(self.cmdopts["n_threads"]))

        # This whole tree can be missing and that's fine
        if xml_luigi.has_tag(".//loop_functions/convergence"):
            xml_luigi.attr_change(".//loop_functions/convergence",
                                  "n_threads",
                                  str(self.cmdopts["n_threads"]))

    def __generate_visualization_defs(self, xml_luigi: XMLLuigi):
        """
        Remove visualization elements from input file, if configured to do so. It may be desired to
        leave them in if generating frames/video.
        """
        if not self.cmdopts["with_rendering"]:
            xml_luigi.tag_remove(".", "./visualization", noprint=True)  # ARGoS visualizations

    def __generate_random_defs(self, xml_luigi, random_seeds, exp_num):
        """
        Generate random seed definitions for a specific simulation in an experiment during the
        input generation process. This cannot be done in init_sim_defs() because it is *not* common
        to all experiments; each experiment has their own random seed.
        """

        # get the random seed for this experiment
        random_seed = random_seeds[exp_num]

        # set the random seed in the config file
        xml_luigi.attr_change(".//experiment", "random_seed", str(random_seed))
        if xml_luigi.has_tag('.//params/rng'):
            xml_luigi.attr_change(".//params/rng", "seed", str(random_seed))
        else:
            xml_luigi.tag_add(".//params", "rng", {"seed": str(random_seed)})

    def __generate_output_defs(self, xml_luigi, exp_num):
        """
        Generate output definitions for a specific simulation in an experiment during the input
        generation process. This cannot be done in init_sim_defs(), because it is *not* common to
        all experiments; each experiment logs/outputs to a unique directory.
        """
        sim_output_dir = self.output_name_format.format(
            self.main_input_name, exp_num)
        frames_fpath = os.path.join(self.exp_output_root, sim_output_dir, "frames")

        xml_luigi.attr_change(
            ".//controllers/*/params/output", "output_dir", sim_output_dir)
        xml_luigi.attr_change(
            ".//controllers/*/params/output", "output_root", self.exp_output_root)
        xml_luigi.attr_change(
            ".//loop_functions/output", "output_dir", sim_output_dir)
        xml_luigi.attr_change(
            ".//loop_functions/output", "output_root", self.exp_output_root)
        xml_luigi.attr_change(
            ".//qt-opengl/frame_grabbing",
            "directory", frames_fpath, noprint=True)  # probably will not be present

    def __create_sim_input_file(self, random_seeds, xml_luigi, exp_num):
        """
        Write the input files for a particular simulation run.
        """

        # create a new name for this experiment's config file
        new_config_name = self.config_name_format.format(
            self.main_input_name, exp_num)

        # Setup simulation random seed
        self.__generate_random_defs(xml_luigi, random_seeds, exp_num)

        # Setup simulation logging/output
        self.__generate_output_defs(xml_luigi, exp_num)

        save_path = os.path.join(self.exp_generation_root, new_config_name)
        xml_luigi.output_filepath = save_path
        open(save_path, 'w').close()  # create an empty file

        # save the config file to the correct place
        xml_luigi.write()

    def __add_sim_to_command_file(self, xml_fname, exp_num):
        """Adds the command to run a particular simulation definition to the command file."""

        # Specify ARGoS invocation in generated command file per cmdline arguments. An option is
        # provided to tweak the exact name of the program used to invoke ARGoS so that different
        # versions compiled for different architectures/machines that exist on the same filesystem
        # can easily be run.
        if 'local' in self.cmdopts['exec_method']:
            argos_cmd = 'argos3'
        else:
            if 'MSI' == self.cmdopts['hpc_env']:
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

        with open(self.commands_fpath, "a") as commands_file:
            commands_file.write(xvfb_cmd +
                                argos_cmd +
                                ' -c "{0}" --log-file /dev/null --logerr-file /dev/null\n'.format(
                                    xml_fname))

    def __generate_random_seeds(self):
        """Generates random seeds for experiments to use."""
        try:
            return random.sample(range(self.random_seed_min, self.random_seed_max + 1), self.cmdopts["n_sims"])
        except ValueError:
            # create a new error message that clarifies the previous one
            raise ValueError("Too few seeds for the required experiment amount; change the random seed parameters") from None
