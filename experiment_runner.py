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
import subprocess

class ExperimentRunner:

    """
    Runs the specified  # of experiments in parallel using GNU Parallel on
    the provided set of hosts on MSI (or on a single personal computer for testing).

    Attributes:
      code_path(str): Path(relative to current dir or absolute) to the C++
                      code to be run.
      config_save_path(str): Where XML configuration files generated from the
                             template should be stored(relative to current
                             dir or absolute).
      n_sims(int): Number of simulations to run in parallel.
    """

    def __init__(self, config_save_path, code_path, n_sims):

        # will get the main name and extension of the config file (without the full absolute path)
        self.main_config_name, self.main_config_extension = os.path.splitext(
            os.path.basename(self.config_path))

        # where the generated config and command files should be stored
        if config_save_path is None:
            config_save_path = os.path.join(os.path.dirname(
                self.config_path), "Generated_Config_Files")
        self.config_save_path = os.path.abspath(config_save_path)

        # where the code for the experiment is
        # (this may not be necessary, but I use it)
        self.code_path = os.path.abspath(code_path)

        # how many experiments should be run
        self.n_sims = n_sims

        # where the commands file will be stored
        self.commands_file_path = os.path.abspath(
            os.path.join(self.config_save_path, "commands.txt"))

    def run_experiments(self, personal=False):
        '''Runs the experiments.'''
        try:
            # so that it can be run on non-supercomputers
            if personal:
                subprocess.run('cd "{}" && parallel < "{}"'.format(
                    self.code_path, self.commands_file_path), shell=True, check=True)
            else:
                # running on a supercomputer - specifically MSI
                subprocess.run('cd "{}" && module load parallel && sort -u $PBS_NODEFILE > unique-nodelist.txt && \
                                parallel --jobs 1 --sshloginfile unique-nodelist.txt --workdir $PWD < "{}"'.format(self.code_path, self.commands_file_path),
                               shell=True, check=True)
            print("Experiments ran successfully. (Output can be found in '{}')".format(
                self.output_save_path))
        except subprocess.CalledProcessError as e:
            print("Experiments failed.")
            raise e
