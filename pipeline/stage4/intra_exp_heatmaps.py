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
#


import os
import logging
from graphs.heatmap import Heatmap


class IntraExpHeatmaps:
    """
    Generates heatmaps from averaged output data within a single experiment.

    Attributes:
        exp_output_root: Absolute path to root directory for experiment simulation outputs.
        exp_output_root: Absolute path to root directory for experiment graph outputs.
        targets: Dictionary of lists of dictionaries specifying what graphs should be
                 generated.
    """

    def __init__(self, exp_output_root: str, exp_graph_root: str, targets: list):

        self.exp_output_root = exp_output_root
        self.exp_graph_root = exp_graph_root
        self.targets = targets

    def generate(self):
        logging.info("Heatmaps from {0}".format(self.exp_output_root))

        # For each category of heatmaps we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                Heatmap(input_fpath=os.path.join(self.exp_output_root,
                                                 graph['src_stem'] + '.csv'),
                        output_fpath=os.path.join(self.exp_graph_root,
                                                  graph['src_stem'] + '-hm.png'),
                        title=graph['title'],
                        xlabel='Y',
                        ylabel='X',
                        xtick_labels=None,
                        ytick_labels=None).generate()
