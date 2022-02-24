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
Contains main class implementing stage  of the experimental pipeline.
"""

# Core packges
import typing as tp
import logging  # type: tp.Any

# 3rd party packages

# Project packages
from sierra.core.generators.exp_generators import BatchExpDefGenerator
from sierra.core.generators.exp_creator import BatchExpCreator
import sierra.core.variables.batch_criteria as bc
from sierra.core import types


class PipelineStage1:
    """
    Implements stage 1 of the pipeline.

    Generates a set of XML configuration files from a template suitable for
    launching simulations/real robot controller that contain user-specified
    modifications. This stage is idempotent.

    """

    def __init__(self,
                 cmdopts: types.Cmdopts,
                 controller: str,
                 criteria: bc.IConcreteBatchCriteria) -> None:
        self.generator = BatchExpDefGenerator(controller_name=controller,
                                              scenario_basename=cmdopts['scenario'],
                                              criteria=criteria,
                                              cmdopts=cmdopts)
        self.creator = BatchExpCreator(criteria=criteria, cmdopts=cmdopts)

        self.cmdopts = cmdopts
        self.criteria = criteria
        self.logger = logging.getLogger(__name__)

    def run(self) -> None:
        """
        Run stage 1 of the experiment pipeline.
        """

        self.logger.info("Generating input files for batch experiment in %s...",
                         self.cmdopts['batch_root'])
        self.creator.create(self.generator)

        n_exp_in_batch = len(self.criteria.gen_attr_changelist()) + \
            len(self.criteria.gen_tag_addlist())
        self.logger.info("%d input files generated in %d experiments.",
                         self.cmdopts['n_runs'] * n_exp_in_batch,
                         n_exp_in_batch)


__api__ = [
    'PipelineStage1'
]
