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
from graphs.stacked_line_graph import StackedLineGraph


class IntraExpGraphGenerator:
    """
    Generates common/basic graphs from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
    """

    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = os.path.abspath(os.path.join(exp_output_root, 'averaged-output'))
        self.exp_graph_root = os.path.abspath(exp_graph_root)
        os.makedirs(self.exp_graph_root, exist_ok=True)

    def __call__(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "collision-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance.eps"),
            cols=['n_avoiding_collision', 'n_cum_avoiding_collision'],
            title="Swarm Collision Avoidance",
            legend=['# Robots Avoiding Collision (within interval)',
                    '# Cumulative Robots Avoiding Collision'],
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "distance-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "distance-stats.eps"),
            cols=['cum_distance'],
            title="Swarm Cumulative Distance Traveled",
            legend=['Average Distance (within interval)'],
            xlabel="Timestep",
            ylabel="Distance (m)").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "robots-acquiring-blocks.eps"),
            cols=['avg_acquiring_goal', 'avg_vectoring_to_goal',
                  'avg_exploring_for_goal'],
            title="Swarm Block Acquisition",
            legend=['# Robots Acquiring Blocks', '# Robots Vectoring To Blocks',
                    '# Robots Exploring For Blocks'],
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-acquisition-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "robots-acquiring-caches.eps"),
            cols=['avg_acquiring_goal', 'avg_vectoring_to_goal',
                  'avg_exploring_for_goal'],
            title="Swarm Cache Acquisition",
            legend=['# Robots Acquiring Caches', '# Robots Vectoring To Caches',
                    '# Robots Exploring For Caches'],
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "cum-robots-acquiring-blocks.eps"),
            cols=['avg_cum_acquiring_goal', 'avg_cum_vectoring_to_goal',
                  'avg_cum_exploring_for_goal'],
            title="Swarm Block Acquisition",
            legend=['# Robots Acquiring Blocks', '# Robots Vectoring To Blocks',
                    '# Robots Exploring For Blocks'],
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-acquisition-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "cum-robots-acquiring-caches.eps"),
            cols=['avg_cum_acquiring_goal', 'avg_cum_vectoring_to_goal',
                  'avg_cum_exploring_for_goal'],
            title="Swarm Cache Acquisition",
            legend=['# Robots Acquiring Caches', '# Robots Vectoring To Caches',
                    '# Robots Exploring For Caches'],
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "blocks-collected.eps"),
            cols=['n_collected', 'n_cube_collected', 'n_ramp_collected'],
            title="Swarm Blocks Collected",
            legend=['# Blocks Collected', '# Cube blocks collected', '# Ramp blocks collected'],
            xlabel="Timestep",
            ylabel="# Blocks").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "blocks-avg-transporters.eps"),
            cols=['avg_transporters'],
            title="Swarm Block Average Transporters",
            legend=['Average # Transporters Per Block'],
            xlabel="Timestep",
            ylabel="# Transporters").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "block-transport-time.eps"),
            cols=['avg_transport_time', 'avg_initial_wait_time'],
            title="Swarm Block Transport Time",
            legend=['Average Block Transport Time', "Average Initial Wait Time"],
            xlabel="Timestep",
            ylabel="Time").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "block-pickup-drop-rates.eps"),
            cols=['avg_pickup_events', 'avg_drop_events'],
            title="Swarm Average Block Pickup/Drop Rates",
            legend=['Average Pickup Events', "Average Drop Events"],
            xlabel="Timestep",
            ylabel="Time").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-lifecycle-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "cache-lifecycle.eps"),
            cols=['n_depleted', 'n_created'],
            title="Swarm Cache Lifecycles",
            legend=['# Caches Created (within interval)',
                    "# Caches Depleted (within interval)"],
            xlabel="Timestep",
            ylabel="# Caches").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-utilization-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "cache-utilization-avg-blocks.eps"),
            cols=['avg_blocks'],
            title="Swarm Cache Size",
            legend=['Cache Size (blocks)'],
            xlabel="Timestep",
            ylabel="# Blocks").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-utilization-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "cache-utilization-pickups-drops.eps"),
            cols=['avg_pickups', 'avg_drops'],
            title="Swarm Cache Pickups/Drops",
            legend=['Average # Pickups', 'Average # Drops'],
            xlabel="Timestep",
            ylabel="# Pickups/Drops").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-utilization-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "cache-utilization-avg-penalty.eps"),
            cols=['avg_penalty'],
            title="Swarm Cache Penalties",
            legend=['Average Penalty'],
            xlabel="Timestep",
            ylabel="# Penalty Timesteps").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "perception-world-model"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "perception-world-model-inaccuracies.eps"),
            cols=['ST_EMPTY_inaccuracies', 'ST_HAS_BLOCK_inaccuracies',
                  'ST_HAS_CACHE_inaccuracies'],
            title="Swarm Perception Model Inaccuracies",
            legend=['ST_EMPTY', 'ST_HAS_BLOCK', 'ST_HAS_CACHE'],
            xlabel="Timestep",
            ylabel="# Inaccuracies").generate()
