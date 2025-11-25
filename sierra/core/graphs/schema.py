#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""
YAML schemas for graphs.
"""
# Core packages

# 3rd party packages
import strictyaml

# Project packages


heatmap = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        "dest_stem": strictyaml.Str(),
        "type": strictyaml.Str(),
        strictyaml.Optional("col"): strictyaml.Str(),
        strictyaml.Optional("title"): strictyaml.Str(),
        strictyaml.Optional("zlabel"): strictyaml.Str(),
        strictyaml.Optional("xlabel"): strictyaml.Str(),
        strictyaml.Optional("ylabel"): strictyaml.Str(),
        strictyaml.Optional("index"): strictyaml.Int(),
        strictyaml.Optional("x"): strictyaml.Str(),
        strictyaml.Optional("y"): strictyaml.Str(),
        strictyaml.Optional("z"): strictyaml.Str(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.heatmap` graphs.
"""

stacked_line = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        "dest_stem": strictyaml.Str(),
        "type": strictyaml.Str(),
        # Only optional for intra-exp, but there's not a simple way to mark it
        # as such at this level.
        strictyaml.Optional("cols"): strictyaml.Seq(strictyaml.Str()),
        strictyaml.Optional("title"): strictyaml.Str(),
        strictyaml.Optional("legend"): strictyaml.Seq(strictyaml.Str()),
        strictyaml.Optional("xlabel"): strictyaml.Str(),
        strictyaml.Optional("ylabel"): strictyaml.Str(),
        strictyaml.Optional("points"): strictyaml.Bool(),
        strictyaml.Optional("logy"): strictyaml.Bool(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.stacked_line` graphs.
"""

summary_line = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        "dest_stem": strictyaml.Str(),
        "col": strictyaml.Str(),
        strictyaml.Optional("legend"): strictyaml.Seq(strictyaml.Str()),
        strictyaml.Optional("title"): strictyaml.Str(),
        strictyaml.Optional("type"): strictyaml.Str(),
        strictyaml.Optional("xlabel"): strictyaml.Str(),
        strictyaml.Optional("ylabel"): strictyaml.Str(),
        strictyaml.Optional("points"): strictyaml.Bool(),
        strictyaml.Optional("index"): strictyaml.Int(),
        strictyaml.Optional("logy"): strictyaml.Bool(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.summary_line` graphs.
"""

network = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        "dest_stem": strictyaml.Str(),
        "layout": strictyaml.Str(),
        strictyaml.Optional("title"): strictyaml.Str(),
        strictyaml.Optional("type"): strictyaml.Str(),
        strictyaml.Optional("backend"): strictyaml.Str(),
        strictyaml.Optional("large_text"): strictyaml.Str(),
        strictyaml.Optional("node_color_attr"): strictyaml.Str(),
        strictyaml.Optional("edge_color_attr"): strictyaml.Str(),
        strictyaml.Optional("edge_weight_attr"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.network` graphs.
"""
