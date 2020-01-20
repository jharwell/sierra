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

from core.variables import batch_criteria as bc
from core.pipeline.stage2.exp_runner import BatchedExpRunner


class PipelineStage2:
    """
    Implements stage 2 of the experimental pipeline.

    Runs all experiments in the generation root in parallel using GNU Parallel on
    the provided set of hosts in an HPC environment, or on the local machine. This stage is *NOT*
    idempotent, for obvious reasons.
    """

    def run(self, cmdopts: tp.Dict[str, str], batch_criteria: bc.BatchCriteria):
        if cmdopts['with_rendering']:
            logging.info('Stage2: Frame grabbing enabled')

        BatchedExpRunner(cmdopts, batch_criteria)()
