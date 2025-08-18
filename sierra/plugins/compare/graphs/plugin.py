#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""
Stage5 plugin to compare graphs across {controllers, scenarios, criterias}.
"""

# Core packages
import logging
import argparse

# 3rd party packages

# Project packages
from sierra.core import types, utils
from sierra.plugins.compare.graphs import outputroot
from sierra.plugins.compare.graphs import inter_controller as intercc
from sierra.plugins.compare.graphs import inter_scenario as intersc

_logger = logging.getLogger(__name__)


def proc_exps(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    cli_args: argparse.Namespace,
    stage5_config: types.YAMLDict,
) -> None:
    stage5_roots = outputroot.PathSet(
        cmdopts,
        cmdopts["things"].split(",") if cmdopts["across"] == "controllers" else None,
        cmdopts["things"].split(",") if cmdopts["across"] == "scenarios" else None,
    )

    if stage5_roots.model_root is not None:
        utils.dir_create_checked(stage5_roots.model_root, True)

    # Create directories for .csv files and graphs
    utils.dir_create_checked(stage5_roots.graph_root, True)
    utils.dir_create_checked(stage5_roots.csv_root, True)

    assert (
        cmdopts["bc_cardinality"] <= 2
    ), "This plugin only supports batch criteria with cardinality <=2"

    if cmdopts["across"] == "controllers":
        _run_cc(main_config, cmdopts, cli_args, stage5_roots, stage5_config)
    elif cmdopts["across"] == "scenarios":
        _run_sc(main_config, cmdopts, cli_args, stage5_roots, stage5_config)
    elif cmdopts["across"] == "criterias":
        raise RuntimeError("Inter-criteria comparison not implemented yet!")


def _run_cc(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    cli_args: argparse.Namespace,
    stage5_roots: outputroot.PathSet,
    stage5_config: types.YAMLDict,
) -> None:
    controllers = cmdopts["things"].split(",")

    # Use nice controller names on graph legends if configured
    if cmdopts["things_legend"] is not None:
        legend = cmdopts["things_legend"].split(",")
    else:
        legend = controllers

    _logger.info("Inter-batch controller comparison of %s...", controllers)

    if cmdopts["bc_cardinality"] == 1:
        univar = intercc.UnivarInterControllerComparator(
            controllers,
            stage5_roots,
            cmdopts,
            cli_args,
            main_config,
        )
        univar(
            target_graphs=list(stage5_config["inter-controller"]["graphs"]),
            legend=list(legend),
        )
    elif cmdopts["bc_cardinality"] == 2:
        bivar = intercc.BivarInterControllerComparator(
            controllers,
            stage5_roots,
            cmdopts,
            cli_args,
            main_config,
        )
        bivar(
            target_graphs=list(stage5_config["inter-controller"]["graphs"]),
            legend=list(legend),
        )

    _logger.info("Inter-batch controller comparison complete")


def _run_sc(
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    cli_args: argparse.Namespace,
    stage5_roots: outputroot.PathSet,
    stage5_config: types.YAMLDict,
) -> None:
    scenarios = cmdopts["things"].split(",")

    # Use nice scenario names on graph legends if configured
    if cmdopts["things_legend"] is not None:
        legend = cmdopts["things_legend"].split(",")
    else:
        legend = scenarios

    controller = cmdopts["controller"]

    _logger.info("Inter-batch comparison of %s across %s...", controller, scenarios)

    assert (
        cmdopts["bc_cardinality"] == 1
    ), "inter-scenario controller comparison only valid for univariate batch criteria"

    comparator = intersc.UnivarInterScenarioComparator(
        controller,
        scenarios,
        stage5_roots,
        cmdopts,
        cli_args,
        main_config,
    )

    comparator(
        target_graphs=list(stage5_config["inter-scenario"]["graphs"]),
        legend=list(legend),
    )

    _logger.info(
        "Inter-batch  comparison of %s across %s complete",
        controller,
        scenarios,
    )
