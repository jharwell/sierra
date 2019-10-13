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
import yaml
from .inter_batch_comparator import InterBatchComparator


class PipelineStage5:

    """

    Implements stage 5 of the experimental pipeline:

    Compare controllers that have been tested with the same batch criteria across different
    performance measures.

    Attributes:
      targets(list): List of controllers (as strings) that should be compared within sierra_root.
    """

    def __init__(self, cmdopts, targets):
        self.targets = targets
        self.cmdopts = cmdopts
        self.main_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                       'main.yaml')))

        self.cc_graph_root = os.path.join(self.cmdopts['sierra_root'], "cc-graphs")
        self.cc_csv_root = os.path.join(self.cmdopts['sierra_root'], "cc-csvs")
        self.sc_graph_root = os.path.join(self.cmdopts['sierra_root'], "sc-graphs")
        self.sc_csv_root = os.path.join(self.cmdopts['sierra_root'], "sc-csvs")

        os.makedirs(self.cc_graph_root, exist_ok=True)
        os.makedirs(self.cc_csv_root, exist_ok=True)
        os.makedirs(self.sc_graph_root, exist_ok=True)
        os.makedirs(self.sc_csv_root, exist_ok=True)

    def run(self):
        # Verify that all controllers have run the same set of experiments before doing the
        # comparison
        self.targets = self.targets.split(',')
        print("- Stage5: Inter-batch controller comparison of {0}...".format(self.targets))

        for t1 in self.targets:
            for t2 in self.targets:
                for item in os.listdir(os.path.join(self.cmdopts['sierra_root'], t1)):
                    path1 = os.path.join(self.cmdopts['sierra_root'], t1, item,
                                         'exp-outputs',
                                         self.main_config['sierra']['collate_csv_leaf'])
                    path2 = os.path.join(self.cmdopts['sierra_root'], t2, item,
                                         'exp-outputs',
                                         self.main_config['sierra']['collate_csv_leaf'])
                    if os.path.isdir(path1) and not os.path.exists(path2):
                        print("WARN: {0} does not exist".format(path2))
                    if os.path.isdir(path2) and not os.path.exists(path1):
                        print("WARN: {0} does not exist".format(path1))

        InterBatchComparator(controllers=self.targets,
                             cmdopts=self.cmdopts).generate()
        print("- Stage5: Inter-batch controller comparison complete")
