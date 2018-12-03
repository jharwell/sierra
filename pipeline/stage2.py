"""
 Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/
"""

from pipeline.exp_runner import ExpRunner
from pipeline.batched_exp_runner import BatchedExpRunner


class PipelineStage2:

    """
    Implements stage 2 of the experimental pipeline:

    Runs all experiments in the generation root in parallel using GNU Parallel on
    the provided set of hosts on MSI (or on a single personal computer for testing).
    """

    def __init__(self, args):
        self.args = args

    def run(self):
        if self.args.batch_criteria is not None:
            runner = BatchedExpRunner(self.args.generation_root, self.args.batch_exp_num)
        else:
            runner = ExpRunner(self.args.generation_root, False)

        runner.run(no_msi=self.args.no_msi)
