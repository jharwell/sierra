# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Stage 1 of the experimental pipeline: generating experimental inputs."""

# Core packges
import logging
import time
import datetime

# 3rd party packages

# Project packages
from sierra.core.generators.experiment import BatchExpDefGenerator, BatchExpCreator
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, batchroot


class PipelineStage1:
    """Generates a :term:`Batch Experiment` for running during stage 2.

    Generated experimental input files are written to the filesystem, and can be
    be used in stage 2 to launch simulations/real robot controller. This stage
    is idempotent with default settings; this can be overridden with
    ``--no-preserve-seeds``, in which case this stage is no longer idempotent.

    """

    def __init__(
        self,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
        controller: str,
        criteria: bc.XVarBatchCriteria,
    ) -> None:
        self.generator = BatchExpDefGenerator(
            controller_name=controller,
            scenario_basename=cmdopts["scenario"],
            criteria=criteria,
            pathset=pathset,
            cmdopts=cmdopts,
        )

        self.creator = BatchExpCreator(
            criteria=criteria, cmdopts=cmdopts, pathset=pathset
        )
        self.pathset = pathset

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
           Criteria` related (e.g., :term:`Engine` changes). These changes
           apply to all experiment runs in an experiment, but may differ across
           experimental runs (e.g., # cores used for a simulator engine).

        #. Generate per-experimental run changes for each experimental run in
           the experiment, according to engine and :term:`Project`
           configuration.

        #. Write the input files for all experimental runs in all experiments to
           the filesystem after generation.

        """

        self.logger.info("Generating batch experiment in %s...", self.pathset.root)

        start = time.time()
        self.creator.create(self.generator)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        n_exp_in_batch = len(self.criteria.gen_attr_changelist()) + len(
            self.criteria.gen_element_addlist()
        )
        self.logger.info(
            "Generation complete in %s: %d experiments, %d runs per experiment, %d runs total",
            str(sec),
            n_exp_in_batch,
            int(self.cmdopts["n_runs"]),
            int(self.cmdopts["n_runs"]) * n_exp_in_batch,
        )


__all__ = ["PipelineStage1"]
