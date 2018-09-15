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


class HistogramGenerator:
    """
    Generates histograms from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
    """

    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = exp_output_root
        self.exp_graph_root = exp_graph_root

    def __call__(self):
        self.depth0_generate_histograms()


#
# Depth0 graph generation
#

    def depth0_generate_histograms(self):
        self.generate_collision_histograms()
        self.generate_distance_histograms()
        self.generate_block_acq_histograms()
        self.generate_block_trans_histograms()

    def generate_collision_histograms(self):
        Histogram(input_fpath=os.path.join(self.exp_output_root, "collision-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-in-hist.png"),
            col=['int_avg_in_avoidance'],
            title="Swarm Average Collision Avoidance (interval)",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "collision-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-entered-hist.png"),
            col=['int_avg_entered_avoidance'],
            title="Swarm Average Entering Collision Avoidance (interval)",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "collision-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-exited-hist.png"),
            col=['int_avg_exited_avoidance'],
            title="Swarm Average Exited Collision Avoidance (interval)",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "collision-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-duration-hist.png"),
            col=['int_avg_avoidance_duration'],
            title="Swarm Average Collision Avoidance Duration (interval)",
            xlabel="Duration (timestpng)",
            ylabel="Count").generate()

    def generate_distance_histograms(self):
        Histogram(input_fpath=os.path.join(self.exp_output_root, "distance-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "distance-stats-hist.png"),
            col=['int_avg_distance'],
            title="Swarm Cumulative Distance Traveled (interval)",
            xlabel="Distance (m)",
            ylabel="Count").generate()

    def generate_block_acq_histograms(self):
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "robots-acquiring-blocks-hist.png"),
            col=['int_avg_acquiring_goal'],
            title="Swarm Block Acquisition (interval)",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "robots-vectoring-to-blocks-hist.png"),
            col=['int_avg_vectoring_to_goal'],
            title="Swarm Block Acquisition Vectoring (interval)",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "robots-exploring-for-blocks-hist.png"),
            col=['int_avg_exploring_for_goal'],
            title="Swarm Block Acquisition Exploring (interval)",
            xlabel="# Robots",
            ylabel="Count").generate()

    def generate_block_trans_histograms(self):
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-transport-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "blocks-collected-all-hist.png"),
            col=['int_collected'],
            title="Swarm Blocks Collected (interval)",
            xlabel="# Blocks",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-transport-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "blocks-collected-cube-hist.png"),
            col=['int_cube_collected'],
            title="Swarm Cube Blocks Collected (interval)",
            xlabel="# Blocks",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-transport-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "blocks-collected-ramp-hist.png"),
            col=['int_ramp_collected'],
            title="Swarm Ramp Blocks Collected (interval)",
            xlabel="# Blocks",
            ylabel="Count").generate()

        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-transport-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "blocks-transporters-hist.png"),
            col=['int_avg_transporters'],
            title="Swarm Average Transporters (interval)",
            xlabel="# Transporters",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-transport-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "blocks-transport-time-hist.png"),
            col=['int_avg_transport_time'],
            title="Swarm Average Block Transport Time (interval)",
            xlabel="# Timesteps",
            ylabel="Count").generate()
