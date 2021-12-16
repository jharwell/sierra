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
Container module for the 5 pipeline stages implemented by SIERRA. See
:ref:`ln-usage-pipeline` for high-level documentation.
"""

# Core packages
import os
import typing as tp
import logging  # type: tp.Any
import argparse

# 3rd party packages
import yaml

# Project packages
import sierra.core.variables.batch_criteria as bc
import sierra.core.plugin_manager as pm
from sierra.core import types

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
                 rdg_opts: types.Cmdopts) -> None:
        self.args = args
        self.logger = logging.getLogger(__name__)

        self.cmdopts = {
            # general
            'sierra_root': self.args.sierra_root,
            'scenario': self.args.scenario,
            'template_input_file': self.args.template_input_file,
            'project': self.args.project,
            'exec_env': args.exec_env,
            'platform_vc': self.args.platform_vc,
            "n_runs": args.n_runs,
            'project_imagizing': self.args.project_imagizing,
            'exp_overwrite': self.args.exp_overwrite,
            'exp_range': self.args.exp_range,
            'dist_stats': self.args.dist_stats,
            'no_collate': self.args.no_collate,
            'platform': self.args.platform,

            # stage 1
            'no_preserve_seeds': self.args.no_preserve_seeds,

            # stage 2
            'nodefile': self.args.nodefile,

            # stage 3
            'no_verify_results': self.args.no_verify_results,
            'render_cmd_opts': self.args.render_cmd_opts,
            'processing_mem_limit': self.args.processing_mem_limit,
            'serial_processing': self.args.serial_processing,
            'storage_medium': self.args.storage_medium,

            # stage 4
            'exp_graphs': self.args.exp_graphs,

            'project_no_yaml_LN': self.args.project_no_yaml_LN,
            'project_no_yaml_HM': self.args.project_no_yaml_HM,
            'project_rendering': self.args.project_rendering,

            'plot_log_xscale': self.args.plot_log_xscale,
            'plot_enumerated_xscale': self.args.plot_enumerated_xscale,
            'plot_log_yscale': self.args.plot_log_yscale,
            'plot_regression_lines': self.args.plot_regression_lines,
            'plot_primary_axis': self.args.plot_primary_axis,
            'plot_large_text': self.args.plot_large_text,

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

        # Load additional cmdline options from platform
        self.logger.debug("Updating cmdopts with extensions from '%s'",
                          self.cmdopts['platform'])
        module = pm.module_load_tiered("cmdline",
                                       platform=self.cmdopts['platform'])
        module.PlatformCmdline.cmdopts_update(self.args, self.cmdopts)

        if rdg_opts is not None:
            self.cmdopts.update(rdg_opts)

            # Load additional cmdline options from project. This is mandatory,
            # because all projects have to define --controller and --scenario
            # at a minimum.
            self.logger.debug("Updating cmdopts with extensions from '%s'",
                              self.cmdopts['project'])
            path = "{0}.cmdline".format(self.cmdopts['project'])
            module = pm.module_load(path)

            module.Cmdline.cmdopts_update(self.args, self.cmdopts)

        self.cmdopts['plugin_root'] = os.path.join('sierra', 'plugins')

        project = pm.SIERRAPluginManager().get_plugin(self.cmdopts['project'])
        path = os.path.join(project['parent_dir'], self.cmdopts['project'])
        self.cmdopts['project_root'] = path
        self.cmdopts['project_config_root'] = os.path.join(path, 'config')
        self.cmdopts['project_model_root'] = os.path.join(path, 'models')

        self._load_config()

        if 5 not in self.args.pipeline:
            self.batch_criteria = bc.factory(self.main_config,
                                             self.cmdopts,
                                             self.args)

        self.controller = controller

    def run(self) -> None:
        """
        Run pipeline stages as configured.
        """
        if 1 in self.args.pipeline:
            PipelineStage1(self.cmdopts,
                           self.controller,
                           self.batch_criteria).run()

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
        self.logger.debug("Loading project config from '%s'",
                          self.cmdopts['project_config_root'])

        try:
            self.main_config = yaml.load(open(os.path.join(self.cmdopts['project_config_root'],
                                                           'main.yaml')),
                                         yaml.FullLoader)
        except FileNotFoundError:
            self.logger.fatal("%s/main.yaml must exist!",
                              self.cmdopts['project_config_root'])
            raise

        try:
            perf_config = yaml.load(open(os.path.join(self.cmdopts['project_config_root'],
                                                      self.main_config['sierra']['perf'])),
                                    yaml.FullLoader)

        except FileNotFoundError:
            self.logger.fatal("%s/%s must exist!",
                              self.cmdopts['project_config_root'],
                              self.main_config['sierra']['perf'])
            raise

        self.main_config['sierra'].update(perf_config)


__api__ = [
    'Pipeline'
]
