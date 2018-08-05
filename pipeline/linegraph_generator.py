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


class LinegraphGenerator:
    """
    Generates linegrahs from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
    """

    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = exp_output_root
        self.exp_graph_root = exp_graph_root

    def __call__(self):
        self.depth0_generate_linegraphs()
        self.depth1_generate_linegraphs()

#
# Depth0 graph generation
#

    def depth0_generate_linegraphs(self):
        self.generate_collision_linegraphs()
        self.generate_distance_linegraphs()
        self.generate_block_acq_linegraphs()
        self.generate_block_trans_linegraphs()
        self.generate_block_manip_linegraphs()

    def generate_collision_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "collision-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-counts.eps"),
            cols=['int_avg_in_avoidance', 'cum_avg_in_avoidance',
                  'int_avg_entered_avoidance', 'cum_avg_entered_avoidance',
                  'int_avg_exited_avoidance', 'cum_avg_exited_avoidance'],
            title="Swarm Collision Avoidance",
            legend=['Average # Robots Avoiding Collision (interval)',
                    'Average # Robots Avoiding Collision (cumulative)',
                    'Average # Robots Entered Avoidance (interval)',
                    'Average # Robots Entered Avoidance (cumulative)',
                    'Average # Robots Exited Avoidance (interval)',
                    'Average # Robots Exited Avoidance (cumulative)'],
            xlabel="Timestep",
            ylabel="# Robots").generate()
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "collision-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-duration.eps"),
            cols=['int_avg_avoidance_duration', 'cum_avg_avoidance_duration'],
            title="Swarm Collision Avoidance",
            legend=['Average Avoidance Duration (interval)',
                    'Average Avoidance Duration (cumulative)'],
            xlabel="Timestep",
            ylabel="Duration").generate()

    def generate_distance_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "distance-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "distance-stats.eps"),
            cols=['int_avg_distance', 'cum_avg_distance'],
            title="Swarm Cumulative Distance Traveled",
            legend=['Average Distance (interval)', 'Average Distance (cumulative)'],
            xlabel="Timestep",
            ylabel="Distance (m)").generate()

    def generate_block_acq_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "robots-acquiring-blocks.eps"),
            cols=['int_avg_acquiring_goal', 'cum_avg_acquiring_goal',
                  'int_avg_vectoring_to_goal', 'cum_avg_vectoring_to_goal',
                  'int_avg_exploring_for_goal', 'cum_avg_exploring_for_goal'],
            title="Swarm Block Acquisition",
            legend=['Average # Robots Acquiring Blocks (interval)',
                    'Average # Robots Acquiring Blocks (cumulative)',
                    'Average # Robots Vectoring To Blocks (interval)',
                    'Average # Robots Vectoring To Blocks (cumulative)',
                    'Average # Robots Exploring For Blocks (interval)',
                    'Average # Robots Exploring For Blocks (cumulative)'],
            xlabel="Timestep",
            ylabel="# Robots").generate()

    def generate_block_trans_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "blocks-int-collected.eps"),
            cols=['int_collected', 'int_cube_collected', 'int_ramp_collected'],
            title="Swarm Interval Blocks Collected",
            legend=['All Blocks', '# Cube Blocks', '# Ramp Blocks'],
            xlabel="Timestep",
            ylabel="# Blocks").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "blocks-cum-collected.eps"),
            cols=['cum_avg_collected', 'cum_avg_cube_collected', 'cum_avg_ramp_collected'],
            title="Swarm Cumulative Average Blocks Collected",
            legend=['# Blocks Collected', '# Cube Blocks', '# Ramp Blocks Collected'],
            xlabel="Timestep",
            ylabel="# Blocks").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "blocks-avg-transporters.eps"),
            cols=['int_avg_transporters', 'cum_avg_transporters'],
            title="Swarm Block Average Transporters",
            legend=['Average # Transporters Per Block (interval)',
                    'Average # Transporters Per Block (cumulative)'],
            xlabel="Timestep",
            ylabel="# Transporters").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "block-transport-time.eps"),
            cols=['int_avg_transport_time', 'cum_avg_transport_time',
                  'int_avg_initial_wait_time', 'cum_avg_initial_wait_time'],
            title="Swarm Block Transport Time",
            legend=['Average Block Transport Time (interval)',
                    'Cumulative Average Transport Time (cumulative)',
                    "Average Initial Wait Time (interval)",
                    'Average Initial Wait Time (cumulative)'],
            xlabel="Timestep",
            ylabel="Time").generate()

    def generate_block_manip_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-manipulation-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "block-manipulation-op.eps"),
            cols=['int_avg_free_pickup_events', 'int_avg_free_drop_events',
                  'int_avg_cache_pickup_events', 'int_avg_cache_drop_events'],
            title="Block Manipulation Pickups/Drops",
            legend=['Average # Free Pickups (interval)', 'Average # Free Drops (interval)',
                    'Average # Cache Pickups (interval)', 'Average # Cache Drops (interval)'],
            xlabel="Timestep",
            ylabel="# Pickups/Drops").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-manipulation-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "block-manipulation-penalty.eps"),
            cols=['int_avg_free_pickup_penalty', 'int_avg_free_drop_penalty',
                  'int_avg_cache_pickup_penalty', 'int_avg_cache_drop_penalty'],
            title="Block Manipulation Penalties",
            legend=['Average Free Pickup Penalty (interval)', 'Average Free Drop Penalty (interval)',
                    'Average Cache Picup Penalty (interval)', 'Average Cache Drop Penalty (interval)'],
            xlabel="Timestep",
            ylabel="Penalty").generate()

    def generate_world_model_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "perception-world-model"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "perception-world-model-inaccuracies.eps"),
            cols=['ST_EMPTY_inaccuracies', 'ST_HAS_BLOCK_inaccuracies',
                  'ST_HAS_CACHE_inaccuracies'],
            title="Swarm Perception Model Inaccuracies",
            legend=['ST_EMPTY', 'ST_HAS_BLOCK', 'ST_HAS_CACHE'],
            xlabel="Timestep",
            ylabel="# Inaccuracies").generate()

