# Copyright 2018 John Harwell, All rights reserved.
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

"""Stage 2 of the experimental pipeline: running experiments.

"""

# Core packages
import time
import datetime
import logging

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.pipeline.stage2.exp_runner import BatchExpRunner
from sierra.core import types


class PipelineStage2:
    """Runs :term:`Experiments <Experiment>` in a :term:`Batch Experiment`.

    GNUParallel is used as the execution engine, and a provided/generated set of
    hosts is used to actually execute experiments in the selected execution
    environment.

    This stage is *NOT* idempotent, for obvious reasons.

    """

    def __init__(self, cmdopts: types.Cmdopts) -> None:
        self.logger = logging.getLogger(__name__)
        self.cmdopts = cmdopts

    def run(self, criteria: bc.BatchCriteria) -> None:
        start = time.time()
        BatchExpRunner(self.cmdopts, criteria)()
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Execution complete in %s", str(sec))


__api__ = [
    'PipelineStage2'
]
