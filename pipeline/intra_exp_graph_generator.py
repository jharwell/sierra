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
from pipeline.intra_exp_heatmaps import IntraExpHeatmaps
from pipeline.intra_exp_targets import Linegraphs, Histograms, Heatmaps


class IntraExpGraphGenerator:
    """
    Generates common/basic graphs from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment
                            outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
      generator(str): Fully qualified name of the generator used to create/run the experiments.
      with_hists(bool): If TRUE, then histograms will be generated.
    """

    def __init__(self, exp_output_root, exp_graph_root, generator, with_hists):

        self.exp_output_root = os.path.abspath(os.path.join(exp_output_root, 'averaged-output'))
        self.exp_graph_root = os.path.abspath(exp_graph_root)
        self.generator = generator
        self.with_hists = with_hists
        os.makedirs(self.exp_graph_root, exist_ok=True)

    def __call__(self):
        IntraExpLinegraphs(self.exp_output_root, self.exp_graph_root,
                           Linegraphs.targets('depth2' in self.generator)).generate()
        if self.with_hists:
            IntraExpHistograms(self.exp_output_root, self.exp_graph_root,
                               Histograms.targets()).generate()

        IntraExpHeatmaps(self.exp_output_root, self.exp_graph_root,
                         Heatmaps.targets()).generate()
