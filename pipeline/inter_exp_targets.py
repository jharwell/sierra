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
    @staticmethod
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

        convergence = [
            {
                'src_stem': 'swarm-convergence',
                'col': 'int_avg_interact_deg_raw',
                'dest_stem': 'swarm-convergence-int-deg-raw',
                'title': "Swarm Convergence: Interaction Degree (Raw)",
                'xlabel': 'Interval',
                'ylabel': 'Degree'
            },
            {
                'src_stem': 'swarm-convergence',
                'col': 'int_avg_interact_deg_raw_dt',
                'dest_stem': 'swarm-convergence-int-deg-raw-dt',
                'title': "Swarm Convergence: Interaction Degree DT (Raw)",
                'xlabel': 'Interval',
                'ylabel': 'Degree'
            },
            {
                'src_stem': 'swarm-convergence',
                'col': 'int_avg_interact_deg_norm',
                'dest_stem': 'swarm-convergence-int-deg-norm',
                'title': "Swarm Convergence: Interaction Degree (Normalized)",
                'xlabel': 'Interval',
                'ylabel': 'Degree'
            },
            {
                'src_stem': 'swarm-convergence',
                'col': 'int_avg_interact_deg_norm_dt',
                'dest_stem': 'swarm-convergence-int-deg-norm-dt',
                'title': "Swarm Convergence: Interaction Degree DT (Normalized)",
                'xlabel': 'Interval',
                'ylabel': 'Degree'
            },
            {
                'src_stem': 'swarm-convergence',
                'col': 'int_avg_ang_order',
                'dest_stem': 'swarm-convergence-ang-order',
                'title': "Swarm Convergence: Angular Order",
                'xlabel': 'Interval',
                'ylabel': 'Order'
            },
            {
                'src_stem': 'swarm-convergence',
                'col': 'int_avg_ang_order_dt',
                'dest_stem': 'swarm-convergence-ang-order-dt',
                'title': "Swarm Convergence: Angular Order DT",
                'xlabel': 'Interval',
                'ylabel': 'Order'
            },
            {
                'src_stem': 'swarm-convergence',
                'col': 'int_avg_pos_entropy',
                'dest_stem': 'swarm-convergence-pos-entropy',
                'title': "Swarm Convergence: Positional Entropy",
                'xlabel': 'Interval',
                'ylabel': 'Entropy'
            },
            {
                'src_stem': 'swarm-convergence',
                'col': 'int_avg_pos_entropy_dt',
                'dest_stem': 'swarm-convergence-pos-entropy-dt',
                'title': "Swarm Convergence: Positional Entropy DT",
                'xlabel': 'Interval',
                'ylabel': 'Entropy'
            },
        ]
        return {'fsm_collision': collision,
                'fsm_movement': movement,
                'block_trans': block_trans,
                'block_acq': block_acq,
                'block_manip': block_manip,
                'world_model': world_model,
                'convergence': convergence
                }

    @staticmethod
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
                'dest_stem': 'cache-utilization-pickups-cum-avg',
                'col': 'cum_avg_pickups',
                'title': "Average # Pickups Across All Caches (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-drops-cum-avg',
                'col': 'cum_avg_drops',
                'title': "Average # Drops Across All Caches (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-cache-counts-int',
                'col': 'int_unique_caches',
                'title': "# Caches in Arena (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-cache-counts-cum',
                'col': 'cum_unique_caches',
                'title': "# Caches in Arena (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-block-counts-int-avg',
                'col': 'int_avg_blocks',
                'title': "Average # Block All Caches (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-block-counts-cum-avg',
                'col': 'cum_avg_blocks',
                'title': "Average # Block All Caches (Cumulative)",
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
                'title': "# Caches Depleted (Interval)",
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
                'dest_stem': 'task-execution-collector-exec-est-int',
                'col': 'int_avg_exec_estimate',
                'title': "Collector Execution Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-exec-est-cum',
                'col': 'int_avg_exec_estimate',
                'title': "Collector Execution Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },

            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-interface-time-int-avg',
                'col': 'int_avg_interface_time',
                'title': "Average Collector Interface Times (Interval)",
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
                'dest_stem': 'task-execution-collector-interface-est-int',
                'col': 'int_avg_interface_estimate',
                'title': "Collector Interface Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-interface-est-cum',
                'col': 'int_avg_interface_estimate',
                'title': "Collector Interface Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-abort-count-int',
                'col': 'int_avg_abort_count',
                'title': "Average Collector Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-abort-count-cum',
                'col': 'cum_avg_abort_count',
                'title': "Average Collector Abort Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-complete-count-int',
                'col': 'int_avg_complete_count',
                'title': "Average Collector Completion Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-complete-count-cum',
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
                'dest_stem': 'task-execution-harvester-exec-est-int',
                'col': 'int_avg_exec_estimate',
                'title': "Harvester Execution Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-exec-est-cum',
                'col': 'int_avg_exec_estimate',
                'title': "Harvester Execution Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-interface-time-int-avg',
                'col': 'int_avg_interface_time',
                'title': "Average Harvester Interface Times (Interval)",
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
                'dest_stem': 'task-execution-harvester-interface-est-int',
                'col': 'int_avg_interface_estimate',
                'title': "Harvester Interface Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-interface-est-cum',
                'col': 'cum_avg_interface_estimate',
                'title': "Harvester Interface Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-abort-count-int',
                'col': 'int_avg_abort_count',
                'title': "Average Harvester Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-abort-count-cum',
                'col': 'cum_avg_abort_count',
                'title': "Average Harvester Abort Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-complete-count-int',
                'col': 'int_avg_complete_count',
                'title': "Average Harvester Completion Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-complete-count-cum',
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
                'dest_stem': 'task-execution-generalist-exec-est-int',
                'col': 'int_avg_exec_estimate',
                'title': "Generalist Execution Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-exec-est-cum',
                'col': 'int_avg_exec_estimate',
                'title': "Generalist Execution Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-abort-count-int',
                'col': 'int_avg_abort_count',
                'title': "Average Generalist Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-abort-count-cum',
                'col': 'cum_avg_abort_count',
                'title': "Average Generalist Abort Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-complete-count-int',
                'col': 'int_avg_complete_count',
                'title': "Average Generalist Completion Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-complete-count-cum',
                'col': 'cum_avg_complete_count',
                'title': "Average Generalist Completion Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            }
        ]
        generalist_tab = [
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask1-counts-int-avg',
                'col': 'int_avg_subtask1_count',
                'title': "Generalist TAB Average Harvester Selection Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask1-counts-cum-avg',
                'col': 'cum_avg_subtask1_count',
                'title': "Generalist TAB Average Harvester Selection Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask2-counts-int-avg',
                'col': 'int_avg_subtask2_count',
                'title': "Generalist TAB Average Collector Selection Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask2-counts-cum-avg',
                'col': 'cum_avg_subtask2_count',
                'title': "Generalist TAB Average Collector Selection Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-counts-int-avg',
                'col': 'int_avg_partition_count',
                'title': "Generalist TAB Average Partition Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-nopartition-counts-int-avg',
                'col': 'int_avg_no_partition_count',
                'title': "Generalist TAB Average no partition Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-counts-cum-avg',
                'col': 'cum_avg_partition_count',
                'title': "Generalist TAB Average Partition Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-nopartition-counts-cum-avg',
                'col': 'cum_avg_no_partition_count',
                'title': "Generalist TAB Average No Partition Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-task-sw-counts-int-avg',
                'col': 'int_avg_task_sw_count',
                'title': "Generalist TAB Average Task Switch Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-task-sw-counts-cum-avg',
                'col': 'cum_avg_task_sw_count',
                'title': "Generalist TAB Average Task Switch Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-task-depth-sw-counts-int-avg',
                'col': 'int_avg_task_depth_sw_count',
                'title': "Generalist TAB Average Task Depth Switch Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-task-depth-sw-counts-cum-avg',
                'col': 'cum_avg_task_depth_sw_count',
                'title': "Generalist TAB Average Task Depth Switch Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-prob-int-avg',
                'col': 'int_avg_partition_prob',
                'title': "Generalist TAB Average Partition Probability (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-prob-cum-avg',
                'col': 'cum_avg_partition_prob',
                'title': "Generalist TAB Average Partition Probability (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask-selection-prob-int-avg',
                'col': 'int_avg_subtask_selection_prob',
                'title': "Generalist TAB Average Subtask Selection Probability (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask-selection-prob-cum-avg',
                'col': 'cum_avg_subtask_selection_prob',
                'title': "Generalist TAB Average Subtask Selection Probability (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
        ]
        task_dist = [
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-depth0-count-int',
                'col': 'int_avg_depth0_count',
                'title': "Task Distribution Depth0 Count (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-depth0-count-cum-avg',
                'col': 'cum_avg_depth0_count',
                'title': "Average Task Distribution Depth0 Count (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-depth1-count-int',
                'col': 'int_avg_depth1_count',
                'title': "Task Distribution Depth1 Count (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-depth1-count-cum-avg',
                'col': 'cum_avg_depth1_count',
                'title': "Average Task Distribution Depth1 Count (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task0-int',
                'col': 'int_avg_task0_count',
                'title': "Average Task Distribution Task0 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task0-cum-avg',
                'col': 'cum_avg_task0_count',
                'title': "Task Distribution Task0 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task1-int',
                'col': 'int_avg_task1_count',
                'title': "Average Task Distribution Task1 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task1-cum-avg',
                'col': 'cum_avg_task1_count',
                'title': "Task Distribution Task1 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task2-int',
                'col': 'int_avg_task2_count',
                'title': "Average Task Distribution Task2 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task2-cum-avg',
                'col': 'cum_avg_task2_count',
                'title': "Task Distribution Task2 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-tab0-counts-int',
                'col': 'int_avg_tab0_count',
                'title': "Task Distribution TAB0 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-tab0-counts-cum-avg',
                'col': 'cum_avg_tab0_count',
                'title': "Task Distribution TAB0 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },

        ]
        return {'cache_acq': cache_acq,
                'cache_util': cache_util,
                'cache_lifecycle': cache_lifecycle,
                'depth1_task_exec': task_exec,
                'depth1_task_dist': task_dist,
                'generalist_tab': generalist_tab}

    @staticmethod
    def _depth2_targets():
        task_exec = [
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Cache Starter Execution Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Cache Starter Execution Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-exec-est-int',
                'col': 'int_avg_exec_estimate',
                'title': "Cache Starter Execution Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-exec-est-cum',
                'col': 'int_avg_exec_estimate',
                'title': "Cache Starter Execution Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-interface-time-int-avg',
                'col': 'int_avg_interface_time',
                'title': "Average Cache Starter Interface Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Cache Starter Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-interface-est-int',
                'col': 'int_avg_interface_estimate',
                'title': "Cache Starter Interface Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-interface-est-cum',
                'col': 'int_avg_interface_estimate',
                'title': "Cache Starter Interface Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-abort-count-int',
                'col': 'int_avg_abort_count',
                'title': "Average Cache Starter Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-abort-count-cum',
                'col': 'cum_avg_abort_count',
                'title': "Average Cache Starter Abort Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-complete-count-int',
                'col': 'int_avg_complete_count',
                'title': "Average Cache Starter Completion Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-starter',
                'dest_stem': 'task-execution-cache-starter-complete-count-cum',
                'col': 'cum_avg_complete_count',
                'title': "Average Cache Starter Completion Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Cache Finisher Execution Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Cache Finisher Execution Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-exec-est-int',
                'col': 'int_avg_exec_estimate',
                'title': "Average Cache Finisher Execution Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-exec-est-cum',
                'col': 'int_avg_exec_estimate',
                'title': "Average Cache Finisher Execution Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-interface-time-int-avg',
                'col': 'int_avg_interface_time',
                'title': "Average Cache Finisher Interface Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Cache Finisher Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-interface-est-int',
                'col': 'int_avg_interface_estimate',
                'title': "Average Cache Finisher Interface Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-interface-est-cum',
                'col': 'int_avg_interface_estimate',
                'title': "Average Cache Finisher Interface Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-abort-count-int',
                'col': 'int_avg_abort_count',
                'title': "Average Cache Finisher Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-abort-count-cum',
                'col': 'cum_avg_abort_count',
                'title': "Average Cache Finisher Abort Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-complete-count-int',
                'col': 'int_avg_complete_count',
                'title': "Average Cache Finisher Completion Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-finisher',
                'dest_stem': 'task-execution-cache-finisher-complete-count-cum',
                'col': 'cum_avg_complete_count',
                'title': "Average Cache Finisher Completion Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Cache Transferer Execution Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Cache Transferer Execution Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-exec-est-int',
                'col': 'int_avg_exec_estimate',
                'title': "Average Cache Transferer Execution Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-exec-est-cum',
                'col': 'int_avg_exec_estimate',
                'title': "Average Cache Transferer Execution Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },

            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-interface-time-int-avg',
                'col': 'int_avg_interface_time',
                'title': "Average Cache Transferer Interface Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Cache Transferer Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-interface-est-int',
                'col': 'int_avg_interface_estimate',
                'title': "Average Cache Transferer Interface Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-interface-est-cum',
                'col': 'int_avg_interface_estimate',
                'title': "Average Cache Transferer Interface Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-abort-count-int',
                'col': 'int_avg_abort_count',
                'title': "Average Cache Transferer Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-abort-count-cum',
                'col': 'cum_avg_abort_count',
                'title': "Average Cache Transferer Abort Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-complete-count-int',
                'col': 'int_avg_complete_count',
                'title': "Average Cache Transferer Completion Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-transferer',
                'dest_stem': 'task-execution-cache-transferer-complete-count-cum',
                'col': 'cum_avg_complete_count',
                'title': "Average Cache Transferer Completion Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Cache Collector Execution Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Cache Collector Execution Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-exec-est-int',
                'col': 'int_avg_exec_estimate',
                'title': "Average Cache Collector Execution Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-exec-est-cum',
                'col': 'int_avg_exec_estimate',
                'title': "Average Cache Collector Execution Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-interface-time-int-avg',
                'col': 'int_avg_interface_time',
                'title': "Average Cache Collector Interface Times (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Cache Collector Interface Times (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-interface-est-int',
                'col': 'int_avg_interface_estimate',
                'title': "Average Cache Collector Interface Time Estimate (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-interface-est-cum',
                'col': 'cum_avg_interface_estimate',
                'title': "Average Cache Collector Interface Time Estimate (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-abort-count-int',
                'col': 'int_avg_abort_count',
                'title': "Average Cache Collector Abort Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-abort-count-cum',
                'col': 'cum_avg_abort_count',
                'title': "Average Cache Collector Abort Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-complete-count-int',
                'col': 'int_avg_complete_count',
                'title': "Average Cache Collector Completion Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-cache-collector',
                'dest_stem': 'task-execution-cache-collector-complete-count-cum',
                'col': 'cum_avg_complete_count',
                'title': "Average Cache Collector Completion Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
        ]

        task_dist = [
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-depth2-count-int',
                'col': 'int_avg_depth2_count',
                'title': "Task Distribution Depth2 Count (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-depth2-count-cum-avg',
                'col': 'cum_avg_depth2_count',
                'title': "Average Task Distribution Depth2 Count (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task3-int',
                'col': 'int_avg_task3_count',
                'title': "Average Task Distribution Task3 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task3-cum-avg',
                'col': 'cum_avg_task3_count',
                'title': "Task Distribution Task3 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task4-int',
                'col': 'int_avg_task4_count',
                'title': "Average Task Distribution Task4 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task4-cum-avg',
                'col': 'cum_avg_task4_count',
                'title': "Task Distribution Task4 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task5-int',
                'col': 'int_avg_task5_count',
                'title': "Average Task Distribution Task5 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task5-cum-avg',
                'col': 'cum_avg_task5_count',
                'title': "Task Distribution Task5 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task6-int',
                'col': 'int_avg_task6_count',
                'title': "Average Task Distribution Task6 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-task-counts-task6-cum-avg',
                'col': 'cum_avg_task6_count',
                'title': "Task Distribution Task 6 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-tab1-counts-int',
                'col': 'int_tab1_count',
                'title': "Task Distribution TAB1 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-tab1-counts-cum-avg',
                'col': 'cum_avg_tab1_count',
                'title': "Task Distribution TAB1 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-tab2-counts-int',
                'col': 'int_tab2_count',
                'title': "Task Distribution TAB2 Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-distribution',
                'dest_stem': 'task-distribution-tab2-counts-cum-avg',
                'col': 'cum_avg_tab2_count',
                'title': "Task Distribution TAB2 Counts (Cumulative Average)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
        ]
        harvester_tab = [
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-subtask1-counts-int',
                'col': 'int_avg_subtask1_count',
                'title': "Harvester TAB Average Cache Starter Selection Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-subtask1-counts-cum',
                'col': 'cum_avg_subtask1_count',
                'title': "Harvester TAB Average Cache Starter Selection Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-subtask2-counts-int',
                'col': 'int_avg_subtask2_count',
                'title': "Harvester TAB Average Cache Finisher Selection Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-subtask2-counts-cum',
                'col': 'cum_avg_subtask2_count',
                'title': "Harvester TAB Average Cache Finisher Selection Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-partition-counts-int',
                'col': 'int_avg_partition_count',
                'title': "Harvester TAB Average Partition Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-nopartition-counts-int',
                'col': 'int_avg_no_partition_count',
                'title': "Harvester TAB Average no partition Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-partition-counts-cum',
                'col': 'cum_avg_partition_count',
                'title': "Harvester TAB Average Partition Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-nopartition-counts-cum',
                'col': 'cum_avg_no_partition_count',
                'title': "Harvester TAB Average no partition Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-task-sw-counts-int',
                'col': 'int_avg_task_sw_count',
                'title': "Harvester TAB Average Task Switch Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-task-sw-counts-cum',
                'col': 'cum_avg_task_sw_count',
                'title': "Harvester TAB Average Task Switch Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-task-depth-sw-counts-int',
                'col': 'int_avg_task_depth_sw_count',
                'title': "Harvester TAB Average Task Depth Switch Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-task-depth-sw-counts-cum',
                'col': 'cum_avg_task_depth_sw_count',
                'title': "Harvester TAB Average Task Depth Switch Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-partition-prob-int-avg',
                'col': 'int_avg_partition_prob',
                'title': "Harvester TAB Average Partition Probability (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-partition-prob-cum-avg',
                'col': 'cum_avg_partition_prob',
                'title': "Harvester TAB Average Partition Probability (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-subtask-selection-prob-int-avg',
                'col': 'int_avg_subtask_selection_prob',
                'title': "Harvester TAB Average Subtask Selection Probability (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-harvester-tab',
                'dest_stem': 'task-harvester-tab-subtask-selection-prob-cum-avg',
                'col': 'cum_avg_subtask_selection_prob',
                'title': "Harvester TAB Average Subtask Selection Probability (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
        ]
        collector_tab = [
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-subtask1-counts-int',
                'col': 'int_avg_subtask1_count',
                'title': "Collector TAB Average Cache Transferer Selection Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-subtask1-counts-cum',
                'col': 'cum_avg_subtask1_count',
                'title': "Collector TAB Average Cache Transferer Selection Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-subtask2-counts-int',
                'col': 'int_avg_subtask2_count',
                'title': "Collector TAB Average Cache Collector Selection Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-subtask2-counts-cum',
                'col': 'cum_avg_subtask2_count',
                'title': "Collector TAB Average Cache Collector Selection Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-partition-counts-int',
                'col': 'int_avg_partition_count',
                'title': "Collector TAB Average Partition Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-nopartition-counts-int',
                'col': 'int_avg_no_partition_count',
                'title': "Collector TAB Average no partition Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-partition-counts-cum',
                'col': 'cum_avg_partition_count',
                'title': "Collector TAB Average Partition Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-nopartition-counts-cum',
                'col': 'cum_avg_no_partition_count',
                'title': "Collector TAB Average no partition Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-task-sw-counts-int',
                'col': 'int_avg_task_sw_count',
                'title': "Collector TAB Average Task Switch Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-task-sw-counts-cum',
                'col': 'cum_avg_task_sw_count',
                'title': "Collector TAB Average Task Switch Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-task-depth-sw-counts-int',
                'col': 'int_avg_task_depth_sw_count',
                'title': "Collector TAB Average Task Depth Switch Counts (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-task-depth-sw-counts-cum',
                'col': 'cum_avg_task_depth_sw_count',
                'title': "Collector TAB Average Task Depth Switch Counts (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-partition-prob-int-avg',
                'col': 'int_avg_partition_prob',
                'title': "Collector TAB Average Partition Probability (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-partition-prob-cum-avg',
                'col': 'cum_avg_partition_prob',
                'title': "Collector TAB Average Partition Probability (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-subtask-selection-prob-int-avg',
                'col': 'int_avg_subtask_selection_prob',
                'title': "Collector TAB Average Subtask Selection Probability (Interval)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
            {
                'src_stem': 'task-collector-tab',
                'dest_stem': 'task-collector-tab-subtask-selection-prob-cum-avg',
                'col': 'cum_avg_subtask_selection_prob',
                'title': "Collector TAB Average Subtask Selection Probability (Cumulative)",
                'xlabel': 'Interval',
                'ylabel': 'Value'
            },
        ]

        return {"depth2_task_dist": task_dist,
                'depth2_task_exec': task_exec,
                'harvester_tab': harvester_tab,
                'collector_tab': collector_tab}

    @staticmethod
    def targets(gen_depth2):
        """
        Get a list of dictionaries specifying all the graphs that should be created within a batched
        experiment (i.e. across experiments).
        """

        d = Linegraphs._depth0_targets()
        d.update(Linegraphs._depth1_targets())
        if gen_depth2:
            d.update(Linegraphs._depth2_targets())
        return d
