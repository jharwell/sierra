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

# . Generate a set of XML configuration files from a template suitable for
   input into ARGoS that contain user-specified modifications.
# . Run the specified  # of experiments in parallel using GNU Parallel on
   the provided set of hosts on MSI (or on a single personal computer for testing).
# . Average the .csv results of the simulation runs together.
# . Generate a user-defined set of graphs based on the averaged results for each
   experiment, and possibly across experiments for batches.
# . Compare controllers that have been tested with the same experiment batch across different
   performance measures.
"""

# Core packages
import os
import logging
import argparse
import typing as tp

# 3rd party packages
import yaml

# Project packages
import sierra.core.variables.batch_criteria as bc
import sierra.core.plugin_manager as pm

from sierra.core.pipeline.stage1.pipeline_stage1 import PipelineStage1
from sierra.core.pipeline.stage2.pipeline_stage2 import PipelineStage2
from sierra.core.pipeline.stage3.pipeline_stage3 import PipelineStage3
from sierra.core.pipeline.stage4.pipeline_stage4 import PipelineStage4
from sierra.core.pipeline.stage5.pipeline_stage5 import PipelineStage5


class Pipeline:
    "Implements SIERRA's 5 stage pipeline."

    def __init__(self,
                 args: argparse.Namespace,
                 controller: str,
                 cmdopts: tp.Dict[str, tp.Any]) -> None:
        self.args = args
        self.logger = logging.getLogger(__name__)
        self.cmdopts = {
            # general
            'sierra_root': self.args.sierra_root,
            'scenario': self.args.scenario,
            'template_input_file': self.args.template_input_file,
            'project': self.args.project,
            'hpc_env': args.hpc_env,
            'argos_rendering': self.args.argos_rendering,
            "n_sims": args.n_sims,
            'n_robots': args.n_robots,
            'project_imagizing': self.args.project_imagizing,
            'exp_overwrite': self.args.exp_overwrite,
            'exp_range': self.args.exp_range,
            'dist_stats': self.args.dist_stats,
            'no_collate': self.args.no_collate,


            # stage 1
            'time_setup': self.args.time_setup,

            'physics_n_engines': self.args.physics_n_engines,
            "physics_engine_type2D": self.args.physics_engine_type2D,
            "physics_engine_type3D": self.args.physics_engine_type3D,
            "physics_iter_per_tick": self.args.physics_iter_per_tick,

            "with_robot_rab": self.args.with_robot_rab,
            "with_robot_leds": self.args.with_robot_leds,
            "with_robot_battery": self.args.with_robot_battery,

            'camera_config': self.args.camera_config,

            # stage 2
            'exec_resume': self.args.exec_resume,
            'exec_sims_per_node': self.args.exec_sims_per_node,

            # stage 3
            'no_verify_results': self.args.no_verify_results,
            'render_cmd_opts': self.args.render_cmd_opts,
            'processing_mem_limit': self.args.processing_mem_limit,
            'serial_processing': self.args.serial_processing,
            'storage_medium': self.args.storage_medium,

            # stage 4
            'envc_cs_method': self.args.envc_cs_method,
            'gen_vc_plots': self.args.gen_vc_plots,
            'reactivity_cs_method': self.args.reactivity_cs_method,
            'adaptability_cs_method': self.args.adaptability_cs_method,
            'rperf_cs_method': self.args.rperf_cs_method,
            'exp_graphs': self.args.exp_graphs,

            'project_no_yaml_LN': self.args.project_no_yaml_LN,
            'project_no_yaml_HM': self.args.project_no_yaml_HM,
            'project_rendering': self.args.project_rendering,

            'plot_log_xscale': self.args.plot_log_xscale,
            'plot_log_yscale': self.args.plot_log_yscale,
            'plot_regression_lines': self.args.plot_regression_lines,
            'plot_primary_axis': self.args.plot_primary_axis,
            'plot_large_text': self.args.plot_large_text,

            'pm_scalability_normalize': self.args.pm_scalability_normalize,
            'pm_scalability_from_exp0': self.args.pm_scalability_from_exp0,
            'pm_self_org_normalize': self.args.pm_self_org_normalize,
            'pm_flexibility_normalize': self.args.pm_flexibility_normalize,
            'pm_robustness_normalize': self.args.pm_robustness_normalize,
            'pm_normalize_method': self.args.pm_normalize_method,

            'models_disable': self.args.models_disable,

            # stage 5
            'controllers_list': self.args.controllers_list,
            'controllers_legend': self.args.controllers_legend,
            'scenarios_list': self.args.scenarios_list,
            'scenarios_legend': self.args.scenarios_legend,
            'scenario_comparison': self.args.scenario_comparison,
            'controller_comparison': self.args.controller_comparison,
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

            # Load additional cmdline options from project. This is mandatory, because all projects
            # have to defined --controller and --scenario at a minimum.
            self.logger.debug("Updating cmdopts for cmdline extensions from project '%s'",
                              self.cmdopts['project'])
            path = "projects.{0}.cmdline".format(self.cmdopts['project'])
            module = pm.module_load(path)

            module.Cmdline.cmdopts_update(self.args, self.cmdopts)

        self.cmdopts['plugin_root'] = os.path.join('sierra', 'plugins')
        self.cmdopts['core_config_root'] = os.path.join('sierra', 'core', 'config')

        env = os.environ.get('SIERRA_PROJECT_PATH')
        for root in env.split(os.pathsep):
            path = os.path.join(root, 'projects', self.cmdopts['project'])
            if os.path.exists(path):
                self.cmdopts['project_config_root'] = os.path.join(path, 'config')
                self.cmdopts['project_model_root'] = os.path.join(path, 'models')
                break

        self._load_config()

        if 5 not in self.args.pipeline:
            self.batch_criteria = bc.factory(self.main_config, self.cmdopts, self.args)

        self.controller = controller

    def run(self) -> None:
        """
        Run pipeline stages as configured.
        """
        if 1 in self.args.pipeline:
            PipelineStage1(self.controller,
                           self.batch_criteria,
                           self.cmdopts).run()

        if 2 in self.args.pipeline:
            PipelineStage2(self.cmdopts).run(self.batch_criteria)

        if 3 in self.args.pipeline:
            PipelineStage3(self.main_config,
                           self.cmdopts).run(self.batch_criteria)

        if 4 in self.args.pipeline:
            PipelineStage4(self.main_config,
                           self.cmdopts).run(self.batch_criteria)

        # not part of default pipeline
        if 5 in self.args.pipeline:
            PipelineStage5(self.main_config,
                           self.cmdopts).run(self.args)

    def _load_config(self) -> None:
        self.logger.debug("Loading project config from '%s'", self.cmdopts['project_config_root'])

        try:
            self.main_config = yaml.load(open(os.path.join(self.cmdopts['project_config_root'],
                                                           'main.yaml')),
                                         yaml.FullLoader)
        except FileNotFoundError:
            self.logger.exception("%s/main.yaml must exist!", self.cmdopts['project_config_root'])
            raise

        try:
            perf_config = yaml.load(open(os.path.join(self.cmdopts['project_config_root'],
                                                      self.main_config['perf'])),
                                    yaml.FullLoader)

        except FileNotFoundError:
            self.logger.exception("%s/%s must exist!",
                                  self.cmdopts['project_config_root'],
                                  self.main_config['perf'])
            raise

        self.main_config.update(perf_config)


__api__ = [
    'Pipeline'
]
