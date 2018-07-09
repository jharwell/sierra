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
from stacked_line_graph import StackedLineGraph


class InterExpGraphGenerator:
    """
    Generates graphs from collated .csv data across a batch of experiments

    Attributes:
      batch_output_root(str): Root directory (relative to current dir or absolute) for experiment
                              outputs.
      batch_graph_root(str): Root directory (relative to current dir or absolute) of where the
                             generated graphs should be saved for the experiment.
    """

    def __init__(self, batch_output_root, batch_graph_root):

        self.batch_output_root = os.path.abspath(os.path.join(batch_output_root, 'collated-csvs'))
        self.batch_graph_root = os.path.abspath(os.path.join(batch_graph_root, 'collated-graphs'))
        os.makedirs(self.batch_graph_root, exist_ok=True)

    def __call__(self):
        StackedLineGraph(input_fpath=os.path.join(self.batch_output_root, "blocks-collected.csv"),
                         output_fpath=os.path.join(
            self.batch_graph_root, "blocks-collected.eps"),
            cols=None,
            title="Average Blocks Collected Across Experiments",
            legend=None,
            xlabel="Timestep",
            ylabel="# Blocks").generate()

        StackedLineGraph(input_fpath=os.path.join(self.batch_output_root, "blocks-avg-transporters.csv"),
                         output_fpath=os.path.join(
            self.batch_graph_root, "blocks-avg-transporters.eps"),
            cols=None,
            title="Average Block Transporters Across Experiments",
            legend=None,
            xlabel="Timestep",
            ylabel="# Transporters").generate()

        StackedLineGraph(input_fpath=os.path.join(self.batch_output_root, "block-acquisition.csv"),
                         output_fpath=os.path.join(
            self.batch_graph_root, "block-acquisition.eps"),
            cols=None,
            title="Average Robots Acquiring Blocks Across Experiments",
            legend=None,
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_fpath=os.path.join(self.batch_output_root, "block-acquisition-exploring.csv"),
                         output_fpath=os.path.join(
            self.batch_graph_root, "block-acquisition-exploring.eps"),
            cols=None,
            title="Average Robots Exploring For Blocks Across Experiments",
            legend=None,
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_fpath=os.path.join(self.batch_output_root, "block-acquisition-vectoring.csv"),
                         output_fpath=os.path.join(
            self.batch_graph_root, "block-acquisition-vectoring.eps"),
            cols=None,
            title="Average Robots Vectoring To Blocks Across Experiments",
            legend=None,
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_fpath=os.path.join(self.batch_output_root, "blocks-avg-transport-times.csv"),
                         output_fpath=os.path.join(
            self.batch_graph_root, "blocks-avg-transport-times.eps"),
            cols=None,
            title="Average Block Transport Times Across Experiments",
            legend=None,
            xlabel="Timestep",
            ylabel="# Timesteps For Transport").generate()

        StackedLineGraph(input_fpath=os.path.join(self.batch_output_root, "blocks-initial-wait-time.csv"),
                         output_fpath=os.path.join(
            self.batch_graph_root, "blocks-initial-wait-time.eps"),
            cols=None,
            title="Average Block Initial Wait Times Across Experiments",
            legend=None,
            xlabel="Timestep",
            ylabel="# Timesteps Waiting").generate()
