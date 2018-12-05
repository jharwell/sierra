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
                'xlabel': 'Interval',
                'ylabel': '# Robots'
            },
            {
                'src_stem': 'fsm-collision',
                'dest_stem': 'fsm-collision-duration',
                'cols': ['int_avg_avoidance_duration', 'cum_avg_avoidance_duration'],
                'title': 'Swarm Collision Avoidance Duration',
                'legend':['Average Avoidance Duration (interval)',
                          'Average Avoidance Duration (cumulative)'],
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
                'ylabel': 'Distance (m)'
            },
            {
                'src_stem': 'fsm-movement',
                'dest_stem': 'fsm-movement-velocity',
                'cols': ['int_avg_velocity', 'cum_avg_velocity'],
                'title': 'Average Per-robot Velocity',
                'legend': ['Velocity (interval)', 'Velocity (cumulative)'],
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
                'ylabel': '# Blocks'
            },
            {
                'src_stem': 'block-transport',
                'dest_stem': 'blocks-collected-cum',
                'cols': ['cum_collected', 'cum_cube_collected', 'cum_ramp_collected'],
                'title': 'Blocks Collected (cumulative)',
                'legend': ['All Blocks', '# Cube Blocks', '# Ramp Blocks'],
                'xlabel': 'Interval',
                'ylabel': '# Blocks'
            },
            {
                'src_stem': 'block-transport',
                'dest_stem': 'block-transporters-int',
                'cols': ['int_avg_transporters', 'cum_avg_transporters'],
                'title': "Swarm Block Average Transporters",
                'legend': ['Average # Transporters Per Block (interval)',
                           'Average # Transporters Per Block (cumulative)'],
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
        ]
        convergence = [
            {
                'src_stem': 'swarm-convergence',
                'dest_stem': 'swarm-conv-int-deg-raw',
                'cols': ['int_avg_interact_deg_raw', 'int_avg_interact_deg_raw_dt'],
                'title': "Swarm Convergence (Interaction Degree)",
                'legend': ['Raw', 'DT'],
                'xlabel': 'Interval',
                'ylabel': 'Degree'
            },
            {
                'src_stem': 'swarm-convergence',
                'dest_stem': 'swarm-conv-int-deg-norm',
                'cols': ['int_avg_interact_deg_norm', 'int_avg_interact_deg_norm_dt'],
                'title': "Swarm Convergence (Interaction Degree)",
                'legend': ['Normalized', 'DT'],
                'xlabel': 'Interval',
                'ylabel': 'Degree'
            },
            {
                'src_stem': 'swarm-convergence',
                'dest_stem': 'swarm-conv-ang-order',
                'cols': ['int_avg_ang_order', 'int_avg_ang_order_dt'],
                'title': "Swarm Convergence (Angular Order)",
                'legend': ['Order', 'DT'],
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'swarm-convergence',
                'dest_stem': 'swarm-conv-pos-entropy',
                'cols': ['int_avg_pos_entropy', 'int_avg_pos_entropy_dt'],
                'title': "Swarm Convergence (Positional Entropy)",
                'legend': ['Entropy', 'DT'],
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
        ]
        return {'fsm-collision': collision,
                'fsm-movement': movement,
                'block_trans': block_trans,
                'block_acq': block_acq,
                'block_manip': block_manip,
                'world_model': world_model,
                'convergence': convergence
                }

    def _depth1_targets():
        cache_util = [
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-opcounts',
                'cols': ['int_avg_pickups', 'int_avg_drops',
                         'cum_avg_pickups', 'cum_avg_drops'],
                'title': "Average # Pickups/Drops Across All Caches",
                'legend': ['Average # Pickups (Interval)', 'Average # Drops (Interval)',
                           'Average # Pickups (Cumulative)', 'Average # Drops (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-cache-counts',
                'cols': ['int_unique_caches', 'cum_unique_caches'],
                'title': "# Unique Caches in Arena",
                'legend': ['# Caches (Interval)', '# Caches (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-block-counts',
                'cols': ['int_avg_blocks', 'cum_avg_blocks'],
                'title': "# Blocks in Caches",
                'legend': ['Average # Blocks (Interval)', 'Average # Blocks (Cumulative)'],
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
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
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
        ]
        task_exec = [
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-times',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Collector Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-ests',
                'cols': ['int_avg_exec_estimate', 'cum_avg_exec_estimate',
                         'int_avg_interface_estimate', 'cum_avg_interface_estimate'],
                'title': "Collector Execution/Interface Estimates",
                'legend': ['Average Exec Estimate (Interval)',
                           'Average Exec Estimate (Cumulative)',
                           'Average Interface Estimate (Interval)',
                           'Average Interface Estimate (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },

            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-counts',
                'cols': ['int_avg_abort_count', 'cum_avg_abort_count',
                         'int_avg_complete_count', 'cum_avg_complete_count'],
                'title': "Collector Abort/Completion Counts",
                'legend': ['Average Abort Count (Interval)',
                           'Average Abort Count (Cumulative)',
                           'Average Completion Count (Interval)',
                           'Average Completion Count (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-times',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Harvester Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-ests',
                'cols': ['int_avg_exec_estimate', 'cum_avg_exec_estimate',
                         'int_avg_interface_estimate', 'cum_avg_interface_estimate'],
                'title': "Harvester Execution/Interface Estimates",
                'legend': ['Average Exec Estimate (Interval)',
                           'Average Exec Estimate (Cumulative)',
                           'Average Interface Estimate (Interval)',
                           'Average Interface Estimate (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-counts',
                'cols': ['int_avg_abort_count', 'cum_avg_abort_count',
                         'int_avg_complete_count', 'cum_avg_complete_count'],
                'title': "Harvester Abort/Completion Counts",
                'legend': ['Average Abort Count (Interval)',
                           'Average Abort Count (Cumulative)',
                           'Average Completion Count (Interval)',
                           'Average Completion Count (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-times',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Generalist Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-counts',
                'cols': ['int_avg_abort_count', 'cum_avg_abort_count',
                         'int_avg_complete_count', 'cum_avg_complete_count'],
                'title': "Generalist Abort/Completion Counts",
                'legend': ['Average Abort Count (Interval)',
                           'Average Average Abort Count (Cumulative)',
                           'Average Completion Count (Interval)',
                           'Average Completion Count (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-ests',
                'cols': ['int_avg_exec_estimate', 'cum_avg_exec_estimate'],
                'title': "Generalist Execution Estimates",
                'legend': ['Average Exec Estimate (Interval)',
                           'Average Exec Estimate (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },

        ]
        generalist_tab = [
            {
                'src_stem': 'task-tab-generalist',
                'dest_stem': 'task-tab-generalist-subtask-counts',
                'cols': ['int_avg_subtask1_count', 'cum_avg_subtask1_count',
                         'int_avg_subtask2_count', 'cum_avg_subtask2_count'],
                'title': "Average Generalist TAB Subtask Selection Counts",
                'legend': ['Harvester (Interval)',
                           'Harvester (Cumulative)',
                           'Collector (Interval)',
                           'Collector (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-generalist',
                'dest_stem': 'task-tab-generalist-partition-counts',
                'cols': ['int_avg_partition_count', 'cum_avg_partition_count',
                         'int_avg_no_partition_count', 'cum_avg_no_partition_count'],
                'title': "Averge Generalist TAB Partition Counts",
                'legend': ['Partition (Interval)',
                           'Partition (Cumulative)',
                           'No Partition (Interval)',
                           'No Partition (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-generalist',
                'dest_stem': 'task-tab-generalist-task-sw-counts',
                'cols': ['int_avg_task_sw_count', 'cum_avg_task_sw_count'],
                'title': "Average Generalist TAB Task Switch Counts",
                'legend': ['Interval', 'Cumulative'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-generalist',
                'dest_stem': 'task-tab-generalist-task-sw-counts',
                'cols': ['int_avg_task_sw_count', 'cum_avg_task_sw_count'],
                'title': "Average Generalist TAB Task Switch Counts",
                'legend': ['Interval', 'Cumulative'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-generalist',
                'dest_stem': 'task-tab-generalist-task-depth-sw-counts',
                'cols': ['int_avg_task_depth_sw_count', 'cum_avg_task_depth_sw_count'],
                'title': "Average Generalist TAB Task Depth Switch Counts",
                'legend': ['Interval', 'Cumulative'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-generalist',
                'dest_stem': 'task-tab-generalist-prob',
                'cols': ['int_avg_partition_prob', 'cum_avg_partition_prob',
                         'int_avg_subtask_selection_prob', 'cum_avg_subtask_selection_prob'],
                'title': "Generalist TAB Partition/Subtask Selection Probabilities",
                'legend': ['Partition Probability (Interval Average)',
                           'Partition Probability (Cumulative Average)',
                           'Subtask Selection Probability (Interval Average)',
                           'Subtask Selection Probability (Cumulative Average)'],
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },

        ]
        task_dist = [
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-int-depth-counts',
                'cols': ['int_avg_depth0_count', 'cum_avg_depth0_count',
                         'int_avg_depth1_count', 'cum_avg_depth1_count'],
                'title': "Task Distribution Depth Counts",
                'legend': ['Depth0 (Interval)',
                           'Depth0 (Cumulative Average)',
                           'Depth1 (Interval)',
                           'Depth1 (Cumulative Average)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts',
                'cols': ['int_avg_task0_count', 'cum_avg_task0_count',
                         'int_avg_task1_count', 'cum_avg_task1_count',
                         'int_avg_task2_count', 'cum_avg_task2_count'],
                'title': "Task Distribution Task Counts",
                'legend': ['Average Generalist (Interval)',
                           'Average Generalist (Cumulative)',
                           'Average Harvester (Interval)',
                           'Average Harvester (Cumulative)',
                           'Average Collector (Interval)',
                           'Average Collector (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-tab-counts',
                'cols': ['int_avg_tab0_count', 'cum_avg_tab0_count'],
                'title': "Task Distribution TAB Counts",
                'legend': ['TAB0 (Interval)', 'TAB0 (Cumulative Average)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },

        ]

        return {'cache_util': cache_util,
                'cache_lifecycle': cache_lifecycle,
                'cache_acq': cache_acq,
                'depth1_task_exec': task_exec,
                'depth1_task_dist': task_dist,
                'generalist_tab': generalist_tab}

    def _depth2_targets():
        task_dist = [
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-int-depth-counts',
                'cols': ['int_avg_depth0_count', 'cum_avg_depth0_count',
                         'int_avg_depth1_count', 'cum_avg_depth1_count',
                         'int_avg_depth2_count', 'cum_avg_depth2_count'],
                'title': "Task Distribution Depth Counts",
                'legend': ['Depth0 (Interval)',
                           'Depth0 (Cumulative Average)',
                           'Depth1 (Interval)',
                           'Depth1 (Cumulative Average)',
                           'Depth2 (Interval)',
                           'Depth2 (Cumulative Average)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts',
                'cols': ['int_avg_task0_count', 'cum_avg_task0_count',
                         'int_avg_task1_count', 'cum_avg_task1_count',
                         'int_avg_task2_count', 'cum_avg_task2_count',
                         'int_avg_task3_count', 'cum_avg_task3_count'
                         'int_avg_task4_count', 'cum_avg_task4_count'
                         'int_avg_task5_count', 'cum_avg_task5_count'
                         'int_avg_task6_count', 'cum_avg_task6_count'],
                'title': "Task Distribution Task Counts",
                'legend': ['Average Generalist (Interval)',
                           'Average Generalist (Cumulative)',
                           'Average Harvester (Interval)',
                           'Average Harvester (Cumulative)',
                           'Average Collector (Interval)',
                           'Average Collector (Cumulative)'
                           'Average Cache Starter (Interval)',
                           'Average Cache Starter (Cumulative)'
                           'Average Cache Finisher (Interval)',
                           'Average Cache Finisher (Cumulative)'
                           'Average Cache Transferer (Interval)',
                           'Average Cache Transferer (Cumulative)'
                           'Average Cache Collector (Interval)',
                           'Average Cache Collector (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-tab-counts',
                'cols': ['int_tab0_count', 'cum_avg_tab0_count',
                         'int_tab1_count', 'cum_avg_tab1_count'
                         'int_tab2_count', 'cum_avg_tab2_count'],
                'title': "Task Distribution TAB Counts",
                'legend': ['TAB0 (Interval)', 'TAB0 (Cumulative Average)',
                           'TAB1 (Interval)', 'TAB1 (Cumulative Average)'
                           'TAB2 (Interval)', 'TAB2 (Cumulative Average)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },

        ]
        harvester_tab = [
            {
                'src_stem': 'task-tab-harvester',
                'dest_stem': 'task-tab-harvester-subtask-counts',
                'cols': ['int_avg_subtask1_count', 'cum_avg_subtask1_count',
                         'int_avg_subtask2_count', 'cum_avg_subtask2_count'],
                'title': "Average Harvester TAB Subtask Selection Counts",
                'legend': ['Cache Starter (Interval)',
                           'Cache Starter (Cumulative)',
                           'Cache Finisher (Interval)',
                           'Cache Finisher (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-harvester',
                'dest_stem': 'task-tab-harvester-partition-counts',
                'cols': ['int_avg_partition_count', 'cum_avg_partition_count',
                         'int_avg_no_partition_count', 'cum_avg_no_partition_count'],
                'title': "Average Harvester TAB Partition Counts",
                'legend': ['Partition (Interval)',
                           'Partition (Cumulative)',
                           'No Partition (Interval)',
                           'No Partition (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-harvester',
                'dest_stem': 'task-tab-harvester-task-sw-counts',
                'cols': ['int_avg_task_sw_count', 'cum_avg_task_sw_count'],
                'title': "Average Harvester TAB Task Switch Counts",
                'legend': ['Interval', 'Cumulative'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-harvester',
                'dest_stem': 'task-tab-harvester-task-depth-sw-counts',
                'cols': ['int_avg_task_depth_sw_count', 'cum_avg_task_depth_sw_count'],
                'title': "Average Harvester TAB Task Depth Switch Counts",
                'legend': ['Interval', 'Cumulative'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-harvester',
                'dest_stem': 'task-tab-harvester-prob',
                'cols': ['int_avg_partition_prob', 'cum_avg_partition_prob',
                         'int_avg_subtask_selection_prob', 'cum_avg_subtask_selection_prob'],
                'title': "Harvester TAB Partition/Subtask Selection Probabilities",
                'legend': ['Partition Probability (Interval Average)',
                           'Partition Probability (Cumulative Average)',
                           'Subtask Selection Probability (Interval Average)',
                           'Subtask Selection Probability (Cumulative Average)'],
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
        ]
        collector_tab = [
            {
                'src_stem': 'task-tab-collector',
                'dest_stem': 'task-tab-collector-subtask-counts',
                'cols': ['int_avg_subtask1_count', 'cum_avg_subtask1_count',
                         'int_avg_subtask2_count', 'cum_avg_subtask2_count'],
                'title': "Average Collector TAB Subtask Selection Counts",
                'legend': ['Cache Transferer (Interval)',
                           'Cache Transferer (Cumulative)',
                           'Cache Collector (Interval)',
                           'Cache Collector (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-collector',
                'dest_stem': 'task-tab-collector-partition-counts',
                'cols': ['int_avg_partition_count', 'cum_avg_partition_count',
                         'int_avg_no_partition_count', 'cum_avg_no_partition_count'],
                'title': "Average Collector TAB Partition Counts",
                'legend': ['Partition (Interval)',
                           'Partition (Cumulative)',
                           'No Partition (Interval)',
                           'No Partition (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-collector',
                'dest_stem': 'task-tab-collector-task-sw-counts',
                'cols': ['int_avg_task_sw_count', 'cum_avg_task_sw_count'],
                'title': "Average Collector TAB Task Switch Counts",
                'legend': ['Interval', 'Cumulative'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-collector',
                'dest_stem': 'task-tab-collector-task-depth-sw-counts',
                'cols': ['int_avg_task_depth_sw_count', 'cum_avg_task_depth_sw_count'],
                'title': "Average Collector TAB Task Depth Switch Counts",
                'legend': ['Interval', 'Cumulative'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-tab-collector',
                'dest_stem': 'task-tab-collector-prob',
                'cols': ['int_avg_partition_prob', 'cum_avg_partition_prob',
                         'int_avg_subtask_selection_prob', 'cum_avg_subtask_selection_prob'],
                'title': "Collector TAB Partition/Subtask Selection Probabilities",
                'legend': ['Partition Probability (Interval Average)',
                           'Partition Probability (Cumulative Average)',
                           'Subtask Selection Probability (Interval Average)',
                           'Subtask Selection Probability (Cumulative Average)'],
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
        ]
        task_exec = [
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-times',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Cache Starter Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-ests',
                'cols': ['int_avg_exec_estimate', 'cum_avg_exec_estimate',
                         'int_avg_interface_estimate', 'cum_avg_interface_estimate'],
                'title': "Cache Starter Execution/Interface Estimates",
                'legend': ['Average Exec Estimate (Interval)',
                           'Average Exec Estimate (Cumulative)',
                           'Average Interface Estimate (Interval)',
                           'Average Interface Estimate (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },

            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-counts',
                'cols': ['int_avg_abort_count', 'cum_avg_abort_count',
                         'int_avg_complete_count', 'cum_avg_complete_count'],
                'title': "Cache Starter Abort/Completion Counts",
                'legend': ['Average Abort Count (Interval)',
                           'Average Abort Count (Cumulative)',
                           'Average Completion Count (Interval)',
                           'Average Completion Count (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-times',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Cache Finisher Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-ests',
                'cols': ['int_avg_exec_estimate', 'cum_avg_exec_estimate',
                         'int_avg_interface_estimate', 'cum_avg_interface_estimate'],
                'title': "Cache Finisher Execution/Interface Estimates",
                'legend': ['Average Exec Estimate (Interval)',
                           'Average Exec Estimate (Cumulative)',
                           'Average Interface Estimate (Interval)',
                           'Average Interface Estimate (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-counts',
                'cols': ['int_avg_abort_count', 'cum_avg_abort_count',
                         'int_avg_complete_count', 'cum_avg_complete_count'],
                'title': "Cache Finisher Abort/Completion Counts",
                'legend': ['Average Abort Count (Interval)',
                           'Average Average Abort Count (Cumulative)',
                           'Average Completion Count (Interval)',
                           'Average Average Completion Count (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-transferer-times',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Cache Transferer Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-ests',
                'cols': ['int_avg_exec_estimate', 'cum_avg_exec_estimate',
                         'int_avg_interface_estimate', 'cum_avg_interface_estimate'],
                'title': "Cache Transferer Execution/Interface Estimates",
                'legend': ['Average Exec Estimate (Interval)',
                           'Average Exec Estimate (Cumulative)',
                           'Average Interface Estimate (Interval)',
                           'Average Interface Estimate (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },

            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-counts',
                'cols': ['int_avg_abort_count', 'cum_avg_abort_count',
                         'int_avg_complete_count', 'cum_avg_complete_count'],
                'title': "Cache Transferer Abort/Completion Counts",
                'legend': ['Average Abort Count (Interval)',
                           'Average Abort Count (Cumulative)',
                           'Average Completion Count (Interval)',
                           'Average Completion Count (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-times',
                'cols': ['int_avg_exec_time', 'cum_avg_exec_time',
                         'int_avg_interface_time', 'cum_avg_interface_time'],
                'title': "Cache Collector Execution/Interface Times",
                'legend': ['Average Exec Time (Interval)',
                           'Average Exec Time (Cumulative)',
                           'Average Interface Time (Interval)',
                           'Average Interface Time (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-ests',
                'cols': ['int_avg_exec_estimate', 'cum_avg_exec_estimate',
                         'int_avg_interface_estimate', 'cum_avg_interface_estimate'],
                'title': "Cache Collector Execution/Interface Estimates",
                'legend': ['Average Exec Estimate (Interval)',
                           'Average Exec Estimate (Cumulative)',
                           'Average Interface Estimate (Interval)',
                           'Average Interface Estimate (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-counts',
                'cols': ['int_avg_abort_count', 'cum_avg_abort_count',
                         'int_avg_complete_count', 'cum_avg_complete_count'],
                'title': "Cache Collector Abort/Completion Counts",
                'legend': ['Average Abort Count (Interval)',
                           'Average Average Abort Count (Cumulative)',
                           'Average Completion Count (Interval)',
                           'Average Average Completion Count (Cumulative)'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
        ]

        return {"depth2_task_dist": task_dist,
                "depth2_task_exec": task_exec,
                "harvester_tab": harvester_tab,
                "collector_tab": collector_tab}

    def targets(gen_depth2):
        """
        Get a list of dictionaries specifying all the graphs that should be created within an
        experiment (i.e. across simulation runs).
        """
        d = Linegraphs._depth0_targets()
        d.update(Linegraphs._depth1_targets())
        if gen_depth2:
            d.update(Linegraphs._depth2_targets())
        return d


class Histograms:
    """Histogram intra-experiment targets."""

    def targets():
        """Get the histogram targets, which are shared with linegraphs"""
        return Linegraphs.targets(False)


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
