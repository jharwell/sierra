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

    Linegraph inter-experiment targets.
    """

    def _depth0_targets():
        collision = [
            {
                'src_stem': 'fsm-collision',
                'col': 'int_avg_in_avoidance',
                'dest_stem': 'ca-in-int-avg',
                'title': 'Average Robots in Collision Avoidance (interval)',
                'xlabel': 'Interval',
                'ylabel': '# Robots',
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'cum_avg_in_avoidance',
                'dest_stem': 'ca-in-cum-avg',
                'title': 'Average Robots in Collision Avoidance (cumulative)',
                'xlabel': 'Interval',
                'ylabel': '# Robots'},
            {
                'src_stem': 'fsm-collision',
                'col': 'int_avg_entered_avoidance',
                'dest_stem': 'ca-entered-int-avg',
                'title': 'Average Robots Entering Collision Avoidance (interval)',
                'xlabel': 'Interval',
                'ylabel': '# Robots'
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'cum_avg_entered_avoidance',
                'dest_stem': 'ca-entered-cum-avg',
                'title': 'Average Robots Entering Collision Avoidance (cumulative)',
                'xlabel': 'Interval',
                'ylabel': '# Robots',
                'analytical_model': 'CAModelEnter'
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'int_avg_exited_avoidance',
                'dest_stem': 'ca-exited-int-avg',
                'title': 'Average Robots Exiting Collision Avoidance (interval)',
                'xlabel': 'Interval',
                'ylabel': '# Robots'
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'cum_avg_exited_avoidance',
                'dest_stem': 'ca-exited-cum-avg',
                'title': 'Average Robots Exiting Collision Avoidance (cumulative)',
                'xlabel': 'Interval',
                'ylabel': '# Robots'
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'int_avg_avoidance_duration',
                'dest_stem': 'ca-duration-int-avg',
                'title': 'Average Collision Avoidance Duration (interval)',
                'xlabel': 'Interval',
                'ylabel': '# Robots',
                'analytical_model': 'CAModelDuration'
            },
            {'src_stem': 'fsm-collision',
             'col': 'cum_avg_avoidance_duration',
             'dest_stem': 'ca-duration-cum-avg',
             'title': 'Average Collision Avoidance Duration (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
        ]

        movement = [
            {
                'src_stem': 'fsm-movement',
                'col': 'int_avg_distance',
                'dest_stem': 'distance-int-avg',
                'title': 'Per-robot Distance Traveled (interval)',
                'xlabel': 'Interval',
                'ylabel': 'Distance (m)'
            },
            {
                'src_stem': 'fsm-movement',
                'col': 'cum_avg_distance',
                'dest_stem': 'distance-cum-avg',
                'title': 'Per-robot Distance Traveled (cumulative)',
                'xlabel': 'Interval',
                'ylabel': 'Distance (m)'},
            {
                'src_stem': 'fsm-movement',
                'col': 'int_avg_velocity',
                'dest_stem': 'velocity-int-avg',
                'title': 'Per-robot Velocity (interval)',
                'xlabel': 'Interval',
                'ylabel': 'Velocity (m/s)'
            },
            {
                'src_stem': 'fsm-movement',
                'col': 'cum_avg_velocity',
                'dest_stem': 'velocity-cum-avg',
                'title': 'Per-robot Velocity (cumulative)',
                'xlabel': 'Interval',
                'ylabel': 'Velocity (m/s)'}
        ]

        block_trans = [
            {
                'src_stem': 'block-transport',
                'col': 'int_collected',
                'dest_stem': 'blocks-collected-int',
                'title': 'Blocks Collected (interval)',
                'xlabel': 'Interval',
                'ylabel': '# Blocks'},
            {
                'src_stem': 'block-transport',
                'col': 'cum_collected',
                'dest_stem': 'blocks-collected-cum',
                'title': 'Blocks Collected (cumulative)',
                'xlabel': 'Interval',
                'ylabel': '# Blocks'
            },
            {'src_stem': 'block-transport',
             'col': 'int_cube_collected',
             'dest_stem': 'cube-blocks-collected-int',
             'title': 'Cube Blocks Collected (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Blocks'},
            {'src_stem': 'block-transport',
             'col': 'int_ramp_collected',
             'dest_stem': 'ramp-blocks-collected-int',
             'title': 'Ramp Blocks Collected (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Blocks'
             },
            {'src_stem': 'block-transport',
             'col': 'cum_collected',
             'dest_stem': 'blocks-collected-cum-avg',
             'title': 'Average Blocks Collected (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Blocks'
             },
            {'src_stem': 'block-transport',
             'col': 'cum_cube_collected',
             'dest_stem': 'cube-blocks-collected-cum-avg',
             'title': 'Average Cube Blocks Collected (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Blocks'},
            {'src_stem': 'block-transport',
             'col': 'cum_ramp_collected',
             'dest_stem': 'ramp-blocks-collected-cum-avg',
             'title': 'Average Ramp Blocks Collected (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Blocks'
             },
            {'src_stem': 'block-transport',
             'col': 'int_avg_transporters',
             'dest_stem': 'block-transporters-int-avg',
             'title': 'Average Block Transporters (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-transport',
             'col': 'cum_avg_transporters',
             'dest_stem': 'block-transporters-cum-avg',
             'title': 'Average Block Transporters (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-transport',
             'col': 'int_avg_transport_time',
             'dest_stem': 'blocks-transport-time-int-avg',
             'title': 'Average Block Transport Time (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Timesteps'
             },
            {'src_stem': 'block-transport',
             'col': 'cum_avg_transport_time',
             'dest_stem': 'blocks-transport-time-cum-avg',
             'title': 'Average Block Transport Time (Cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Timesteps'
             },
            {'src_stem': 'block-transport',
             'col': 'int_avg_initial_wait_time',
             'dest_stem': 'blocks-initial-wait-time-int-avg',
             'title': 'Average Block Initial Wait Time (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Timesteps'},
            {'src_stem': 'block-transport',
             'col': 'cum_avg_initial_wait_time',
             'dest_stem': 'blocks-initial-wait-time-cum-avg',
             'title': 'Average Block Initial Wait Time (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'},
        ]
        block_acq = [
            {'src_stem': 'block-acquisition',
             'col': 'int_avg_acquiring_goal',
             'dest_stem': 'block-acquisition-int-avg',
             'title': 'Average Robots Acquiring Blocks (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'int_avg_vectoring_to_goal',
             'dest_stem': 'block-acquisition-vectoring-int-avg',
             'title': 'Average Robots Vectoring To Blocks (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'int_avg_exploring_for_goal',
             'dest_stem': 'block-acquisition-exploring-int-avg',
             'title': 'Average Robots Exploring For Blocks (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'cum_avg_acquiring_goal',
             'dest_stem': 'block-acquisition-cum-avg',
             'title': 'Average Robots Acquiring Blocks (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'cum_avg_vectoring_to_goal',
             'dest_stem': 'block-acquisition-vectoring-cum-avg',
             'title': 'Average Robots Vectoring To Blocks (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'cum_avg_exploring_for_goal',
             'dest_stem': 'block-acquisition-exploring-cum-avg',
             'title': 'Average Robots Exploring For Blocks (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             }
        ]

        block_manip = [
            {'src_stem': 'block-manipulation',
             'col': 'int_avg_free_pickup_events',
             'dest_stem': 'free-pickup-events-int-avg',
             'title': 'Average Free Block Pickup Events (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Pickups'},
            {'src_stem': 'block-manipulation',
             'col': 'int_avg_free_drop_events',
             'dest_stem': 'free-drop-events-int-avg',
             'title': 'Average Free Block Drop Events (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Drops'},
            {'src_stem': 'block-manipulation',
             'col': 'int_avg_free_pickup_penalty',
             'dest_stem': 'free-pickup-penalty-int-avg',
             'title': 'Average Free Block Pickup Penalty (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Timesteps'},
            {'src_stem': 'block-manipulation',
             'col': 'int_avg_free_drop_penalty',
             'dest_stem': 'free-drop-penalty-int-avg',
             'title': 'Average Free Block Drop Penalty (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Timesteps'}
        ]
        world_model = [
            {
                'src_stem': 'perception-world-model',
                'col': 'ST_EMPTY_inaccuracies',
                'dest_stem': 'world-model-empty-int',
                'title': 'Average ST_EMPTY Inaccuracies (interval)',
                'xlabel': 'Interval',
                'ylabel': '# Inaccuracies'
            },
            {
                'src_stem': 'perception-world-model',
                'col': 'ST_HAS_BLOCK_inaccuracies',
                'dest_stem': 'world-model-block-int',
                'title': 'Average ST_HAS_BLOCK Inaccuracies (interval)',
                'xlabel': 'Interval',
                'ylabel': '# Inaccuracies'
            },
            {
                'src_stem': 'perception-world-model',
                'col': 'ST_HAS_CACHE_inaccuracies',
                'dest_stem': 'world-model-cache-int',
                'title': 'Average ST_HAS_CACHE Inaccuracies (interval)',
                'xlabel': 'Interval',
                'ylabel': '# Inaccuracies'
            }
        ]

        return {'fsm-collision': collision,
                'fsm-movement': movement,
                'block_trans': block_trans,
                'block_acq': block_acq,
                'block_manip': block_manip,
                'world_model': world_model
                }

    def _depth1_targets():
        cache_acq = [
            {'src_stem': 'cache-acquisition',
             'col': 'int_avg_acquiring_goal',
             'dest_stem': 'cache-acquisition-int-avg',
             'title': 'Average Robots Acquiring Caches (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'int_avg_vectoring_to_goal',
             'dest_stem': 'cache-acquisition-vectoring-int-avg',
             'title': 'Average Robots Vectoring To Caches (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'int_avg_exploring_for_goal',
             'dest_stem': 'cache-acquisition-exploring-int-avg',
             'title': 'Average Robots Exploring For Caches (interval)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'cum_avg_acquiring_goal',
             'dest_stem': 'cache-acquisition-cum-avg',
             'title': 'Average Robots Acquiring Caches (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'cum_avg_vectoring_to_goal',
             'dest_stem': 'cache-acquisition-vectoring-cum-avg',
             'title': 'Average Robots Vectoring To Caches (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'cum_avg_exploring_for_goal',
             'dest_stem': 'cache-acquisition-exploring-cum-avg',
             'title': 'Average Robots Exploring For Caches (cumulative)',
             'xlabel': 'Interval',
             'ylabel': '# Robots'
             }
        ]
        cache_util = [
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-pickups-int-avg',
                'col': 'int_avg_pickups',
                'title': "Average # Pickups Across All Caches (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-drops-int-avg',
                'col': 'int_avg_drops',
                'title': "Average # Drops Across All Caches (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-int',
                'col': ['int_unique_caches'],
                'title': "# Caches in Arena (Interval)",
                'legend': ['# Caches'],
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
        ]
        cache_lifecycle = [
            {
                'src_stem': 'cache-lifecycle',
                'dest_stem': 'cache-lifecyle-created-int',
                'col': 'int_created',
                'title': "# Caches Created (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-lifecycle',
                'dest_stem': 'cache-lifecyle-depleted-int',
                'col': 'int_depleted',
                'title': "# Caches  (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
        ]
        task_exec = [
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Collector Execution Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Collector Execution Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Collector Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Collector Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-abort-count-int',
                'col': 'int_abort_count',
                'title': "Collector Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-complete-count-cum-avg',
                'col': 'cum_avg_complete_count',
                'title': "Average Collector Completion Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Harvester Execution Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Harvester Execution Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Harvester Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Harvester Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-abort-count-int',
                'col': 'int_abort_count',
                'title': "Harvester Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-complete-count-cum-avg',
                'col': 'cum_avg_complete_count',
                'title': "Average Harvester Completion Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Generalist Execution Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Generalist Execution Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Generalist Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Generalist Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-abort-count-int',
                'col': 'int_abort_count',
                'title': "Generalist Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-complete-count-cum-avg',
                'col': 'cum_avg_complete_count',
                'title': "Average Generalist Completion Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            }
        ]
        generalist_tab = [
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask1-counts-int',
                'col': 'int_subtask1_count',
                'title': "Generalist TAB Subtask1 Selection Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask2-counts-int',
                'col': 'int_subtask2_count',
                'title': "Generalist TAB Subtask2 Selection Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask1-counts-cum',
                'col': 'cum_avg_subtask1_count',
                'title': "Generalist TAB Subtask1 Selection Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask2-counts-cum',
                'col': 'cum_avg_subtask2_count',
                'title': "Generalist TAB Subtask2 Selection Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-counts-int',
                'col': 'int_partition_count',
                'title': "Generalist TAB Partition Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-nopartition-counts-int',
                'col': 'int_no_partition_count',
                'title': "Generalist TAB Nopartition Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-counts-cum',
                'col': 'cum_avg_partition_count',
                'title': "Generalist TAB Partition Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-nopartition-counts-cum',
                'col': 'cum_avg_no_partition_count',
                'title': "Generalist TAB Nopartition Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-sw-counts-int',
                'col': 'int_task_sw_count',
                'title': "Generalist TAB Task Switch Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-sw-counts-cum',
                'col': 'cum_task_sw_count',
                'title': "Generalist TAB Task Switch Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
        ]
        return {'cache_acq': cache_acq,
                'cache_util': cache_util,
                'cache_lifecycle': cache_lifecycle,
                'task_exec': task_exec,
                'generalist_tab': generalist_tab}

    def targets():
        """
        Get a list of dictionaries specifying all the graphs that should be created within a batched
        experiment (i.e. across experiments).
        """

        d = Linegraphs._depth0_targets()
        d.update(Linegraphs._depth1_targets())
        return d
