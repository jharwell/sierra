#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""
Container module for graph generation in stage 4.
"""

# Core packages

# 3rd party packages

# Project packages
from sierra.core.graphs import schema, sections

# Intra- and inter-experiment graphs are both categorized, so that the
# controller YAML can enable/disable whole categories at a time.
#
# 2026-07-24 [JRH]: The two share a type table today. They are registered
# separately (rather than as one Section) because the sections genuinely differ
# -- e.g. 'cols' is required for inter-exp but optional for intra-exp -- and
# keeping them distinct leaves room to express that here later.
for _name in ("intra-exp", "inter-exp"):
    sections.register(
        sections.Section(
            name=_name,
            shape=sections.Shape.CATEGORIZED,
            by_type=schema.BY_TYPE,
            owner="prod.graphs",
        )
    )


def sierra_plugin_type() -> str:
    return "pipeline"
