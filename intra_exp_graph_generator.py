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
import matplotlib
matplotlib.use('Agg')
import pandas as pd


class IntraExpGraphGenerator:
    """
    Generates common/basic graphs experiments from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
    """

    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = os.path.abspath(exp_output_root + '/' + 'averaged-output')
        # self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_graph_root = os.path.abspath(exp_graph_root)
        os.makedirs(self.exp_graph_root, exist_ok=True)

    def generate_graphs(self):
        DistanceTraveledGraphs(self.exp_output_root, self.exp_graph_root).generate()
        GoalAcquisitionGraphs(self.exp_output_root, self.exp_graph_root, "block").generate()
        GoalAcquisitionGraphs(self.exp_output_root, self.exp_graph_root, "cache").generate()
        CumGoalAcquisitionGraphs(self.exp_output_root, self.exp_graph_root, "block").generate()
        CumGoalAcquisitionGraphs(self.exp_output_root, self.exp_graph_root, "cache").generate()
        BlockTransportGraphs(self.exp_output_root, self.exp_graph_root).generate()
        CacheUtilizationGraphs(self.exp_output_root, self.exp_graph_root).generate()
        CacheLifeCycleGraphs(self.exp_output_root, self.exp_graph_root).generate()


class DistanceTraveledGraphs:
    """
    Generates a graph of the swarm cumulative distance traveled over time from distance-stats.csv.

    If the necessary .csv file does not exist, no graphs are generated.

    """
    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_graph_root = os.path.abspath(exp_graph_root)

    def generate(self):
        path = self.exp_output_root + '/distance-stats.csv'
        if not os.path.exists(path):
                return
        df = pd.read_csv(self.exp_output_root + '/distance-stats.csv',
                         sep=';', index_col=0)
        ax = df.plot(title='Swarm Interval Cumulative Distance Traveled')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['Interval Average Distance'])
        ax.set_xlabel('Timestep')
        ax.set_ylabel('Distance (m)')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/distance-stats.eps')
        fig.clf()


class GoalAcquisitionGraphs:
    """
    Generates the following overlayed plots:

    - Average # robots [acquiring, vectoring to, exploring for] the acquisition type across intervals

    If the necessary .csv file does not exist, no graphs are generated.
    """

    def __init__(self, exp_output_root, exp_graph_root, acq_type):

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_graph_root = os.path.abspath(exp_graph_root)
        self.acq_type = acq_type

    def generate(self):
        path = self.exp_output_root + '/' + self.acq_type + '-acquisition-stats.csv'
        if not os.path.exists(path):
            return

        df = pd.read_csv(self.exp_output_root + '/' + self.acq_type + '-acquisition-stats.csv',
                         sep=';', index_col=0)

        ax = df[['avg_acquiring_goal', 'avg_vectoring_to_goal', 'avg_exploring_for_goal']].plot(title='Swarm ' +
                                                                                                self.acq_type.capitalize() +  ' Acquisition')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['# Robots Acquiring ' + self.acq_type.capitalize() + 's',
                          '# Robots Vectoring To ' + self.acq_type.capitalize() + 's',
                          '# Robots Exploring For ' + self.acq_type.capitalize() + 's'])
        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Robots')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/robots-acquiring-' + self.acq_type + 's.eps')
        fig.clf()


class CumGoalAcquisitionGraphs:
    """
    Generates the following overlayed plots from <acq_type>-acquisition-stats.csv:

    - Cumulative average # robots [acquiring, vectoring to, exploring for ] the acquisition type across intervals

    If the necessary .csv file does not exist, no graphs are generated.
    """
    def __init__(self, exp_output_root, exp_graph_root, acq_type):

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_graph_root = os.path.abspath(exp_graph_root)
        self.acq_type = acq_type

    def generate(self):
        path = self.exp_output_root + '/' + self.acq_type + '-acquisition-stats.csv'
        if not os.path.exists(path):
            return

        df = pd.read_csv(self.exp_output_root + '/' + self.acq_type + '-acquisition-stats.csv',
                         sep=';', index_col=0)

        ax = df[['avg_cum_acquiring_goal', 'avg_cum_vectoring_to_goal', 'avg_cum_exploring_for_goal']].plot(title='Swarm'
                                                                                                            + self.acq_type.capitalize() + ' Acquisition')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['# Robots Acquiring ' + self.acq_type.capitalize() + 's',
                          '# Robots Vectoring To ' + self.acq_type.capitalize() + 's',
                          '# Robots Exploring For ' + self.acq_type.capitalize() + 's'])

        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Robots')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/cum-robots-acquiring-' + self.acq_type + 's.eps')
        fig.clf()


