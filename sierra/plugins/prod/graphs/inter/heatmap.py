#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Generate heatmaps *across* multiple :term:`Experiments <Experiment>`."""

# Core packages
import typing as tp
import logging

# 3rd party packages
import json
import yaml
import strictyaml

# Project packages
from sierra.core import types, batchroot, graphs
from sierra.core.graphs import bcbridge, schema

_logger = logging.getLogger(__name__)


def generate(
    cmdopts: types.Cmdopts,
    pathset: batchroot.PathSet,
    targets: list[types.YAMLDict],
    info: bcbridge.GraphInfo,
) -> None:
    """
    Generate heatmaps from: term:`Processed Output Data` files.
    """
    large_text = cmdopts["plot_large_text"]

    _logger.info(
        "Heatmaps from <batch_root>/%s",
        pathset.stat_interexp_root.relative_to(pathset.root),
    )

    # For each category of heatmaps we are generating
    for category in targets:

        # For each graph in each category
        for graph in category:
            # Only try to create heatmaps (duh)
            if graph["type"] != "heatmap":
                continue

            _logger.trace("\n" + json.dumps(graph, indent=4))

            try:
                loaded = strictyaml.load(yaml.dump(graph), schema.heatmap).data

            except strictyaml.YAMLError as e:
                _logger.critical("Non-conformant heatmap YAML: %s", e)
                raise

            graph_pathset = graphs.PathSet(
                input_root=pathset.stat_interexp_root,
                output_root=pathset.graph_interexp_root,
                batchroot=pathset.root,
                model_root=None,
            )
            # 2025-06-05 [JRH]: We always write stage {3,4} output data files as
            # .csv because that is currently SIERRA's 'native' format; this may
            # change in the future.
            graphs.heatmap(
                pathset=graph_pathset,
                input_stem=loaded["dest_stem"],
                output_stem=loaded["dest_stem"],
                medium="storage.csv",
                title=loaded.get("title", None),
                xlabel=info.xlabel,
                ylabel=info.ylabel,
                xticklabels=info.xticklabels,
                yticklabels=info.yticklabels,
                xticks=info.xticks,
                yticks=info.yticks,
                zlabel=loaded.get("zlabel", ""),
                backend=loaded.get("backend", cmdopts["graphs_backend"]),
                colnames=(
                    loaded.get("x", "x"),
                    loaded.get("y", "y"),
                    loaded.get("z", "z"),
                ),
                large_text=large_text,
            )


__all__ = ["generate"]
