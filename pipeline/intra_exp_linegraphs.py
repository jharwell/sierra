"""
Copyright 2018 London John Harwell, All rights reserved.

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
from graphs.stacked_line_graph import StackedLineGraph
import pandas as pd


class IntraExpLinegraphs:
    kTemporalVarCSV = 'loop-temporal-variance.csv'

    """
    Generates linegrahs from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
      targets(list): Dictionary of lists of dictiaries specifying what graphs should be
                     generated.
    """

    def __init__(self, exp_output_root, exp_graph_root, targets):

        self.exp_output_root = exp_output_root
        self.exp_graph_root = exp_graph_root
        self.targets = targets

    def generate(self):
        print("-- Linegraphs from {0}".format(self.exp_output_root))

        for target_set in [self.targets[x] for x in self.targets.keys()]:
            for target in target_set:
                StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root,
                                                               target['src_stem']),
                                 output_fpath=os.path.join(
                                     self.exp_graph_root,
                                     target['dest_stem'] + '.png'),
                                 cols=target['cols'],
                                 title=target['title'],
                                 legend=target['legend'],
                                 xlabel=target['xlabel'],
                                 ylabel=target['ylabel'],
                                 linestyles=target.get('styles', None)).generate()
