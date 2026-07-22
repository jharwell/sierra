#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Container module for the graph product comparison plugin.

See :ref:`plugins/compare/graphs`.
"""

# Core packages

# 3rd party packages

# Project packages
from sierra.core.graphs import sections
from sierra.plugins.compare.graphs import schema

# Comparison graphs are a flat list: there is no controller YAML to
# enable/disable categories at stage 5, since the things being compared are
# named directly on the cmdline.
for _name in ("inter-controller", "inter-scenario"):
    sections.register(
        sections.Section(
            name=_name,
            shape=sections.Shape.FLAT,
            by_type=schema.BY_TYPE,
            owner="compare.graphs",
        )
    )


def sierra_plugin_type() -> str:
    return "pipeline"
