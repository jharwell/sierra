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
from pipeline.intra_exp_linegraphs import IntraExpLinegraphs
from pipeline.intra_exp_histograms import IntraExpHistograms


class IntraExpGraphGenerator:
    """
    Generates common/basic graphs from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
    targets(list): Dictionary of lists of dictiaries specifying what graphs should be
                    generated.
    """

    def __init__(self, exp_output_root, exp_graph_root, targets):

        self.exp_output_root = os.path.abspath(os.path.join(exp_output_root, 'averaged-output'))
        self.exp_graph_root = os.path.abspath(exp_graph_root)
        self.targets = targets
        os.makedirs(self.exp_graph_root, exist_ok=True)

    def __call__(self):
        IntraExpLinegraphs(self.exp_output_root, self.exp_graph_root, self.targets).generate()
        IntraExpHistograms(self.exp_output_root, self.exp_graph_root, self.targets).generate()
