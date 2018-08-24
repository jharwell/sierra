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

from pipeline.intra_exp_graph_generator import IntraExpGraphGenerator
from pipeline.csv_collator import CSVCollator
from pipeline.batched_intra_exp_graph_generator import BatchedIntraExpGraphGenerator
from pipeline.inter_exp_graph_generator import InterExpGraphGenerator


class PipelineStage4:

    """

    Implements stage 4 of the experimental pipeline:

    Generate a user-defined set of graphs based on the averaged results for each
     experiment, and across experiments for batches.
    """

    def __init__(self, args):
        self.args = args

    def _depth0_inter_exp_targets(self):
        collision = [
            {
                'src_stem': 'fsm-collision',
                'col': 'int_avg_in_avoidance',
                'dest_stem': 'in-avoidance-int-avg',
                'title': 'Average Robots in Collision Avoidance (interval)',
                'xlabel': 'timestep',
                'ylabel': '# Robots',
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'cum_avg_in_avoidance',
                'dest_stem': 'in-avoidance-cum-avg',
                'title': 'Average Robots in Collision Avoidance (cumulative)',
                'xlabel': 'timestep',
                'ylabel': '# Robots'},
            {
                'src_stem': 'fsm-collision',
                'col': 'int_avg_entered_avoidance',
                'dest_stem': 'entered-avoidance-int-avg',
                'title': 'Average Robots Entering Collision Avoidance (interval)',
                'xlabel': 'timestep',
                'ylabel': '# Robots'
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'cum_avg_entered_avoidance',
                'dest_stem': 'entered-avoidance-cum-avg',
                'title': 'Average Robots Entering Collision Avoidance (cumulative)',
                'xlabel': 'timestep',
                'ylabel': '# Robots',
                'analytical_model': 'CAModelEnter'
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'int_avg_exited_avoidance',
                'dest_stem': 'exited-avoidance-int-avg',
                'title': 'Average Robots Exiting Collision Avoidance (interval)',
                'xlabel': 'timestep',
                'ylabel': '# Robots'
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'cum_avg_exited_avoidance',
                'dest_stem': 'exited-avoidance-cum-avg',
                'title': 'Average Robots Exiting Collision Avoidance (cumulative)',
                'xlabel': 'timestep',
                'ylabel': '# Robots'
            },
            {
                'src_stem': 'fsm-collision',
                'col': 'int_avg_avoidance_duration',
                'dest_stem': 'avoidance-duration-int-avg',
                'title': 'Average Collision Avoidance Duration (interval)',
                'xlabel': 'timestep',
                'ylabel': '# Robots',
                'analytical_model': 'CAModelDuration'
            },
            {'src_stem': 'fsm-collision',
             'col': 'cum_avg_avoidance_duration',
             'dest_stem': 'avoidance-duration-cum-avg',
             'title': 'Average Collision Avoidance Duration (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
        ]

        movement = [
            {
                'src_stem': 'fsm-movement',
                'col': 'int_avg_distance',
                'dest_stem': 'distance-int-avg',
                'title': 'Per-robot Distance Traveled (interval)',
                'xlabel': 'timestep',
                'ylabel': 'Distance (m)'
            },
            {
                'src_stem': 'fsm-movement',
                'col': 'cum_avg_distance',
                'dest_stem': 'distance-cum-avg',
                'title': 'Per-robot Distance Traveled (cumulative)',
                'xlabel': 'timestep',
                'ylabel': 'Distance (m)'},
            {
                'src_stem': 'fsm-movement',
                'col': 'int_avg_velocity',
                'dest_stem': 'velocity-int-avg',
                'title': 'Per-robot Velocity (interval)',
                'xlabel': 'timestep',
                'ylabel': 'Velocity (m/s)'
            },
            {
                'src_stem': 'fsm-movement',
                'col': 'cum_avg_velocity',
                'dest_stem': 'velocity-cum-avg',
                'title': 'Per-robot Velocity (cumulative)',
                'xlabel': 'timestep',
                'ylabel': 'Velocity (m/s)'}
        ]

        block_trans = [
            {
                'src_stem': 'block-transport',
                'col': 'int_collected',
                'dest_stem': 'blocks-collected-int',
                'title': 'Blocks Collected (interval)',
                'xlabel': 'timestep',
                'ylabel': '# Blocks'},
            {
                'src_stem': 'block-transport',
                'col': 'cum_collected',
                'dest_stem': 'blocks-collected-cum',
                'title': 'Blocks Collected (cumulative)',
                'xlabel': 'timestep',
                'ylabel': '# Blocks'
            },
            {'src_stem': 'block-transport',
             'col': 'int_cube_collected',
             'dest_stem': 'cube-blocks-collected-int',
             'title': 'Cube Blocks Collected (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Blocks'},
            {'src_stem': 'block-transport',
             'col': 'int_ramp_collected',
             'dest_stem': 'ramp-blocks-collected-int',
             'title': 'Ramp Blocks Collected (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Blocks'
             },
            {'src_stem': 'block-transport',
             'col': 'cum_collected',
             'dest_stem': 'blocks-collected-cum-avg',
             'title': 'Average Blocks Collected (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Blocks'
             },
            {'src_stem': 'block-transport',
             'col': 'cum_cube_collected',
             'dest_stem': 'cube-blocks-collected-cum-avg',
             'title': 'Average Cube Blocks Collected (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Blocks'},
            {'src_stem': 'block-transport',
             'col': 'cum_ramp_collected',
             'dest_stem': 'ramp-blocks-collected-cum-avg',
             'title': 'Average Ramp Blocks Collected (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Blocks'
             },
            {'src_stem': 'block-transport',
             'col': 'int_avg_transporters',
             'dest_stem': 'block-transporters-int-avg',
             'title': 'Average Block Transporters (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-transport',
             'col': 'cum_avg_transporters',
             'dest_stem': 'block-transporters-cum-avg',
             'title': 'Average Block Transporters (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-transport',
             'col': 'int_avg_transport_time',
             'dest_stem': 'blocks-transport-time-int-avg',
             'title': 'Average Block Transport Time (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Timesteps'
             },
            {'src_stem': 'block-transport',
             'col': 'cum_avg_transport_time',
             'dest_stem': 'blocks-transport-time-cum-avg',
             'title': 'Average Block Transport Time (Cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Timesteps'
             },
            {'src_stem': 'block-transport',
             'col': 'int_avg_initial_wait_time',
             'dest_stem': 'blocks-initial-wait-time-int-avg',
             'title': 'Average Block Initial Wait Time (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Timesteps'},
            {'src_stem': 'block-transport',
             'col': 'cum_avg_initial_wait_time',
             'dest_stem': 'blocks-initial-wait-time-cum-avg',
             'title': 'Average Block Initial Wait Time (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'},
        ]
        block_acq = [
            {'src_stem': 'block-acquisition',
             'col': 'int_avg_acquiring_goal',
             'dest_stem': 'block-acquisition-int-avg',
             'title': 'Average Robots Acquiring Blocks (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'int_avg_vectoring_to_goal',
             'dest_stem': 'block-acquisition-vectoring-int-avg',
             'title': 'Average Robots Vectoring To Blocks (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'int_avg_exploring_for_goal',
             'dest_stem': 'block-acquisition-exploring-int-avg',
             'title': 'Average Robots Exploring For Blocks (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'cum_avg_acquiring_goal',
             'dest_stem': 'block-acquisition-cum-avg',
             'title': 'Average Robots Acquiring Blocks (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'cum_avg_vectoring_to_goal',
             'dest_stem': 'block-acquisition-vectoring-cum-avg',
             'title': 'Average Robots Vectoring To Blocks (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'block-acquisition',
             'col': 'cum_avg_exploring_for_goal',
             'dest_stem': 'block-acquisition-exploring-cum-avg',
             'title': 'Average Robots Exploring For Blocks (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             }
        ]

        block_manip = [
            {'src_stem': 'block-manipulation',
             'col': 'int_avg_free_pickup_events',
             'dest_stem': 'free-pickup-events-int-avg',
             'title': 'Average Free Block Pickup Events (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Pickups'},
            {'src_stem': 'block-manipulation',
             'col': 'int_avg_free_drop_events',
             'dest_stem': 'free-drop-events-int-avg',
             'title': 'Average Free Block Drop Events (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Drops'},
            {'src_stem': 'block-manipulation',
             'col': 'int_avg_free_pickup_penalty',
             'dest_stem': 'free-pickup-penalty-int-avg',
             'title': 'Average Free Block Pickup Penalty (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Timesteps'},
            {'src_stem': 'block-manipulation',
             'col': 'int_avg_free_drop_penalty',
             'dest_stem': 'free-drop-penalty-int-avg',
             'title': 'Average Free Block Drop Penalty (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Timesteps'}
        ]
        world_model = [
            {'src_stem': 'perception-world-model',
             'col': 'ST_EMPTY_inaccuracies',
             'dest_stem': 'world-model-empty-int',
             'title': 'Average ST_EMPTY Inaccuracies (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Inaccuracies'},
            {'src_stem': 'perception-world-model',
             'col': 'ST_HAS_BLOCK_inaccuracies',
             'dest_stem': 'world-model-block-int',
             'title': 'Average ST_HAS_BLOCK Inaccuracies (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Inaccuracies'},
            {'src_stem': 'perception-world-model',
             'col': 'ST_HAS_CACHE_inaccuracies',
             'dest_stem': 'world-model-cache-int',
             'title': 'Average ST_HAS_CACHE Inaccuracies (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Inaccuracies'}
        ]

        return {'fsm-collision': collision,
                'fsm-movement': movement,
                'block_trans': block_trans,
                'block_acq': block_acq,
                'block_manip': block_manip,
                'world_model': world_model
                }

    def _depth1_inter_exp_targets(self):
        cache_acq = [
            {'src_stem': 'cache-acquisition',
             'col': 'int_avg_acquiring_goal',
             'dest_stem': 'cache-acquisition-int-avg',
             'title': 'Average Robots Acquiring Caches (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'int_avg_vectoring_to_goal',
             'dest_stem': 'cache-acquisition-vectoring-int-avg',
             'title': 'Average Robots Vectoring To Caches (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'int_avg_exploring_for_goal',
             'dest_stem': 'cache-acquisition-exploring-int-avg',
             'title': 'Average Robots Exploring For Caches (interval)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'cum_avg_acquiring_goal',
             'dest_stem': 'cache-acquisition-cum-avg',
             'title': 'Average Robots Acquiring Caches (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'cum_avg_vectoring_to_goal',
             'dest_stem': 'cache-acquisition-vectoring-cum-avg',
             'title': 'Average Robots Vectoring To Caches (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             },
            {'src_stem': 'cache-acquisition',
             'col': 'cum_avg_exploring_for_goal',
             'dest_stem': 'cache-acquisition-exploring-cum-avg',
             'title': 'Average Robots Exploring For Caches (cumulative)',
             'xlabel': 'timestep',
             'ylabel': '# Robots'
             }
        ]
        cache_util = [
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-pickups-int-avg',
                'col': 'int_avg_pickups',
                'title': "Average # Pickups Across All Caches (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-drops-int-avg',
                'col': 'int_avg_drops',
                'title': "Average # Drops Across All Caches (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-utilization',
                'dest_stem': 'cache-utilization-int',
                'col': ['int_unique_caches'],
                'title': "# Caches in Arena (Interval)",
                'legend': ['# Caches'],
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]
        cache_lifecycle = [
            {
                'src_stem': 'cache-lifecycle',
                'dest_stem': 'cache-lifecyle-created-int',
                'col': 'int_created',
                'title': "# Caches Created (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'cache-lifecycle',
                'dest_stem': 'cache-lifecyle-depleted-int',
                'col': 'int_depleted',
                'title': "# Caches  (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]
        task_exec = [
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Collector Execution Times (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Collector Execution Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Collector Interface Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Collector Interface Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-abort-count-int',
                'col': 'int_abort_count',
                'title': "Collector Abort Counts (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-collector',
                'dest_stem': 'task-execution-collector-complete-count-cum-avg',
                'col': 'cum_avg_complete_count',
                'title': "Average Collector Completion Counts (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Harvester Execution Times (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Harvester Execution Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Harvester Interface Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Harvester Interface Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-abort-count-int',
                'col': 'int_abort_count',
                'title': "Harvester Abort Counts (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-harvester',
                'dest_stem': 'task-execution-harvester-complete-count-cum-avg',
                'col': 'cum_avg_complete_count',
                'title': "Average Harvester Completion Counts (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-exec-time-int-avg',
                'col': 'int_avg_exec_time',
                'title': "Average Generalist Execution Times (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-exec-time-cum-avg',
                'col': 'cum_avg_exec_time',
                'title': "Average Generalist Execution Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Generalist Interface Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-interface-time-cum-avg',
                'col': 'cum_avg_interface_time',
                'title': "Average Generalist Interface Times (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Time'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-abort-count-int',
                'col': 'int_abort_count',
                'title': "Generalist Abort Counts (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-execution-generalist',
                'dest_stem': 'task-execution-generalist-complete-count-cum-avg',
                'col': 'cum_avg_complete_count',
                'title': "Average Generalist Completion Counts (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            }
        ]
        generalist_tab = [
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask1-counts-int',
                'col': 'int_subtask1_count',
                'title': "Generalist TAB Subtask1 Selection Counts (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask2-counts-int',
                'col': 'int_subtask2_count',
                'title': "Generalist TAB Subtask2 Selection Counts (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask1-counts-cum',
                'col': 'cum_avg_subtask1_count',
                'title': "Generalist TAB Subtask1 Selection Counts (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-subtask2-counts-cum',
                'col': 'cum_avg_subtask2_count',
                'title': "Generalist TAB Subtask2 Selection Counts (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-counts-int',
                'col': 'int_partition_count',
                'title': "Generalist TAB Partition Counts (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-nopartition-counts-int',
                'col': 'int_no_partition_count',
                'title': "Generalist TAB Nopartition Counts (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-partition-counts-cum',
                'col': 'cum_avg_partition_count',
                'title': "Generalist TAB Partition Counts (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-nopartition-counts-cum',
                'col': 'cum_avg_no_partition_count',
                'title': "Generalist TAB Nopartition Counts (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-sw-counts-int',
                'col': 'int_task_sw_count',
                'title': "Generalist TAB Task Switch Counts (Interval)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
            {
                'src_stem': 'task-generalist-tab',
                'dest_stem': 'task-generalist-tab-sw-counts-cum',
                'col': 'cum_task_sw_count',
                'title': "Generalist TAB Task Switch Counts (Cumulative)",
                'xlabel': 'timestep',
                'ylabel': 'Count'
            },
        ]
        return {'cache_acq': cache_acq,
                'cache_util': cache_util,
                'cache_lifecycle': cache_lifecycle,
                'task_exec': task_exec,
                'generalist_tab': generalist_tab}

    def _inter_exp_targets(self):
        """
        Get a list of dictionaries specifying all the graphs that should be created within a batched
        experiment (i.e. across experiments).
        """

        d = self._depth0_inter_exp_targets()
        d.update(self._depth1_inter_exp_targets())
        return d

    def _depth0_intra_exp_targets(self):
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

    def _depth1_intra_exp_targets(self):
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

    def _intra_exp_targets(self):
        """
        Get a list of dictionaries specifying all the graphs that should be created within an
        experiment (i.e. across simulation runs).
        """
        d = self._depth0_intra_exp_targets()
        d.update(self._depth1_intra_exp_targets())
        return d

    def run(self):
        inter_targets = self._inter_exp_targets()
        intra_targets = self._intra_exp_targets()
        if self.args.batch_criteria is not None:
            CSVCollator(self.args.output_root, inter_targets)()
            intra_exp = BatchedIntraExpGraphGenerator(self.args.output_root,
                                                      self.args.graph_root,
                                                      intra_targets)
        else:

            intra_exp = IntraExpGraphGenerator(self.args.output_root,
                                               self.args.graph_root,
                                               intra_targets)
        print("- Generating intra-experiment graphs...")
        intra_exp()
        print("- Intra-experiment graph generation complete")

        if self.args.batch_criteria is not None:
            print("- Generating inter-experiment graphs...")
            InterExpGraphGenerator(self.args.output_root,
                                   self.args.graph_root,
                                   self.args.generation_root, inter_targets)()
            print("- Inter-experiment graph generation complete")
