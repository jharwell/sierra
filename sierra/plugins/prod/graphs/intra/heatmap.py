#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Generate heatmaps within a single :term:`Experiment`."""

# Core packages
import typing as tp
import logging

# 3rd party packages
import json

# Project packages
from sierra.core import types, exproot, graphs

_logger = logging.getLogger(__name__)


def generate(
    cmdopts: types.Cmdopts,
    pathset: exproot.PathSet,
    targets: tp.List[types.YAMLDict],
) -> None:
    """
    Generate heatmaps from: term:`Processed Output Data` files.
    """
    large_text = cmdopts["plot_large_text"]

    _logger.info(
        "Heatmaps from <batch_root>/%s", pathset.stat_root.relative_to(pathset.parent)
    )

    # For each category of heatmaps we are generating
    for category in targets:

        # For each graph in each category
        for graph in category:
            # Only try to create heatmaps (duh)
            if graph["type"] != "heatmap":
                continue

            _logger.trace("\n" + json.dumps(graph, indent=4))  # type: ignore

            graph_pathset = graphs.PathSet(
                input_root=pathset.stat_root,
                output_root=pathset.graph_root,
                batchroot=pathset.parent.parent,
                model_root=None,
            )
            # 2025-06-05 [JRH]: We always write stage {3,4} output data files as
            # .csv because that is currently SIERRA's 'native' format; this may
            # change in the future.
            graphs.heatmap(
                pathset=graph_pathset,
                input_stem=graph["src_stem"],
                output_stem=graph["dest_stem"],
                medium="storage.csv",
                title=graph.get("title", None),
                xlabel=graph.get("xlabel", None),
                ylabel=graph.get("ylabel", None),
                zlabel=graph.get("zlabel", None),
                colnames=(
                    graph.get("x", "x"),
                    graph.get("y", "y"),
                    graph.get("z", "z"),
                ),
                large_text=large_text,
            )


__all__ = ["generate"]
