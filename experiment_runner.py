'''
By: London Lowmanstone
'''

import os
import random
import argparse
import subprocess
from xml_helper import XMLHelper, InvalidElementError

class ExperimentRunner:
    def __init__(self, config_path, code_path, config_save_path, graph_save_path, amount):
        # where the main config file is
        assert os.path.isfile(config_path), "The path '{}' (which should point to the main config file) did not point to a file".format(config_path)
        self.config_path = os.path.abspath(config_path)

        # where the code for the experiment is
        self.code_path = os.path.abspath(code_path)

        # where the generated config and command files should be stored
        if config_save_path is None:
            config_save_path = os.path.join(os.path.dirname(self.config_path), "Generated_Config_Files")
        self.config_save_path = os.path.abspath(config_save_path)

        # where the graphs should be stored
        if graph_save_path is None:
            graph_save_path = os.path.join(os.path.dirname(self.config_path), "Generated_Graph_Files")
        self.graph_save_path = os.path.abspath(graph_save_path)

        # how many experiments should be run
        self.amount = amount

        self.commands_file_path = os.path.abspath(os.path.join(self.config_save_path, "commands.txt"))

    def run_experiments(testing=False):
        self.generate_xml_files()
        if testing==False:
            subprocess.run('cd "{}" && module load parallel && sort -u $PBS_NODEFILE > unique-nodelist.txt && \
                            parallel --jobs 1 --sshloginfile unique-nodelist.txt --workdir $PWD < "{}"'.format(self.code_path, self.commands_file_path), shell=True)
        else:
            subprocess.run('cd "{}" && parallel --jobs 1 < "{}"'.format(self.code_path, self.commands_file_path), shell=True)



    def generate_xml_files(self):
        xml_helper = XMLHelper(self.config_path)
        # will get the main name and extension of the config file (without the full absolute path)
        main_name, extension = os.path.splitext(os.path.basename(self.config_path))
        os.makedirs(self.config_save_path, exist_ok=True)
        try:
            # restriction: assumes that any visualization will be at "argos-configuration.visualization"
            # note that the "loop_functions.visualization" should not and will not be deleted
            # TODO check with John that this is the correct way to remove the visualization
            xml_helper.remove_element("argos-configuration.visualization")
        except InvalidElementError:
            # no visualization was defined in the first place
            pass
        random_seeds = self._generate_random_seeds()

        with open(self.commands_file_path, "w") as commands_file:
            for experiment_number in range(self.amount):
                new_main_name = main_name + "_" + str(experiment_number)
                new_name = new_main_name + extension
                random_seed = random_seeds[experiment_number]
                # restriction: the config file must have these fields in order for this function to work correctly.
                xml_helper.set_attribute("experiment.random_seed", random_seed)
                # TODO check with John that it's alright to assume that the config file will always be in this format
                xml_helper.set_attribute("output.sim.output_dir", new_main_name + "_output")
                # TODO ask John what output.robot.output_root is
                xml_helper.set_attribute("output.robot.output_dir", new_main_name + "_output")
                xml_helper.set_attribute("output.metrics.output_dir", new_main_name + "_metrics")
                save_path = os.path.join(self.config_save_path, new_name)
                open(save_path, 'w').close() # create an empty file
                xml_helper.write(save_path)
                # need the double quotes around the path so that it works in both Linux and Windows
                commands_file.write('argos3 -c "{}"\n'.format(save_path))


    def _generate_random_seeds(self):
        # choose random seeds from 1 to 10 times the amount of experiments
        return random.sample(range(1, 10*self.amount), self.amount)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", help="the configuration file for the experiment to be run")
    parser.add_argument("code_path", help="where the code is to run the experiment")
    parser.add_argument("amount", help="how many experiments to run", type=int)
    parser.add_argument("--config_save_path", help="where to save the generated config files")
    parser.add_argument("--graph_save_path", help="where to save the generated graph files")
    args = parser.parse_args()
    # check python version
    import sys
    if sys.version_info < (3, 0):
        raise RuntimeError("Python 3.x should be usued to run this code.")
    runner = ExperimentRunner(args.config_path, args.code_path, args.config_save_path, args.graph_save_path, args.amount)
    runner.generate_xml_files()
    print("The XML files have been generated.")
