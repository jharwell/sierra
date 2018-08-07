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


class IntraExpLinegraphs:
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
        self.depth0_generate_linegraphs()

    def depth0_generate_linegraphs(self):
        for target_set in [self.targets[x] for x in ['collision',
                                                     'distance',
                                                     'block_trans',
                                                     'block_acq',
                                                     'block_manip',
                                                     'world_model']]:
            for target in target_set:
                StackedLineGraph(input_stem_fpath=os.path.join(self.exp_output_root,
                                                               target['src_stem']),
                                 output_fpath=os.path.join(
                                     self.exp_graph_root,
                                     target['src_stem'] + '.eps'),
                                 cols=target['cols'],
                                 title=target['title'],
                                 legend=target['legend'],
                                 xlabel=target['xlabel'],
                                 ylabel=target['ylabel']).generate()


#
# @FIXME This will be moved to a diction in the main pipeline file once I
# get depth1 stuff working. Leaving here for now, because big parts of it can be copy-pasted.
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
