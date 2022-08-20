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
"""The 5 pipeline stages implemented by SIERRA.

See :ref:`ln-sierra-usage-pipeline` for high-level documentation.

"""

# Core packages
import typing as tp
import logging
import argparse
import pathlib

# 3rd party packages
import yaml

# Project packages
import sierra.core.plugin_manager as pm
from sierra.core import types, config, utils

from sierra.core.pipeline.stage1.pipeline_stage1 import PipelineStage1
from sierra.core.pipeline.stage2.pipeline_stage2 import PipelineStage2
from sierra.core.pipeline.stage3.pipeline_stage3 import PipelineStage3
from sierra.core.pipeline.stage4.pipeline_stage4 import PipelineStage4
from sierra.core.pipeline.stage5.pipeline_stage5 import PipelineStage5


class Pipeline:
    "Implements SIERRA's 5 stage pipeline."

    def __init__(self,
                 args: argparse.Namespace,
                 controller: tp.Optional[str],
                 rdg_opts: types.Cmdopts) -> None:
        self.args = args
        self.logger = logging.getLogger(__name__)

        assert all(stage in [1, 2, 3, 4, 5] for stage in args.pipeline), \
            f"Invalid pipeline stage in {args.pipeline}: Only 1-5 valid"

        self.cmdopts = {
            # multistage
            'pipeline': self.args.pipeline,
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
            'skip_collate': self.args.skip_collate,
            'platform': self.args.platform,
            'processing_serial': self.args.processing_serial,

            'plot_log_xscale': self.args.plot_log_xscale,
            'plot_enumerated_xscale': self.args.plot_enumerated_xscale,
            'plot_log_yscale': self.args.plot_log_yscale,
            'plot_regression_lines': self.args.plot_regression_lines,
            'plot_primary_axis': self.args.plot_primary_axis,
            'plot_large_text': self.args.plot_large_text,
            'plot_transpose_graphs': self.args.plot_transpose_graphs,

            # stage 1
            'preserve_seeds': self.args.preserve_seeds,

            # stage 2
            'nodefile': self.args.nodefile,

            # stage 3
            'df_skip_verify': self.args.df_skip_verify,
            'df_homogenize': self.args.df_homogenize,
            'render_cmd_opts': self.args.render_cmd_opts,
            'processing_mem_limit': self.args.processing_mem_limit,
            'storage_medium': self.args.storage_medium,

            # stage 4
            'exp_graphs': self.args.exp_graphs,

            'project_no_LN': self.args.project_no_LN,
            'project_no_HM': self.args.project_no_HM,
            'project_rendering': self.args.project_rendering,
            'bc_rendering': self.args.bc_rendering,

            'models_enable': self.args.models_enable,

            # stage 5
            'controllers_list': self.args.controllers_list,
            'controllers_legend': self.args.controllers_legend,
            'scenarios_list': self.args.scenarios_list,
            'scenarios_legend': self.args.scenarios_legend,
            'scenario_comparison': self.args.scenario_comparison,
            'controller_comparison': self.args.controller_comparison,
            'comparison_type': self.args.comparison_type,
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

        project = pm.pipeline.get_plugin(self.cmdopts['project'])
        path = project['parent_dir'] / self.cmdopts['project']

        self.cmdopts['project_root'] = str(path)
        self.cmdopts['project_config_root'] = str(path / 'config')
        self.cmdopts['project_model_root'] = str(path / 'models')

        self._load_config()

        if 5 not in self.args.pipeline:
            bc = pm.module_load_tiered(project=self.cmdopts['project'],
                                       path='variables.batch_criteria')
            self.batch_criteria = bc.factory(self.main_config,
                                             self.cmdopts,
                                             self.args)

        self.controller = controller

    def run(self) -> None:
        """
        Run pipeline stages 1-5 as configured.
        """
        if 1 in self.args.pipeline:
            PipelineStage1(self.cmdopts,
                           self.controller,  # type: ignore
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

        main_path = pathlib.Path(self.cmdopts['project_config_root'],
                                 config.kYAML.main)
        try:
            with utils.utf8open(main_path) as f:
                self.main_config = yaml.load(f, yaml.FullLoader)

        except FileNotFoundError:
            self.logger.fatal("%s must exist!", main_path)
            raise

        perf_path = pathlib.Path(self.cmdopts['project_config_root'],
                                 self.main_config['sierra']['perf'])
        try:
            perf_config = yaml.load(utils.utf8open(perf_path), yaml.FullLoader)

        except FileNotFoundError:
            self.logger.warning("%s does not exist!", perf_path)
            perf_config = {}
        self.main_config['sierra'].update(perf_config)


__api__ = [
    'Pipeline'
]
