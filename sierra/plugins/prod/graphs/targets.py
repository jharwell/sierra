#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#

# Core packages
import typing as tp
import logging

# 3rd party packages

# Project packages
from sierra.core import types

_logger = logging.getLogger(__name__)


def inter_exp_calc(
    loaded_graphs: types.YAMLDict,
    controller_config: tp.Optional[types.YAMLDict],
    cmdopts: types.Cmdopts,
) -> list[list[types.YAMLDict]]:
    """Calculate what inter-experiment graphs to generate.

    This also defines what CSV files need to be collated, as one graph is
    always generated from one CSV file. Uses YAML configuration for
    controllers and inter-experiment graphs.

    """
    keys: list[str] = []

    if controller_config:
        for category in list(dict(controller_config).keys()):
            if category not in cmdopts["controller"]:
                continue
            category_cfg = tp.cast(types.YAMLDict, controller_config[category])
            controllers = tp.cast(
                list[types.YAMLDict], category_cfg["controllers"]
            )
            for controller in controllers:
                if controller["name"] not in cmdopts["controller"]:
                    continue

                # valid to specify no graphs, and only to inherit graphs
                keys = tp.cast(list[str], controller.get("graphs", []))
                if "graphs_inherit" in controller:
                    inherits = tp.cast(
                        list[list[str]], controller["graphs_inherit"]
                    )
                    for inherit in inherits:
                        keys.extend(inherit)  # optional
        _logger.debug("Loaded %s inter-experiment categories: %s", len(keys), keys)
    else:
        keys = list(loaded_graphs)
        _logger.debug(
            "Missing controller graph config--generating all "
            "inter-experiment graphs for all controllers: %s",
            keys,
        )

    filtered_keys = [k for k in loaded_graphs if k in keys]
    targets = [
        tp.cast(list[types.YAMLDict], loaded_graphs[k]) for k in filtered_keys
    ]

    _logger.debug(
        "Enabled %s inter-experiment categories: %s",
        len(filtered_keys),
        filtered_keys,
    )
    return targets
