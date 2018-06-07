'''
By: London Lowmanstone
'''

import os
import random
from xml_helper import XMLHelper

class ExperimentRunner:
    def __init__(self, main_xml_path, code_path, save_xml_path, graph_path, amount):
        self.main_xml_path = main_xml_path
        self.code_path = code_path
        self.save_xml_path = save_xml_path
        self.graph_path = graph_path
        self.amount = amount


    def generate_xml_files(self):
        xml_helper = XMLHelper(self.main_xml_path)
        main_name, extension = os.path.splitext(os.path.basename(self.main_xml_path))
        os.makedirs(self.save_xml_path, exist_ok=True)
        random_seeds = self._generate_random_seeds()
        for experiment_number in range(self.amount):
            random_seed = random_seeds[experiment_number]
            xml_helper.set_path_attribute("experiment.random_seed", random_seed)
            new_name = main_name + "_" + str(experiment_number) + extension
            save_path = os.path.join(self.save_xml_path, new_name)
            print(save_path)
            open(save_path, 'w').close() # create an empty file
            xml_helper.write(save_path)


    def _generate_random_seeds(self):
        # choose random seeds from 1 to 10 times the amount of experiments
        return random.sample(range(1, 10*self.amount), self.amount)


if __name__ == "__main__":
    runner = ExperimentRunner("Sample XML Files/single-source.argos", None, "Generated XML Files", None, 5)
    runner.generate_xml_files()
