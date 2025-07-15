# Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""The 5 pipeline stages implemented by SIERRA.

See :ref:`usage/pipeline` for high-level documentation.

"""

# Core packages
import typing as tp
import logging
import argparse
import pathlib
import os

# 3rd party packages
import yaml

# Project packages
import sierra.core.plugin as pm
from sierra.core import config, utils, batchroot

from sierra.core.pipeline.stage1.pipeline_stage1 import PipelineStage1
from sierra.core.pipeline.stage2.pipeline_stage2 import PipelineStage2
from sierra.core.pipeline.stage3.pipeline_stage3 import PipelineStage3
from sierra.core.pipeline.stage4.pipeline_stage4 import PipelineStage4
from sierra.core.pipeline.stage5.pipeline_stage5 import PipelineStage5


class Pipeline:
    "Implements SIERRA's 5 stage pipeline."

    def __init__(
        self,
        args: argparse.Namespace,
        controller: tp.Optional[str],
        pathset: tp.Optional[batchroot.PathSet] = None,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.pathset = pathset

        self.logger.info("Computed run-time tree:\n%s", self.pathset)

        assert all(
            stage in [1, 2, 3, 4, 5] for stage in args.pipeline
        ), f"Invalid pipeline stage in {args.pipeline}: Only 1-5 valid"

        # After running this, all shortform aliases have been converted to their
        # longform counterparts in the argparse.Namespace. The namespace passed
        # in contains arguments for the core and all plugins, so its OK to
        # handle shortforms which aren't in the SIERRA core at this point. This
        # also preserves the "longforms trump shortforms if both are passed"
        # policy because their converted shortforms are overwritten below.
        self.args = self._handle_shortforms(args)

        self.cmdopts = {
            # multistage
            "pipeline": self.args.pipeline,
            "sierra_root": os.path.expanduser(self.args.sierra_root),
            "scenario": self.args.scenario,
            "expdef_template": self.args.expdef_template,
            "project": self.args.project,
            "exec_env": args.exec_env,
            "engine_vc": self.args.engine_vc,
            "n_runs": args.n_runs,
            "exp_overwrite": self.args.exp_overwrite,
            "exp_range": self.args.exp_range,
            "dist_stats": self.args.dist_stats,
            "skip_collate": self.args.skip_collate,
            "engine": self.args.engine,
            "processing_parallelism": self.args.processing_parallelism,
            "plot_log_xscale": self.args.plot_log_xscale,
            "plot_enumerated_xscale": self.args.plot_enumerated_xscale,
            "plot_log_yscale": self.args.plot_log_yscale,
            "plot_regression_lines": self.args.plot_regression_lines,
            "plot_primary_axis": self.args.plot_primary_axis,
            "plot_large_text": self.args.plot_large_text,
            "plot_transpose_graphs": self.args.plot_transpose_graphs,
            "expdef": self.args.expdef,
            "proc": self.args.proc,
            "prod": self.args.prod,
            # stage 1
            "preserve_seeds": self.args.preserve_seeds,
            # stage 2
            "nodefile": self.args.nodefile,
            # stage 3
            "df_verify": self.args.df_verify,
            "compress_remove_after": self.args.compress_remove_after,
            "imagize_no_stats": self.args.imagize_no_stats,
            "df_homogenize": self.args.df_homogenize,
            "render_cmd_opts": self.args.render_cmd_opts,
            "processing_mem_limit": self.args.processing_mem_limit,
            "storage": self.args.storage,
            # stage 4
            "exp_graphs": self.args.exp_graphs,
            "project_no_LN": self.args.project_no_LN,
            "project_no_HM": self.args.project_no_HM,
            "project_rendering": self.args.project_rendering,
            "bc_rendering": self.args.bc_rendering,
            "models_enable": self.args.models_enable,
            # stage 5
            "controllers_list": self.args.controllers_list,
            "controllers_legend": self.args.controllers_legend,
            "scenarios_list": self.args.scenarios_list,
            "scenarios_legend": self.args.scenarios_legend,
            "scenario_comparison": self.args.scenario_comparison,
            "controller_comparison": self.args.controller_comparison,
            "comparison_type": self.args.comparison_type,
        }

        # Load additional cmdline options from engine
        self.logger.debug(
            "Updating cmdopts with extensions from %s", self.cmdopts["engine"]
        )
        module = pm.module_load_tiered("cmdline", engine=self.cmdopts["engine"])
        self.cmdopts |= module.to_cmdopts(self.args)

        if self.pathset is not None:
            # Load additional cmdline options from project. This is mandatory,
            # because all projects have to define --controller and --scenario
            # at a minimum.
            self.logger.debug(
                "Updating cmdopts with extensions from %s", self.cmdopts["project"]
            )
            path = "{0}.cmdline".format(self.cmdopts["project"])
            module = pm.module_load(path)

            self.cmdopts |= module.to_cmdopts(self.args)

        # Projects are specified as X.Y on cmdline so to get the path to the
        # project dir we combine the parent_dir (which is already a path) and
        # the name of the project (Y component).
        project = pm.pipeline.get_plugin(self.cmdopts["project"])
        path = project["parent_dir"] / "/".join(self.cmdopts["project"].split("."))
        self.cmdopts["project_root"] = str(path)
        self.cmdopts["project_config_root"] = str(path / "config")
        self.cmdopts["project_model_root"] = str(path / "models")

        self._load_config()

        if 5 not in self.args.pipeline:
            bc = pm.module_load_tiered(
                project=self.cmdopts["project"], path="variables.batch_criteria"
            )
            self.batch_criteria = bc.factory(
                self.main_config, self.cmdopts, self.pathset.input_root, self.args
            )

        self.controller = controller

    def run(self) -> None:
        """
        Run pipeline stages 1-5 as configured.
        """
        if 1 in self.args.pipeline:
            PipelineStage1(
                self.cmdopts,
                self.pathset,
                self.controller,  # type: ignore
                self.batch_criteria,
            ).run()

        if 2 in self.args.pipeline:
            PipelineStage2(self.cmdopts, self.pathset).run(self.batch_criteria)

        if 3 in self.args.pipeline:
            PipelineStage3(self.main_config, self.cmdopts, self.pathset).run(
                self.batch_criteria
            )

        if 4 in self.args.pipeline:
            PipelineStage4(self.main_config, self.cmdopts, self.pathset).run(
                self.batch_criteria
            )

        # not part of default pipeline
        if 5 in self.args.pipeline:
            PipelineStage5(self.main_config, self.cmdopts).run(self.args)

    def _handle_shortforms(self, args: argparse.Namespace) -> argparse.Namespace:
        """
        Replace all shortform arguments in with their longform counterparts.

        SIERRA always references arguments internally via longform if needed, so
        this is required.

        """

        shortform_map = {
            "p": "plot",
            "e": "exp",
            "x": "exec",
            "s": "skip",
        }

        for k in shortform_map:
            passed = getattr(args, k, None)
            if not passed:
                self.logger.trace(
                    ("No shortform args for -%s -> --%s " "passed to SIERRA"),
                    k,
                    shortform_map[k],
                )
                continue

            self.logger.trace(
                "Collected shortform args for -%s -> --%s: %s",
                k,
                shortform_map[k],
                passed,
            )

            # There are 3 ways to pass shortform arguments, assuming a shortform
            # of 'X:
            #
            # 1. -Xarg
            # 2. -Xarg=foo
            # 3. -Xarg foo
            for p in passed:
                if len(p) == 1 and "=" not in p[0]:  # boolean
                    # Boolean shortfrom flags should store False if they contain
                    # "no", as a user would expect.
                    key = "{0}_{1}".format(
                        shortform_map[k], p[0].replace("-", "_").replace("no_", "")
                    )
                    setattr(args, key, "no" not in p[0])

                elif len(p) == 1 and "=" in p[0]:
                    arg, value = p[0].split("=")
                    key = "{0}_{1}".format(shortform_map[k], arg.replace("-", "_"))
                    setattr(args, key, value)
                else:
                    key = "{0}_{1}".format(shortform_map[k], p[1:].replace("-", "_"))
                    setattr(args, key, p[1:])

        return args

    def _load_config(self) -> None:
        self.logger.debug(
            "Loading project config from '%s'", self.cmdopts["project_config_root"]
        )

        main_path = pathlib.Path(self.cmdopts["project_config_root"], config.kYAML.main)
        try:
            with utils.utf8open(main_path) as f:
                self.main_config = yaml.load(f, yaml.FullLoader)

        except FileNotFoundError:
            self.logger.fatal("%s must exist!", main_path)
            raise

        if "perf" not in self.main_config["sierra"]:
            return

        perf_path = pathlib.Path(
            self.cmdopts["project_config_root"], self.main_config["sierra"]["perf"]
        )
        try:
            perf_config = yaml.load(utils.utf8open(perf_path), yaml.FullLoader)

        except FileNotFoundError:
            self.logger.warning("%s does not exist!", perf_path)
            perf_config = {}
        self.main_config["sierra"].update(perf_config)


__all__ = ["Pipeline"]
