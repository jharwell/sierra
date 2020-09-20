# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""
Container module for the 5 pipeline stages implemented by SIERRA:

#. Generate a set of XML configuration files from a template suitable for
   input into ARGoS that contain user-specified modifications.
#. Run the specified  # of experiments in parallel using GNU Parallel on
   the provided set of hosts on MSI (or on a single personal computer for testing).
#. Average the .csv results of the simulation runs together.
#. Generate a user-defined set of graphs based on the averaged results for each
   experiment, and possibly across experiments for batches.
#. Compare controllers that have been tested with the same experiment batch across different
   performance measures.
"""

import os
import logging
import yaml

import core.variables.batch_criteria as bc

from core.pipeline.stage1.pipeline_stage1 import PipelineStage1
from core.pipeline.stage2.pipeline_stage2 import PipelineStage2
from core.pipeline.stage3.pipeline_stage3 import PipelineStage3
from core.pipeline.stage4.pipeline_stage4 import PipelineStage4
from core.pipeline.stage5.pipeline_stage5 import PipelineStage5


class Pipeline:
    "Implements SIERRA's 5 stage pipeline."

    def __init__(self, args, controller, scenario, cmdopts) -> None:
        self.args = args
        self.cmdopts = {
            # general
            'sierra_root': self.args.sierra_root,
            'scenario': self.args.scenario,
            'template_input_file': self.args.template_input_file,
            'project': self.args.project,
            'hpc_env': args.hpc_env,
            'argos_rendering': self.args.argos_rendering,
            "n_sims": args.n_sims,
            "n_threads": args.n_threads,
            'n_blocks': args.n_blocks,
            'n_robots': args.n_robots,
            'project_imagizing': self.args.project_imagizing,
            'exp_overwrite': self.args.exp_overwrite,

            # stage 1
            'time_setup': self.args.time_setup,
            'physics_n_engines': self.args.physics_n_engines,
            "physics_engine_type2D": self.args.physics_engine_type2D,
            "physics_engine_type3D": self.args.physics_engine_type3D,
            "physics_iter_per_tick": self.args.physics_iter_per_tick,
            "with_robot_rab": self.args.with_robot_rab,
            "with_robot_leds": self.args.with_robot_leds,
            "with_robot_battery": self.args.with_robot_battery,

            # stage 2
            'exec_exp_range': self.args.exec_exp_range,
            'exec_resume': self.args.exec_resume,
            'n_jobs_per_node': self.args.n_jobs_per_node,

            # stage 3
            'no_verify_results': self.args.no_verify_results,
            'gen_stddev': self.args.gen_stddev,
            'render_cmd_opts': self.args.render_cmd_opts,

            # stage 4
            'envc_cs_method': self.args.envc_cs_method,
            'gen_vc_plots': self.args.gen_vc_plots,
            'reactivity_cs_method': self.args.reactivity_cs_method,
            'adaptability_cs_method': self.args.adaptability_cs_method,
            'rperf_cs_method': self.args.rperf_cs_method,
            'exp_graphs': self.args.exp_graphs,
            'project_rendering': self.args.project_rendering,
            'plot_log_xaxis': self.args.plot_log_xaxis,
            'plot_regression_lines': self.args.plot_regression_lines,
            'plot_primary_axis': self.args.plot_primary_axis,
            'pm_scalability_normalize': self.args.pm_scalability_normalize,
            'pm_scalability_from_exp0': self.args.pm_scalability_from_exp0,
            'pm_self_org_normalize': self.args.pm_self_org_normalize,
            'pm_flexibility_normalize': self.args.pm_flexibility_normalize,
            'pm_robustness_normalize': self.args.pm_robustness_normalize,
            'pm_normalize_method': self.args.pm_normalize_method,

            # stage 5
            'controllers_list': self.args.controllers_list,
            'controllers_legend': self.args.controllers_legend,
            'comparison_type': self.args.comparison_type,
            'transpose_graphs': self.args.transpose_graphs,
        }

        if self.args.pm_all_normalize:
            cmdopts['pm_scalability_normalize'] = True
            cmdopts['pm_self_org_normalize'] = True
            cmdopts['pm_flexibility_normalize'] = True
            cmdopts['pm_robustness_normalize'] = True

        if cmdopts is not None:
            self.cmdopts.update(cmdopts)
            module = __import__("plugins.{0}.cmdline".format(self.cmdopts['project']),
                                fromlist=["*"])
            logging.debug("Updating cmdopts for cmdline extensions from project '%s'",
                          self.cmdopts['project'])
            module.Cmdline.cmdopts_update(self.args, self.cmdopts)

        self.cmdopts['core_config_root'] = os.path.join('core', 'config')
        self.cmdopts['project_config_root'] = os.path.join('plugins',
                                                           self.cmdopts['project'],
                                                           'config')

        try:
            self.main_config = yaml.load(open(os.path.join(self.cmdopts['project_config_root'],
                                                           'main.yaml')),
                                         yaml.FullLoader)
        except FileNotFoundError:
            logging.exception("%s/main.yaml must exist!", self.cmdopts['project_config_root'])
            raise

        if 5 not in self.args.pipeline:
            self.batch_criteria = bc.factory(self.main_config, self.cmdopts, self.args)

        self.controller = controller
        self.scenario = scenario

    def run(self):
        """
        Run pipeline stages as configured.
        """
        if 1 in self.args.pipeline:
            PipelineStage1(self.controller,
                           self.scenario,
                           self.batch_criteria,
                           self.cmdopts).run()

        if 2 in self.args.pipeline:
            PipelineStage2().run(self.cmdopts, self.batch_criteria)

        if 3 in self.args.pipeline:
            PipelineStage3().run(self.main_config, self.cmdopts)

        if 4 in self.args.pipeline:
            PipelineStage4(self.main_config, self.cmdopts).run(self.batch_criteria)

        # not part of default pipeline
        if 5 in self.args.pipeline:
            PipelineStage5(self.main_config, self.cmdopts).run(self.args)


__api__ = [
    'Pipeline'
]
