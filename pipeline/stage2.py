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

from pipeline.batched_exp_runner import BatchedExpRunner


class PipelineStage2:
    """
    Implements stage 2 of the experimental pipeline:

    Runs all experiments in the generation root in parallel using GNU Parallel on
    the provided set of hosts on MSI (or on a single personal computer for testing).
    """

    def run(self, cmdopts, batch_criteria):
        if cmdopts['with_rendering']:
            print('- Stage2: Frame grabbing enabled')

        runner = BatchedExpRunner(cmdopts, batch_criteria)
        runner.run(exec_method=cmdopts['exec_method'],
                   n_threads_per_sim=cmdopts['n_threads'],
                   n_sims=cmdopts['n_sims'],
                   exec_resume=cmdopts['exec_resume'],
                   with_rendering=cmdopts['with_rendering'])
