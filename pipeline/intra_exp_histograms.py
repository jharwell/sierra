"""
Copyright 2018 John Harwell, All rights reserved.

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
from graphs.histogram import Histogram


class IntraExpHistograms:
    """
    Generates histograms from averaged output data within a single experiment.

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
        self.depth0_generate_histograms()

    def depth0_generate_histograms(self):
        for target_set in [self.targets[x] for x in ['fsm-collision',
                                                     'fsm-movement',
                                                     'block_trans',
                                                     'block_acq',
                                                     'block_manip',
                                                     'world_model']]:
            for target in target_set:
                for col in target['cols']:
                    Histogram(input_fpath=os.path.join(self.exp_output_root,
                                                       target['src_stem'] + '.csv'),
                              output_fpath=os.path.join(
                                  self.exp_graph_root,
                        target['src_stem'] + '-' + col + '-hist.eps'),
                        col=col,
                        title=target['title'],
                        xlabel=col,
                        ylabel='Count').generate()
