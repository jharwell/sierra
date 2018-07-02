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
from xml_helper import XMLHelper, InvalidElementError


class XMLFileGenerator:

    """
    Generates a set of XML files from an input template.

    Attributes:
      config_path(str): Path(relative to current dir or absolute) to the template XML configuration file.
      code_path(str): Path(relative to current dir or absolute) to the C++ code to be run.
      config_save_path(str): Where XML configuration files generated from the template should be stored(relative to
                             current dir or absolute).
      output_save_path(str): Root directory for simulation outputs(sort of a scratch directory). Can be relative or absolute.
      n_sims(int): Number of simulations to run in parallel.
      random_seed_min(int): Minimum random seed for the experiment. Defaults to 1.
      random_seed_max(int): Maximum random seed for the experiment. Defaults to 10 * n_s.
      remove_visualization(bool): Whether or not it should remove the loop-function visualization (main argos
                                  visualization is always removed if present).
    """

    def __init__(self, config_path, code_path, config_save_path, output_save_path, n_sims, random_seed_min=None, random_seed_max=None,
                 remove_visualization=False):

        assert os.path.isfile(
            config_path), "The path '{}' (which should point to the main config file) did not point to a file".format(config_path)
        self.config_path = os.path.abspath(config_path)

        # will get the main name and extension of the config file (without the full absolute path)
        self.main_config_name, self.main_config_extension = os.path.splitext(
            os.path.basename(self.config_path))

        # where the code for the experiment is (this may not be necessary, but I use it)
        self.code_path = os.path.abspath(code_path)

        # where the generated config and command files should be stored
        if config_save_path is None:
            config_save_path = os.path.join(os.path.dirname(
                self.config_path), "Generated_Config_Files")
        self.config_save_path = os.path.abspath(config_save_path)

        assert self.config_save_path.find(" ") == -1, ("ARGoS (apparently) does not support running configuration files with spaces in the path. Please make sure the " +
                                                       "configuration file save path '{}' does not have any spaces in it").format(self.config_save_path)

        # where the output data should be stored
        if output_save_path is None:
            output_save_path = os.path.join(os.path.dirname(
                self.config_save_path), "Generated_Output")
        self.output_save_path = os.path.abspath(output_save_path)

        # how many experiments should be run
        self.n_sims = n_sims

        if random_seed_min is None:
            random_seed_min = 1
        if random_seed_max is None:
            random_seed_max = 10 * self.n_sims
        self.random_seed_min = random_seed_min
        self.random_seed_max = random_seed_max

        self.remove_visusalization = remove_visualization

        # where the commands file will be stored
        self.commands_file_path = os.path.abspath(
            os.path.join(self.config_save_path, "commands.txt"))

        # to be formatted like: self.config_name_format.format(name, experiment_number)
        format_base = "{}_{}"
        self.config_name_format = format_base + self.main_config_extension
        self.output_name_format = format_base + "_output"

    def generate_xml_files(self):
        '''Generates and saves all the XML config files for all the experiments'''
        # create an object that will edit the XML file
        xml_helper = XMLHelper(self.config_path)

        # make the save path
        os.makedirs(self.config_save_path, exist_ok=True)

        # take out the main visualization element
        try:
            xml_helper.remove_element("argos-configuration.visualization")
        except InvalidElementError:
            # it's okay if this one doesn't exist
            pass

        if self.remove_both_visusalizations:
            # remove the secondary visualization element
            # sometimes doing this can cause Argos to not work, so it is allowed as an option
            try:
                xml_helper.remove_element("loop_functions.visualization")
            except InvalidElementError:
                print(
                    "Note: it was specified to remove both visualizations, but the second visualization was not found")

        # generate different seeds for each experiment
        random_seeds = self._generate_random_seeds()

        with open(self.commands_file_path, "w") as commands_file:
            for experiment_number in range(self.n_sims):
                # create a new name for this experiment's config file
                new_config_name = self.config_name_format.format(
                    self.main_config_name, experiment_number)
                # get the random seed for this experiment
                random_seed = random_seeds[experiment_number]
                # set the random seed in the config file
                # restriction: the config file must have these fields in order for this function to work correctly.
                xml_helper.set_attribute("experiment.random_seed", random_seed)

                # set the output directory
                # restriction: these attributes must exist in the config file
                # this should throw an error if the attributes don't exist
                output_dir = self.output_name_format.format(
                    self.main_config_name, experiment_number)
                xml_helper.set_attribute(
                    "controllers.output.sim.output_dir", output_dir)
                xml_helper.set_attribute(
                    "controllers.output.sim.output_root", self.output_save_path)
                xml_helper.set_attribute(
                    "loop_functions.output.sim.output_dir", output_dir)
                xml_helper.set_attribute(
                    "loop_functions.output.sim.output_root", self.output_save_path)
                save_path = os.path.join(
                    self.config_save_path, new_config_name)
                open(save_path, 'w').close()  # create an empty file
                # save the config file to the correct place
                xml_helper.write(save_path)
                # need the double quotes around the path so that it works in both Linux and Windows
                commands_file.write('argos3 -c "{}"\n'.format(save_path))
        print("The XML files have been generated.")

    def _generate_random_seeds(self):
        """Generates random seeds for experiments to use."""
        try:
            return random.sample(range(self.random_seed_min, self.random_seed_max + 1), self.n_sims)
        except ValueError:
            # create a new error message that clarifies the previous one
            raise ValueError("Too few seeds for the required experiment amount; change the random seed parameters") from None
