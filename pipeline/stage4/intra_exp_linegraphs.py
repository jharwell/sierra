# Copyright 2018 London John Harwell, All rights reserved.
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
from graphs.stacked_line_graph import StackedLineGraph


class IntraExpLinegraphs:
    """
    Generates linegrahs from averaged output data within a single experiment.

    Attributes:
        exp_output_root: Absolute path to experiment simulation output directory.
        exp_graph_root: Absolutae path to experiment graph output directory.
        targets: Dictionary of lists of dictiaries specifying what graphs should be
                 generated.
    """

    def __init__(self, exp_output_root: str, exp_graph_root: str, targets: list):

        self.exp_output_root = exp_output_root
        self.exp_graph_root = exp_graph_root
        self.targets = targets

    def generate(self):
        print("-- Linegraphs from {0}".format(self.exp_output_root))

        # For each category of linegraphs we are generating
        for category in self.targets:
            # For each graph in each category
            for graph in category['graphs']:
                output_fpath = os.path.join(self.exp_graph_root,
                                            graph['dest_stem'] + '.png'),
                try:
                    StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root,
                                                                   graph['src_stem']),
                                     output_fpath=output_fpath,
                                     cols=graph['cols'],
                                     title=graph['title'],
                                     legend=graph['legend'],
                                     xlabel=graph['xlabel'],
                                     ylabel=graph['ylabel'],
                                     linestyles=graph.get('styles', None),
                                     dashes=graph.get('dashes', None)).generate()
                except KeyError:
                    raise KeyError('Check that the generated {0}.csv file contains the columns {1}'.format(
                        graph['src_stem'],
                        graph['cols']))
