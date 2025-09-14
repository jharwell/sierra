# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Stage 5 of the experimental pipeline: comparing deliverables."""

# Core packages
import logging
import time
import datetime
import argparse

# 3rd party packages

# Project packages
from sierra.core import types
import sierra.core.plugin as pm


class PipelineStage5:
    """Compare generated products across controllers, scenarios, or batch criteria.

    Attributes:
        cmdopts: Dictionary of parsed cmdline parameters.

        main_config: Dictionary of parsed main YAML configuration.

        stage5_roots: Dictionary containing output directories for
                      inter-{scenario,controller,criteria}  product comparison.

    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
    ) -> None:
        self.cmdopts = cmdopts
        self.main_config = main_config

        self.logger = logging.getLogger(__name__)

    def run(self, cli_args: argparse.Namespace) -> None:
        spec = self.cmdopts["compare"]
        self.logger.info(
            "Comparing products with %s comparison plugins: %s", len(spec), spec
        )
        for s in spec:
            module = pm.pipeline.get_plugin_module(s)
            self.logger.info(
                "Running %s",
                s,
            )

            start = time.time()
            module.proc_exps(self.main_config, self.cmdopts, cli_args)
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            self.logger.info("Processing with %s complete in %s", s, str(sec))


__all__ = ["PipelineStage5"]
