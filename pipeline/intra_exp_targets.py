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


class Linegraphs:

    """

    Linegraph intra-experiment targets.
    """

    def _depth0_targets():
        collision = [
            {
                'src_stem': 'fsm-collision',
                'dest_stem': 'fsm-collision-counts',
                'cols': ['int_avg_in_avoidance', 'cum_avg_in_avoidance',
                         'int_avg_entered_avoidance', 'cum_avg_entered_avoidance',
                         'int_avg_exited_avoidance', 'cum_avg_exited_avoidance'],
                'title': 'Swarm Collision Avoidance',
                'legend': ['Average # Robots Avoiding Collision (interval)',
                           'Average # Robots Avoiding Collision (cumulative)',
                           'Average # Robots Entered Avoidance (interval)',
                           'Average # Robots Entered Avoidance (cumulative)',
                           'Average # Robots Exited Avoidance (interval)',
                           'Average # Robots Exited Avoidance (cumulative)'],
                'xlabel': 'timestep',
                'ylabel': '# Robots'
            },
            {
                'src_stem': 'fsm-collision',
                'dest_stem': 'fsm-collision-duration',
                'cols': ['int_avg_avoidance_duration', 'cum_avg_avoidance_duration'],
                'title': 'Swarm Collision Avoidance Duration',
                'legend':['Average Avoidance Duration (interval)',
                          'Average Avoidance Duration (cumulative)'],
                'xlabel': 'timestep',
                'ylabel': '# Timesteps'
            },
        ]

        movement = [
            {
                'src_stem': 'fsm-movement',
                'dest_stem': 'fsm-movement-distance',
                'cols': ['int_avg_distance', 'cum_avg_distance'],
                'title': 'Average Per-robot Distance Traveled',
                'legend': ['Distance (interval)', 'Distance (cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Distance (m)'
            },
            {
                'src_stem': 'fsm-movement',
                'dest_stem': 'fsm-movement-velocity',
                'cols': ['int_avg_velocity', 'cum_avg_velocity'],
                'title': 'Average Per-robot Velocity',
                'legend': ['Velocity (interval)', 'Velocity (cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Velocity (m/s)'
            }
        ]

        block_trans = [
            {
                'src_stem': 'block-transport',
                'dest_stem': 'blocks-collected-int',
                'cols': ['int_collected', 'int_cube_collected', 'int_ramp_collected'],
                'legend': ['All Blocks', '# Cube Blocks', '# Ramp Blocks'],
                'title': 'Blocks Collected (interval)',
                'xlabel': 'timestep',
                'ylabel': '# Blocks'
            },
            {
                'src_stem': 'block-transport',
                'dest_stem': 'blocks-collected-cum',
                'cols': ['cum_collected', 'cum_cube_collected', 'cum_ramp_collected'],
                'title': 'Blocks Collected (cumulative)',
                'legend': ['All Blocks', '# Cube Blocks', '# Ramp Blocks'],
                'xlabel': 'timestep',
                'ylabel': '# Blocks'
            },
            {
                'src_stem': 'block-transport',
                'dest_stem': 'block-transporters-int',
                'cols': ['int_avg_transporters', 'cum_avg_transporters'],
                'title': "Swarm Block Average Transporters",
                'legend': ['Average # Transporters Per Block (interval)',
                           'Average # Transporters Per Block (cumulative)'],
                'xlabel': 'timestep',
                'ylabel': '# Transporters'
            },
            {
                'src_stem': 'block-transport',
                'dest_stem': 'block-transporters-cum',
                'cols': ['int_avg_transport_time', 'cum_avg_transport_time',
                         'int_avg_initial_wait_time', 'cum_avg_initial_wait_time'],
                'title': "Swarm Block Transport Time",
                'legend': ['Average Transport Time (interval)',
                           'Average Transport Time (cumulative)',
                           "Average Initial Wait Time (interval)",
                           'Average Initial Wait Time (cumulative)'],
                'xlabel': 'timestep',
                'ylabel': '# Timesteps'
            }
        ]
        block_acq = [
            {
                'src_stem': 'block-acquisition',
                'dest_stem': 'blocks-acq-counts',
                'cols': ['int_avg_acquiring_goal', 'cum_avg_acquiring_goal',
                         'int_avg_vectoring_to_goal', 'cum_avg_vectoring_to_goal',
                         'int_avg_exploring_for_goal', 'cum_avg_exploring_for_goal'],
                'title': "Swarm Block Acquisition",
                'legend': ['Average # Robots Acquiring Blocks (interval)',
                           'Average # Robots Acquiring Blocks (cumulative)',
                           'Average # Robots Vectoring To Blocks (interval)',
                           'Average # Robots Vectoring To Blocks (cumulative)',
                           'Average # Robots Exploring For Blocks (interval)',
                           'Average # Robots Exploring For Blocks (cumulative)'],
                'xlabel': 'timestep',
                'ylabel': '# Robots'
            },
        ]

        block_manip = [
            {
                'src_stem': 'block-manipulation',
                'dest_stem': 'block-manip-events',
                'cols': ['int_avg_free_pickup_events', 'int_avg_free_drop_events',
                         'int_avg_cache_pickup_events', 'int_avg_cache_drop_events'],
                'title': "Block Manipulation Pickups/Drops",
                'legend': ['Average # Free Pickups (interval)',
                           'Average # Free Drops (interval)',
                           'Average # Cache Pickups (interval)',
                           'Average # Cache Drops (interval)'],
                'xlabel': 'timestep',
                'ylabel': '# Pickups/Drops'
            },
            {
                'src_stem': 'block-manipulation',
                'dest_stem': 'block-manip-penalties',
                'cols': ['int_avg_free_pickup_penalty', 'int_avg_free_drop_penalty',
                         'int_avg_cache_pickup_penalty', 'int_avg_cache_drop_penalty'],
                'title': "Block Manipulation Penalties",
                'legend': ['Average Free Pickup Penalty (interval)',
                           'Average Free Drop Penalty (interval)',
                           'Average Cache Picup Penalty (interval)',
                           'Average Cache Drop Penalty (interval)'],
                'xlabel': 'timestep',
                'ylabel': 'Penalty'
            },
        ]
        world_model = [
            {
                'src_stem': 'perception-world-model',
                'dest_stem': 'perception-world-model',
                'cols': ['ST_EMPTY_inaccuracies', 'ST_HAS_BLOCK_inaccuracies',
                         'ST_HAS_CACHE_inaccuracies'],
                'title': "Swarm Perception Model Inaccuracies",
                'legend': ['ST_EMPTY (interval)', 'ST_HAS_BLOCK (interval)',
                           'ST_HAS_CACHE (interval)'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]

        return {'fsm-collision': collision,
                'fsm-movement': movement,
                'block_trans': block_trans,
                'block_acq': block_acq,
                'block_manip': block_manip,
                'world_model': world_model
                }

    def _depth1_targets():
        cache_util = [
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-opcounts-int',
                'cols': ['int_avg_pickups', 'int_avg_drops'],
                'title': "Average # Pickups/Drops Across All Caches (Interval)",
                'legend': ['Average # Pickups', 'Average # Drops'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-cache-counts-int',
                'cols': ['int_unique_caches'],
                'title': "# Caches in Arena (Interval)",
                'legend': ['# Caches'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]
        cache_lifecycle = [
            {
                'src_stem': 'cache-lifecycle',
                'dest_stem': 'cache-lifecyle-int',
                'cols': ['int_created', 'int_depleted'],
                'title': "# Caches Created/Depleted (Interval)",
                'legend': ['# Created', '# Depleted'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]
        cache_acq = [
            {
                'src_stem': 'cache-acquisition',
                'dest_stem': 'caches-acq-counts',
                'cols': ['int_avg_acquiring_goal', 'cum_avg_acquiring_goal',
                         'int_avg_vectoring_to_goal', 'cum_avg_vectoring_to_goal',
                         'int_avg_exploring_for_goal', 'cum_avg_exploring_for_goal'],
                'title': "Swarm Cache Acquisition",
                'legend': ['Average # Robots Acquiring Caches (interval)',
                           'Average # Robots Acquiring Caches (cumulative)',
                           'Average # Robots Vectoring To Caches (interval)',
                           'Average # Robots Vectoring To Caches (cumulative)',
                           'Average # Robots Exploring For Caches (interval)',
                           'Average # Robots Exploring For Caches (cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]
        task_exec = [
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-counts',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Collector Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-times',
                'cols': ['int_abort_count', 'cum_avg_abort_count',
                         'int_complete_count', 'cum_avg_complete_count'],
                'title': "Collector Abort/Completion Counts",
                'legend': ['Abort Count (Interval)',
                           'Average Abort Count (Cumulative)',
                           'Completion Count (Interval)',
                           'Average Completion Count (Cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-counts',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Harvester Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-times',
                'cols': ['int_abort_count', 'cum_avg_abort_count',
                         'int_complete_count', 'cum_avg_complete_count'],
                'title': "Harvester Abort/Completion Counts",
                'legend': ['Abort Count (Interval)',
                           'Average Abort Count (Cumulative)',
                           'Completion Count (Interval)',
                           'Average Completion Count (Cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-counts',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Generalist Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-times',
                'cols': ['int_abort_count', 'cum_avg_abort_count',
                         'int_complete_count', 'cum_avg_complete_count'],
                'title': "Generalist Abort/Completion Counts",
                'legend': ['Abort Count (Interval)',
                           'Average Abort Count (Cumulative)',
                           'Completion Count (Interval)',
                           'Average Completion Count (Cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]
        generalist_tab = [
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask-counts',
                'cols': ['int_subtask1_count', 'cum_avg_subtask1_count',
                         'int_subtask2_count', 'cum_avg_subtask2_count'],
                'title': "Generalist TAB Subtask Selection Counts",
                'legend': ['Subtask1 (Interval)',
                           'Subtask1 (Cumulative)',
                           'Subtask2 (Interval)',
                           'Subtask2 (Cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-counts',
                'cols': ['int_partition_count', 'cum_avg_partition_count',
                         'int_no_partition_count', 'cum_avg_no_partition_count'],
                'title': "Generalist TAB Partition Counts",
                'legend': ['Partition (Interval)',
                           'Partition (Cumulative)',
                           'No Partition (Interval)',
                           'No Partition (Cumulative)'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-sw-counts',
                'cols': ['int_task_sw_count', 'cum_task_sw_count'],
                'title': "Generalist TAB Task Switch Counts",
                'legend': ['Interval', 'Cumulative'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]
        return {'cache_util': cache_util,
                'cache_lifecycle': cache_lifecycle,
                'cache_acq': cache_acq,
                'task_exec': task_exec,
                'generalist_tab': generalist_tab}

    def targets():
        """
        Get a list of dictionaries specifying all the graphs that should be created within an
        experiment (i.e. across simulation runs).
        """
        d = Linegraphs._depth0_targets()
        d.update(Linegraphs._depth1_targets())
        return d


class Histograms:
    """Histogram intra-experiment targets."""

    def targets():
        """Get the histogram targets, which are shared with linegraphs"""
        return Linegraphs.targets()


class Heatmaps:
    """Heatmap intra-experiment targets."""

    def targets():
        arena = [
            {
                'src_stem': 'arena-robot-occupancy',
                'title': "Robot Occupancy Probability",
            }
        ]
        return {'arena': arena}
