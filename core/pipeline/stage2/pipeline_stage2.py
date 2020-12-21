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

"""
Contains main class implementing stage 2 of the experimental pipeline.
"""

import logging
import typing as tp
import time
import datetime

from core.variables import batch_criteria as bc
from core.pipeline.stage2.exp_runner import BatchedExpRunner


class PipelineStage2:
    """
    Implements stage 2 of the experimental pipeline.

    Runs all experiments in the input root in parallel using GNU Parallel on the provided set of
    hosts in an HPC environment, or on the local machine. This stage is *NOT* idempotent, for
    obvious reasons.

    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def run(self, cmdopts: dict, batch_criteria: bc.BatchCriteria):
        if cmdopts['argos_rendering']:
            self.logger.info('Stage2: ARGoS frame grabbing enabled')

        start = time.time()
        BatchedExpRunner(cmdopts, batch_criteria)()
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        self.logger.info("Stage2: Execution complete in %s", str(sec))


__api__ = [
    'PipelineStage2'
]
