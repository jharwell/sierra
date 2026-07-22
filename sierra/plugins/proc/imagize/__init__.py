#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Container module for the imagize plugin.

See :ref:`plugins/proc/imagize`.
"""

# Core packages

# 3rd party packages

# Project packages
from sierra.core.graphs import schema, sections

# Imagizing turns per-experiment directories of data files into directories of
# images (later stitched into videos), so its config is a flat list with no
# category level.
#
# Only heatmaps and networks can be imagized: everything else needs a full time
# series, which a single frame does not have. The schemas are shared verbatim
# with prod.graphs -- an imagized heatmap *is* a heatmap.
sections.register(
    sections.Section(
        name="imagize",
        shape=sections.Shape.FLAT,
        by_type={
            "heatmap": schema.heatmap,
            "network": schema.network,
        },
        owner="proc.imagize",
    )
)


def sierra_plugin_type() -> str:
    return "pipeline"
