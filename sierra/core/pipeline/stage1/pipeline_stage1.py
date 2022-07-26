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

"""Stage 1 of the experimental pipeline: generating experimental inputs.

"""

# Core packges
import logging

# 3rd party packages

# Project packages
from sierra.core.generators.exp_generators import BatchExpDefGenerator
from sierra.core.generators.exp_creator import BatchExpCreator
import sierra.core.variables.batch_criteria as bc
from sierra.core import types


class PipelineStage1:
    """Generates a :term:`Batch Experiment` for running during stage 2.

    Generated experimental input files are written to the filesystem, and can be
    be used in stage 2 to launch simulations/real robot controller. This stage
    is idempotent with default settings; this can be overridden with
    ``--no-preserve-seeds``, in which case this stage is no longer idempotent.

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
        """Create the :term:`Batch Experiment` in the filesystem.

        The creation process can be summarized as:

        #. Scaffold the batch experiment by applying sets of changes from the
           batch criteria to the XML template input file for each experiment in
           the batch. These changes apply to all :term:`Experiments
           <Experiment>` in the batch and all :term:`Experimental Runs
           <Experimental Run>` in the experiment.

        #. Generate changes to be applied to to the newly written per-experiment
           "template" XML file for each experiment which are non-:term:`Batch
           Criteria` related (e.g., :term:`Platform` changes). These changes
           apply to all experiment runs in an experiment, but may differ across
           experimental runs (e.g., # cores used for a simulator platform).

        #. Generate per-experimental run changes for each experimental run in
           the experiment, according to platform and :term:`Project`
           configuration.

        #. Write the input files for all experimental runs in all experiments to
           the filesystem after generation.

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
