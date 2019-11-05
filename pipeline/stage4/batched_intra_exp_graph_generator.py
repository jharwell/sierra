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
import typing as tp
import copy
from variables import batch_criteria as bc
from .intra_exp_graph_generator import IntraExpGraphGenerator


class BatchedIntraExpGraphGenerator:
    """
    Generates all intra-experiment graphs for all experiments in the batch. Does not generate
    inter-experiment graphs (see :class:`~pipeline.stage4.InterExpGraphGenerator`).

    Attributes:
        cmdopts: Dictionary of parsed cmdline options.
        main_config: Dictionary of parsed main YAML configuration.
    """

    def __init__(self, main_config: dict, cmdopts: tp.Dict[str, str]):
        # Copy because we are modifying it and don't want to mess up the arguments for graphs that
        # are generated after us
        self.cmdopts = copy.deepcopy(cmdopts)
        self.main_config = main_config

    def __call__(self,
                 controller_config: dict,
                 intra_LN_config: dict,
                 intra_HM_config: dict,
                 batch_criteria: bc.BatchCriteria):
        """
        Generate all intra-experiment graphs for all experiments in the batch by creating and
        calling :class:`~pipeline.stage4.IntraExpGraphGenerator` for each experiment in the batch.
        """
        batch_output_root = self.cmdopts["output_root"]
        batch_graph_root = self.cmdopts["graph_root"]
        batch_generation_root = self.cmdopts['generation_root']

        for item in os.listdir(batch_output_root):

            # Roots need to be modified for each experiment for correct behavior
            self.cmdopts["generation_root"] = os.path.join(batch_generation_root, item)
            self.cmdopts["output_root"] = os.path.join(batch_output_root, item)
            self.cmdopts["graph_root"] = os.path.join(batch_graph_root, item)

            if os.path.isdir(self.cmdopts["output_root"]) and self.main_config['sierra']['collate_csv_leaf'] != item:
                IntraExpGraphGenerator(self.main_config,
                                       controller_config,
                                       intra_LN_config,
                                       intra_HM_config,
                                       self.cmdopts)(batch_criteria)