#
# Depth1 graph generation
#
    def depth1_generate_linegraphs(self):
        self.depth0_generate_linegraphs()
        self.generate_cache_acq_linegraphs()
        self.generate_cache_util_linegraphs()
        self.generate_cache_lifecycle_linegraphs()

    def generate_cache_acq_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-acquisition-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "robots-acquiring-caches.eps"),
            cols=['int_avg_acquiring_goal', 'int_avg_vectoring_to_goal',
                  'int_avg_exploring_for_goal'],
            title="Swarm Cache Acquisition",
            legend=['# Robots Acquiring Caches (interval)',
                    '# Robots Vectoring To Caches (interval)',
                    '# Robots Exploring For Caches (interval)'],
            xlabel="Timestep",
            ylabel="# Robots").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-acquisition-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "cum-robots-acquiring-caches.eps"),
            cols=['cum_avg_acquiring_goal', 'cum_avg_vectoring_to_goal',
                  'cum_avg_exploring_for_goal'],
            title="Swarm Cache Acquisition",
            legend=['# Robots Acquiring Caches (cumulative)',
                    '# Robots Vectoring To Caches (cumulative)',
                    '# Robots Exploring For Caches (cumulative)'],
            xlabel="Timestep",
            ylabel="# Robots").generate()

    def generate_cache_lifecycle_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "cache-lifecycle-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "cache-lifecycle.eps"),
            cols=['n_depleted', 'n_created'],
            title="Swarm Cache Lifecycles",
            legend=['# Caches Created (within interval)',
                    "# Caches Depleted (within interval)"],
            xlabel="Timestep",
            ylabel="# Caches").generate()

    def generate_cache_util_linegraphs(self):
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
            self.exp_graph_root, "cache-utilization-avg-penalty.eps"),
            cols=['avg_penalty'],
            title="Swarm Cache Penalties",
            legend=['Average Penalty'],
            xlabel="Timestep",
            ylabel="# Penalty Timesteps").generate()
