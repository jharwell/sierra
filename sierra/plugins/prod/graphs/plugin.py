#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import logging
import pathlib
import time
import datetime

# 3rd party packages
import yaml

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core import types, config, utils, batchroot

from sierra.plugins.prod.graphs import inter, intra, collate

_logger = logging.getLogger(__name__)


def proc_batch_exp(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    criteria: bc.XVarBatchCriteria,
) -> None:
    """
    Generate graphs from the :term:`Batch Experiment`.

    Intra-experiment graph generation: if intra-experiment graphs should be
    generated, according to configuration, the following is run:

        #. :py:func:`~sierra.plugins.prod.graphs.intra.generate` to
           generate graphs for each experiment in the batch, or a subset.

    Inter-experiment graph generation: if inter-experiment graphs should be
    generated according to cmdline configuration, the following is run:

        #. :class:`~sierra.plugins.prod.graphs.collate.GraphCollator`.

        #. :py:func:`~sierra.plugins.prod.graphs.inter.generate` to perform
           graph generation from collated CSV files.
    """
    graphs_path = pathlib.Path(cmdopts["project_config_root"]) / pathlib.Path(
        config.PROJECT_YAML.graphs
    )
    if utils.path_exists(graphs_path):
        _logger.info("Loading graphs config for project=%s", cmdopts["project"])
        graphs_config = yaml.load(utils.utf8open(graphs_path), yaml.FullLoader)
    else:
        _logger.warning("%s does not exist--cannot generate graphs", graphs_path)
        return

    if (
        (cmdopts["exp_graphs"] == "all" or cmdopts["exp_graphs"] == "intra")
        and graphs_config is not None
        and "intra-exp" in graphs_config
    ):
        _logger.info("Generating intra-experiment graphs...")
        start = time.time()
        intra.proc_batch_exp(
            main_config,
            cmdopts,
            pathset,
            criteria,
        )
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        _logger.info("Intra-experiment graph generation complete: %s", str(sec))

    # Collation must be after intra-experiment graph generation, so that all
    # .csv files to be collated have been generated/modified according to
    # parameters.
    if (
        (cmdopts["exp_graphs"] == "all" or cmdopts["exp_graphs"] == "inter")
        and graphs_config is not None
        and "inter-exp" in graphs_config
    ):
        _logger.info("Collating inter-experiment files...")
        start = time.time()
        collate.proc_batch_exp(main_config, cmdopts, pathset, criteria)
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)
        _logger.info("Collating inter-experiment files complete: %s", str(sec))

        _logger.info("Generating inter-experiment graphs...")
        start = time.time()

        inter.generate.proc_batch_exp(
            main_config,
            cmdopts,
            pathset,
            criteria,
        )
        elapsed = int(time.time() - start)
        sec = datetime.timedelta(seconds=elapsed)

        _logger.info("Inter-experiment graph generation complete: %s", str(sec))
