#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Generate linegraphs within a single :term:`Experiment`."""

# Core packages
import typing as tp
import logging

# 3rd party packages
import json

# Project packages
from sierra.core import types, exproot, graphs

_logger = logging.getLogger(__name__)


def generate(
    cmdopts: types.Cmdopts, pathset: exproot.PathSet, targets: tp.List[types.YAMLDict]
) -> None:
    """
    Generate linegraphs from: term:`Processed Output Data` files.
    """

    _logger.info(
        "Linegraphs from <batch_root>/%s", pathset.stat_root.relative_to(pathset.parent)
    )

    # For each category of linegraphs we are generating
    for category in targets:
        # For each graph in each category
        for graph in category:

            # Only try to create linegraphs (duh)
            if graph["type"] != "stacked_line":
                continue

            _logger.trace("\n" + json.dumps(graph, indent=4))  # type: ignore

            paths = graphs.PathSet(
                input_root=pathset.stat_root,
                output_root=pathset.graph_root,
                batchroot=pathset.parent.parent,
                model_root=None,
            )

            try:
                # 2025-06-05 [JRH]: We always write stage {3,4} output data
                # files as .csv because that is currently SIERRA's 'native'
                # format; this may change in the future.
                graphs.stacked_line(
                    paths=paths,
                    input_stem=graph["src_stem"],
                    output_stem=graph["dest_stem"],
                    medium="storage.csv",
                    stats=cmdopts["dist_stats"],
                    cols=graph.get("cols", None),
                    title=graph.get("title", ""),
                    legend=graph.get("legend", graph.get("cols", None)),
                    xlabel=graph.get("xlabel", ""),
                    ylabel=graph.get("ylabel", ""),
                    points=graph.get("points", False),
                    logyscale=cmdopts["plot_log_yscale"],
                    large_text=cmdopts["plot_large_text"],
                )
            except KeyError:
                _logger.fatal(
                    ("Could not generate linegraph. " "Possible reasons include: ")
                )

                _logger.fatal(
                    ("1. The YAML configuration entry is " "missing required fields")
                )
                missing_cols = graph.get("cols", "MISSING_KEY")
                missing_stem = graph.get("src_stem", "MISSING_KEY")
                _logger.fatal(
                    (
                        "2. 'cols' is present in YAML "
                        "configuration but some of %s are "
                        "missing from %s"
                    ),
                    missing_cols,
                    missing_stem,
                )

                raise


__all__ = ["generate"]