class BlockTransportGraphs:
    """
    Generates the following plots from block-transport-stats.csv

    - # blocks collected per interval over time
    - Average block transport duration per interval over time
    - Average block initial pickup time per interval over time
    - Average # block transporters for a given block per interval over time

    If the necessary .csv file does not exist, no graphs are generated.

    """
    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_graph_root = os.path.abspath(exp_graph_root)

    def generate(self):
        path = self.exp_output_root + '/block-transport-stats.csv'
        if not os.path.exists(path):
            return

        df = pd.read_csv(self.exp_output_root + '/block-transport-stats.csv',
                         sep=';', index_col=0)

        ax = df['n_collected'].plot(title='Swarm Blocks Collected')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['# Blocks Collected (within interval)'])
        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Blocks')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/blocks-collected.eps')
        fig.clf()

        ax = df['avg_transporters'].plot(title='Average # Robots Involved in Collecting a Block')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['Average # Robots (within intervals)'])
        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Robots')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/avg-block-transporters.eps')
        fig.clf()

        ax = df['avg_transport_time'].plot(title='Average Block Transport Time')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['Average Time (within intervals)'])
        ax.set_xlabel('Timestep')
        ax.set_ylabel('Collection Time')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/avg-transport-time.eps')
        fig.clf()

        ax = df['avg_initial_wait_time'].plot(title='Average Block Initial Wait Time')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['Average Time (within intervals)'])
        ax.set_xlabel('Timestep')
        ax.set_ylabel('Wait Time')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/avg-initial-wait-time.eps')
        fig.clf()


class CacheUtilizationGraphs:
    """
    Generates the following overlayed plots from cache-utilization-stats.csv:

    - Average # of blocks in in all caches across intervals
    - Average # of cached block pickups in all caches across intervals
    - Average # of cache block drops in all caches across intervals
    - Average penalty imposed in all caches across intervals

    If the necessary .csv file does not exist, no graphs are generated.
    """
    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_graph_root = os.path.abspath(exp_graph_root)

    def generate(self):
        path = self.exp_output_root + '/cache-utilization-stats.csv'
        if not os.path.exists(path):
            return

        df = pd.read_csv(self.exp_output_root + '/cache-utilization-stats.csv',
                         sep=';', index_col=0)

        ax = df['avg_blocks'].plot(title='Average # Blocks in Caches')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['# Blocks (within interval)'])

        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Blocks')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/avg-blocks-in-caches.eps')
        fig.clf()

        ax = df['avg_pickups'].plot(title='Average # Cached Block Pickups')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['# Pickups (within interval)'])

        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Pickups')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/avg-cached-block-pickups.eps')
        fig.clf()

        ax = df['avg_drops'].plot(title='Average # Cache Block Drops')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['# Drops (within interval)'])

        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Drops')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/avg-cached-block-drops.eps')
        fig.clf()

        ax = df['avg_penalty'].plot(title='Average Cache Usage Penalty')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['Penalty (within interval)'])

        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Penalty timesteps')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/avg-cache-penalty.eps')
        fig.clf()


class CacheLifeCycleGraphs:
    """
    Generates the following overlayed plots from cache-lifecycle-stats.csv:

    - Average # of caches created in an interval
    - Average # of caches depleted in an interval

    If the necessary .csv file does not exist, no graphs are generated.
    """
    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_graph_root = os.path.abspath(exp_graph_root)

    def generate(self):
        path = self.exp_output_root + '/cache-lifecycle-stats.csv'
        if not os.path.exists(path):
            return

        df = pd.read_csv(self.exp_output_root + '/cache-lifecycle-stats.csv',
                         sep=';', index_col=0)

        ax = df.plot(title='Average # Caches Created/Depleted')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['# Created (within interval)', '# Depleted (within interval)'])

        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Caches')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/cache-lifecycle.eps')
        fig.clf()


class PerceptionWorldModelGraphs:
    """
    Generates the following overlayed plots from perception-world-model.csv:

    - Average # of ST_EMPTY, ST_CACHE, ST_BLOCK inaccuracies for all robots within an interval

    If the necessary .csv file does not exist, no graphs are generated.
    """
    def __init__(self, exp_output_root, exp_graph_root):

        self.exp_output_root = os.path.abspath(exp_output_root)
        self.exp_graph_root = os.path.abspath(exp_graph_root)

    def generate(self):
        path = self.exp_output_root + '/perception-world-model.csv'
        if not os.path.exists(path):
            return

        df = pd.read_csv(self.exp_output_root + '/perception-world-model.csv',
                         sep=';', index_col=0)

        ax = df.plot(title='Perceived World Model Inaccuracies')
        lines, labels = ax.get_legend_handles_labels()
        ax.legend(lines, ['ST_EMPTY', 'ST_HAS_BLOCK', 'ST_HAS_CACHE'])

        ax.set_xlabel('Timestep')
        ax.set_ylabel('# Inaccuracies')
        fig = ax.get_figure()
        fig.savefig(self.exp_graph_root + '/perception-world-model.eps')
        fig.clf()
