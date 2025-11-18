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
from sierra.core import config, utils, batchroot, types

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

        # The namespace passed in contains arguments for the core and all
        # plugins, so its OK to handle shortforms which aren't in the SIERRA
        # core at this point. This also preserves the "longforms trump
        # shortforms if both are passed" policy because their converted
        # shortforms are overwritten below.
        self.args = args
        shortforms = self._handle_shortforms()

        # Check for problematic characters in arguments used to create directory
        # paths.
        if any(
            "+" in arg
            for arg in [
                self.args.scenario or [],
                self.args.controller or [],
                self.args.batch_criteria,
            ]
        ):
            raise RuntimeError(
                "{--scenario, --controller, --batch-criteria} cannot contain '+'."
            )

        self.cmdopts = self._init_cmdopts(shortforms)

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
                self.controller,
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

    def _init_cmdopts(self, shortforms: types.Cmdopts) -> types.Cmdopts:
        longforms = {
            # multistage
            "pipeline": self.args.pipeline,
            "sierra_root": pathlib.Path(self.args.sierra_root).expanduser(),
            "scenario": self.args.scenario,
            "expdef_template": self.args.expdef_template,
            "project": self.args.project,
            "execenv": self.args.execenv,
            "engine_vc": self.args.engine_vc,
            "n_runs": self.args.n_runs,
            "exp_overwrite": self.args.exp_overwrite,
            "exp_range": self.args.exp_range,
            "engine": self.args.engine,
            "processing_parallelism": self.args.processing_parallelism,
            "exec_parallelism_paradigm": self.args.exec_parallelism_paradigm,
            "expdef": self.args.expdef,
            # stage 1
            "preserve_seeds": self.args.preserve_seeds,
            # stage 2
            "nodefile": self.args.nodefile,
            # stage 3
            "proc": self.args.proc,
            "df_verify": self.args.df_verify,
            "df_homogenize": self.args.df_homogenize,
            "processing_mem_limit": self.args.processing_mem_limit,
            "storage": self.args.storage,
            # stage 4
            "prod": self.args.prod,
            # stage 5
            "compare": self.args.compare,
        }
        cmdopts = longforms

        # Load additional cmdline options from --engine
        self.logger.debug("Updating cmdopts from --engine=%s", cmdopts["engine"])
        module = pm.module_load_tiered("cmdline", engine=cmdopts["engine"])
        cmdopts |= module.to_cmdopts(self.args)

        # Load additional cmdline options from --execenv
        path = "{}.cmdline".format(cmdopts["execenv"])
        if pm.module_exists(path):
            self.logger.debug("Updating cmdopts from --execenv=%s", cmdopts["execenv"])
            module = pm.module_load_tiered(path)
            cmdopts |= module.to_cmdopts(self.args)

        # Load additional cmdline options from --expdef
        path = "{}.cmdline".format(cmdopts["expdef"])
        if pm.module_exists(path):
            self.logger.debug("Updating cmdopts from --expdef=%s", cmdopts["expdef"])
            module = pm.module_load_tiered(path)
            cmdopts |= module.to_cmdopts(self.args)

        # Load additional cmdline options from --proc plugins
        for p in cmdopts["proc"]:
            path = "{}.cmdline".format(p)
            if pm.module_exists(path):
                self.logger.debug("Updating cmdopts from --proc=%s", p)
                module = pm.module_load_tiered(path)
                cmdopts |= module.to_cmdopts(self.args)

        for p in cmdopts["prod"]:
            path = "{}.cmdline".format(p)
            if pm.module_exists(path):
                self.logger.debug("Updating cmdopts from --prod=%s", p)
                module = pm.module_load_tiered(path)
                cmdopts |= module.to_cmdopts(self.args)

        for p in cmdopts["compare"]:
            path = "{}.cmdline".format(p)
            if pm.module_exists(path):
                self.logger.debug("Updating cmdopts from --compare=%s", p)
                module = pm.module_load_tiered(path)
                cmdopts |= module.to_cmdopts(self.args)

        # Load additional cmdline options from --storage
        path = "{}.cmdline".format(cmdopts["storage"])
        if pm.module_exists(path):
            self.logger.debug("Updating cmdopts from --storage=%s", cmdopts["storage"])
            module = pm.module_load_tiered(path)
            cmdopts |= module.to_cmdopts(self.args)

        # Load additional cmdline options from project. This is mandatory,
        # because all projects have to define --controller and --scenario
        # at a minimum.
        self.logger.debug("Updating cmdopts from --project=%s", cmdopts["project"])
        path = "{}.cmdline".format(cmdopts["project"])
        module = pm.module_load(path)
        cmdopts |= module.to_cmdopts(self.args)

        # This has to be AFTER loading cmdopts from all plugins so that any
        # unset/defaulted options don't override the shortform. This also means
        # that shortforms override longforms if both are passed.
        cmdopts |= shortforms

        # Projects are specified as X.Y on cmdline so to get the path to the
        # project dir we combine the parent_dir (which is already a path) and
        # the name of the project (Y component).
        project = pm.pipeline.get_plugin(cmdopts["project"])
        path = project["parent_dir"] / "/".join(cmdopts["project"].split("."))
        cmdopts["project_root"] = str(path)
        cmdopts["project_config_root"] = str(path / "config")
        cmdopts["project_model_root"] = str(path / "models")

        return cmdopts

    def _handle_shortforms(self) -> types.Cmdopts:
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
        ret = {}

        for k, v in shortform_map.items():
            passed = getattr(self.args, k, None)
            if not passed:
                self.logger.trace(
                    ("No shortform args for -%s -> --%s passed to SIERRA"), k, v
                )
                continue

            self.logger.trace(
                "Collected shortform args for -%s -> --%s: %s",
                k,
                v,
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
                    key = "{}_{}".format(v, p[0].replace("-", "_").replace("no_", ""))
                    ret[key] = "no" not in p[0]

                elif len(p) == 1 and "=" in p[0]:
                    arg, value = p[0].split("=")
                    key = "{}_{}".format(v, arg.replace("-", "_"))
                    ret[key] = value
                else:
                    key = "{}_{}".format(v, p[1:].replace("-", "_"))
                    ret[key] = p[1:]

        return ret

    def _load_config(self) -> None:
        self.logger.debug(
            "Loading project config from '%s'", self.cmdopts["project_config_root"]
        )

        main_path = pathlib.Path(
            self.cmdopts["project_config_root"], config.PROJECT_YAML.main
        )
        try:
            with utils.utf8open(main_path) as f:
                self.main_config = yaml.load(f, yaml.FullLoader)

        except FileNotFoundError:
            self.logger.fatal("%s must exist!", main_path)
            raise


__all__ = ["Pipeline"]
