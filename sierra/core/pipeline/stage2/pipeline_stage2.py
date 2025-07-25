# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Stage 2 of the experimental pipeline: running experiments."""

# Core packages
import time
import datetime
import logging

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.pipeline.stage2.runner import BatchExpRunner
from sierra.core import types, batchroot


class PipelineStage2:
    """Runs :term:`Experiments <Experiment>` in a :term:`Batch Experiment`.

    GNUParallel is used as the execution engine, and a provided/generated set of
    hosts is used to actually execute experiments in the selected execution
    environment.

    This stage is *NOT* idempotent, for obvious reasons.

    """

    def __init__(self, cmdopts: types.Cmdopts, pathset: batchroot.PathSet) -> None:
        self.logger = logging.getLogger(__name__)
        self.cmdopts = cmdopts
        self.pathset = pathset

    def run(self, criteria: bc.XVarBatchCriteria) -> None:
        start = time.time()
        BatchExpRunner(self.cmdopts, self.pathset, criteria)()
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Execution complete in %s", str(sec))


__all__ = ["PipelineStage2"]
