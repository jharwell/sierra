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
from graphs.histogram import Histogram


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
        self.depth0_generate_linegraphs()
        self.depth0_generate_histograms()

    def depth0_generate_histograms(self):
        Histogram(input_fpath=os.path.join(self.exp_output_root, "collision-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-in-hist.eps"),
            col=['avg_in_avoidance'],
            title="Swarm Average Collision Avoidance",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "collision-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-entered-hist.eps"),
            col=['avg_entered_avoidance'],
            title="Swarm Average Entering Collision Avoidance",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "collision-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-exited-hist.eps"),
            col=['avg_exited_avoidance'],
            title="Swarm Average Exited Collision Avoidance",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "collision-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-duration-hist.eps"),
            col=['avg_avoidance_duration'],
            title="Swarm Average Collision Avoidance Duration",
            xlabel="Duration (timesteps)",
            ylabel="Count").generate()

        Histogram(input_fpath=os.path.join(self.exp_output_root, "distance-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "distance-stats-hist.eps"),
            col=['avg_distance'],
            title="Swarm Cumulative Distance Traveled",
            xlabel="Distance (m)",
            ylabel="Count").generate()

        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "robots-acquiring-blocks-hist.eps"),
            col=['avg_acquiring_goal'],
            title="Swarm Block Acquisition",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "robots-vectoring-to-blocks-hist.eps"),
            col=['avg_vectoring_to_goal'],
            title="Swarm Block Acquisition Vectoring",
            xlabel="# Robots",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-acquisition-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "robots-exploring-for-blocks-hist.eps"),
            col=['avg_exploring_for_goal'],
            title="Swarm Block Acquisition Exploring",
            xlabel="# Robots",
            ylabel="Count").generate()

        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-transport-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "blocks-collected-hist.eps"),
            col=['n_collected'],
            title="Swarm Blocks Collected",
            xlabel="# Blocks",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-transport-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "blocks-transporters-hist.eps"),
            col=['avg_transporters'],
            title="Swarm Blocks Collected Average Transporters",
            xlabel="# Transporters",
            ylabel="Count").generate()
        Histogram(input_fpath=os.path.join(self.exp_output_root, "block-transport-stats.csv"),
                  output_fpath=os.path.join(
            self.exp_graph_root, "blocks-transport-time-hist.eps"),
            col=['avg_transport_time'],
            title="Swarm Average Transport Time",
            xlabel="# Timesteps",
            ylabel="Count").generate()

    def depth0_generate_linegraphs(self):
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "collision-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-counts.eps"),
            cols=['avg_in_avoidance', 'avg_cum_in_avoidance', 'avg_entered_avoidance',
                  'avg_cum_entered_avoidance', 'avg_exited_avoidance', 'avg_cum_exited_avoidance'],
            title="Swarm Collision Avoidance",
            legend=['Average # Robots Avoiding Collision (within interval)',
                    'Cumulative Average Robots Avoiding Collision',
                    'Average # Robots Entered Avoidance (within interval)',
                    'Cumulative Average Robots Entered Avoidance',
                    'Average # Robots Exited Avoidance (within interval)',
                    'Cumulative Average Robots Exited Avoidance'],
            xlabel="Timestep",
            ylabel="# Robots").generate()
        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "collision-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "collision-avoidance-duration.eps"),
            cols=['avg_avoidance_duration', 'avg_cum_avoidance_duration'],
            title="Swarm Collision Avoidance",
            legend=['Average Avoidance Duration (within interval)',
                    'Cumulative Average Avoidance Duration'],
            xlabel="Timestep",
            ylabel="Duration").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "distance-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "distance-stats.eps"),
            cols=['avg_distance', 'avg_cum_distance'],
            title="Swarm Cumulative Distance Traveled",
            legend=['Average Distance (within interval)', 'Cumulative Average Distance Traveled'],
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

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "blocks-collected.eps"),
            cols=['n_collected', 'cum_collected'],
            title="Swarm Blocks Collected",
            legend=['# Blocks Collected', 'Cumulative # Blocks Collected'],
            xlabel="Timestep",
            ylabel="# Blocks").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "blocks-avg-transporters.eps"),
            cols=['avg_transporters', 'avg_cum_transporters'],
            title="Swarm Block Average Transporters",
            legend=['Average # Transporters Per Block',
                    'Cumulative Average # Transporters Per Block'],
            xlabel="Timestep",
            ylabel="# Transporters").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-transport-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "block-transport-time.eps"),
            cols=['avg_transport_time', 'avg_initial_wait_time',
                  'avg_cum_transport_time', 'avg_cum_initial_wait_time'],
            title="Swarm Block Transport Time",
            legend=['Average Block Transport Time', "Average Initial Wait Time",
                    'Cumulative Average Transport Time', 'Cumulative Average Initial Wait Time'],
            xlabel="Timestep",
            ylabel="Time").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-manipulation-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "block-manipulation-op.eps"),
            cols=['avg_free_pickup_events', 'avg_free_drop_events',
                  'avg_cache_pickup_events', 'avg_cache_drop_events'],
            title="Block Manipulation Pickups/Drops",
            legend=['Average # Free Pickups', 'Average # Free Drops',
                    'Average # Cache Pickups', 'Average # Cache Drops'],
            xlabel="Timestep",
            ylabel="# Pickups/Drops").generate()

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "block-manipulation-stats"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "block-manipulation-penalty.eps"),
            cols=['avg_free_pickup_penalty', 'avg_free_drop_penalty',
                  'avg_cache_pickup_penalty', 'avg_cache_drop_penalty'],
            title="Block Manipulation Penalties",
            legend=['Average Free Pickup Penalty', 'Average Free Drop Penalty',
                    'Average Cache Picup Penalty', 'Average Cache Drop Penalty'],
            xlabel="Timestep",
            ylabel="Penalty").generate()

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

        StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root, "perception-world-model"),
                         output_fpath=os.path.join(
            self.exp_graph_root, "perception-world-model-inaccuracies.eps"),
            cols=['ST_EMPTY_inaccuracies', 'ST_HAS_BLOCK_inaccuracies',
                  'ST_HAS_CACHE_inaccuracies'],
            title="Swarm Perception Model Inaccuracies",
            legend=['ST_EMPTY', 'ST_HAS_BLOCK', 'ST_HAS_CACHE'],
            xlabel="Timestep",
            ylabel="# Inaccuracies").generate()

    def depth1_generate_linegraphs(self):
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
            self.exp_graph_root, "cache-utilization-avg-penalty.eps"),
            cols=['avg_penalty'],
            title="Swarm Cache Penalties",
            legend=['Average Penalty'],
            xlabel="Timestep",
            ylabel="# Penalty Timesteps").generate()
