# Copyright 2018 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT

"""Stage 4 of the experimental pipeline: generating products."""

# Core packages
import time
import datetime
import logging
import pathlib

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc

import sierra.core.plugin as pm
from sierra.core import types, batchroot


class PipelineStage4:
    """Generates end-result experimental products.

    Delvirables can be within a single experiment (intra-experiment) and across
    experiments in a batch (inter-experiment).  Currently this includes:

    - Graph generation controlled via YAML config files.

    - Video rendering controlled via YAML config files.

    This stage is idempotent.

    Attributes:
        cmdopts: Dictionary of parsed cmdline options.

        controller_config: YAML configuration file found in
                           ``<project_config_root>/controllers.yaml``. Contains
                           configuration for what categories of graphs should be
                           generated for what controllers, for all categories of
                           graphs in both inter- and intra-experiment graph
                           generation.

        graphs_config: YAML configuration file found in
                         ``<project_config_root>/graphs.yaml``
                         Contains configuration for categories of graphs
                         that *can* potentially be generated for all controllers
                         *across* experiments in a batch and *within* each
                         experiment in a batch. Which linegraphs are
                         *actually* generated for a given controller is
                         controlled by
                         ``<project_config_root>/controllers.yaml``.
    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
    ) -> None:
        self.main_config = main_config
        self.cmdopts = cmdopts
        self.pathset = pathset

        self.project_config_root = pathlib.Path(self.cmdopts["project_config_root"])

        self.logger = logging.getLogger(__name__)

        # Load YAML config

    def run(self, criteria: bc.XVarBatchCriteria) -> None:
        """Run the pipeline stage."""
        spec = self.cmdopts["prod"]
        self.logger.info("Generating products %s product plugins: %s", len(spec), spec)

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
            self.logger.info("Generation with %s complete in %s", s, str(sec))


__all__ = ["PipelineStage4"]
