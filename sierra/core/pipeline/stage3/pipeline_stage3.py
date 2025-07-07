# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Stage 3 of the experimental pipeline: processing experimental results."""

# Core packages
import time
import datetime
import logging

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, batchroot
import sierra.core.plugin as pm


class PipelineStage3:
    """Processes the results of running a :term:`Batch Experiment`.

    Currently this includes:

        - Generating statistics from results for generating per-experiment
          graphs during stage 4.  This can generate :term:`Processed Output
          Data` files, among other statistics.

        - Collating results across experiments for generating inter-experiment
          graphs during stage 4.

        - Generating image files from project metric collection for later use in
          video rendering in stage 4.

    This stage is idempotent.
    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.pathset = pathset

    def run(self, criteria: bc.XVarBatchCriteria) -> None:
        spec = self.cmdopts["proc"]
        self.logger.info(
            "Processing data with %s processing plugins: %s", len(spec), spec
        )
        for s in spec:
            module = pm.pipeline.get_plugin_module(s)
            self.logger.info(
                "Running %s in <batchroot>/%s",
                s,
                self.pathset.output_root.relative_to(self.pathset.root),
            )

            start = time.time()
            module.proc_batch_exp(
                self.main_config, self.cmdopts, self.pathset, criteria
            )
            elapsed = int(time.time() - start)
            sec = datetime.timedelta(seconds=elapsed)
            self.logger.info("Processing with %s complete in %s", s, str(sec))


__all__ = ["PipelineStage3"]
