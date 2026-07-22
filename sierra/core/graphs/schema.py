#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""
YAML schemas for graphs.

Each schema below is the *single* source of truth for the set of keys a given
graph type accepts, which of those keys are required, and what value each
optional key takes when omitted from YAML. Consumers should therefore index
validated config directly (``loaded["title"]``) rather than re-supplying
defaults via ``.get()``; the only exception is for values which are derived
from the cmdline rather than from YAML (e.g. ``backend``, ``logy``), which
cannot be expressed here.
"""
# Core packages

# 3rd party packages
import strictyaml

# Project packages


#: Ways of rendering multiple histograms onto a single plot. Referenced by
#: :data:`histogram` so that the schema and
#: :func:`sierra.core.graphs.histogram.generate` cannot drift apart.
HISTOGRAM_KINDS = ["overlay", "steps", "facet"]

#: networkx layouts supported by :func:`sierra.core.graphs.network.generate`.
NETWORK_LAYOUTS = [
    "spring",
    "spectral",
    "planar",
    "spiral",
    "graphviz_neato",
    "graphviz_dot",
    "bfs",
]

heatmap = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        strictyaml.Optional("dest_stem"): strictyaml.Str(),
        "type": strictyaml.Enum(["heatmap"]),
        strictyaml.Optional("title", default=""): strictyaml.Str(),
        strictyaml.Optional("zlabel", default=""): strictyaml.Str(),
        strictyaml.Optional("xlabel", default=""): strictyaml.Str(),
        strictyaml.Optional("ylabel", default=""): strictyaml.Str(),
        strictyaml.Optional("index", default=-1): strictyaml.Int(),
        strictyaml.Optional("x", default="x"): strictyaml.Str(),
        strictyaml.Optional("y", default="y"): strictyaml.Str(),
        strictyaml.Optional("z", default="z"): strictyaml.Str(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.heatmap.generate_numeric` graphs.
"""

confusion_matrix = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        strictyaml.Optional("dest_stem"): strictyaml.Str(),
        "type": strictyaml.Enum(["confusion_matrix"]),
        strictyaml.Optional("title", default=""): strictyaml.Str(),
        strictyaml.Optional("truth_col", default="truth"): strictyaml.Str(),
        strictyaml.Optional("predicted_col", default="predicted"): strictyaml.Str(),
        strictyaml.Optional("xlabels_rotate", default=False): strictyaml.Bool(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.heatmap.generate_confusion` graphs.
"""

stacked_line = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        strictyaml.Optional("dest_stem"): strictyaml.Str(),
        "type": strictyaml.Enum(["stacked_line"]),
        # Only optional for intra-exp, but there's not a simple way to mark it
        # as such at this level.
        strictyaml.Optional("cols"): strictyaml.Seq(strictyaml.Str()),
        strictyaml.Optional("title", default=""): strictyaml.Str(),
        strictyaml.Optional("legend"): strictyaml.Seq(strictyaml.Str()),
        # 2026-07-22 [JRH]: Deliberate special case. Inter-exp stacked
        # linegraphs are always a time series across experiments, so "Time" is
        # the right default here rather than the "" used everywhere else.
        strictyaml.Optional("xlabel", default="Time"): strictyaml.Str(),
        strictyaml.Optional("ylabel", default=""): strictyaml.Str(),
        strictyaml.Optional("points", default=False): strictyaml.Bool(),
        strictyaml.Optional("logy"): strictyaml.Bool(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.stacked_line.generate` graphs.
"""

histogram = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        strictyaml.Optional("dest_stem"): strictyaml.Str(),
        "type": strictyaml.Enum(["histogram"]),
        # Required for both intra- and inter-exp. Intra-exp plots these columns
        # directly; inter-exp uses them during collation to build the collated
        # frame which is then plotted in its entirety.
        "cols": strictyaml.Seq(strictyaml.Str()),
        strictyaml.Optional("kind", default="overlay"): strictyaml.Enum(
            HISTOGRAM_KINDS
        ),
        strictyaml.Optional("bins"): strictyaml.Int(),
        strictyaml.Optional("title", default=""): strictyaml.Str(),
        strictyaml.Optional("legend"): strictyaml.Seq(strictyaml.Str()),
        strictyaml.Optional("xlabel", default=""): strictyaml.Str(),
        strictyaml.Optional("ylabel", default="Count"): strictyaml.Str(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.histogram.generate` graphs.
"""

summary_line = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        strictyaml.Optional("dest_stem"): strictyaml.Str(),
        "type": strictyaml.Enum(["summary_line"]),
        "col": strictyaml.Str(),
        strictyaml.Optional("legend"): strictyaml.Seq(strictyaml.Str()),
        strictyaml.Optional("title", default=""): strictyaml.Str(),
        strictyaml.Optional("xlabel", default=""): strictyaml.Str(),
        strictyaml.Optional("ylabel", default=""): strictyaml.Str(),
        strictyaml.Optional("points", default=False): strictyaml.Bool(),
        strictyaml.Optional("index", default=-1): strictyaml.Int(),
        strictyaml.Optional("logy"): strictyaml.Bool(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.summary_line.generate` graphs.
"""

network = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        strictyaml.Optional("dest_stem"): strictyaml.Str(),
        "type": strictyaml.Enum(["network"]),
        strictyaml.Optional("layout", default="spring"): strictyaml.Enum(
            NETWORK_LAYOUTS
        ),
        strictyaml.Optional("title", default=""): strictyaml.Str(),
        strictyaml.Optional("backend"): strictyaml.Str(),
        strictyaml.Optional("node_color_attr"): strictyaml.Str(),
        strictyaml.Optional("node_size_attr"): strictyaml.Str(),
        strictyaml.Optional("edge_color_attr"): strictyaml.Str(),
        strictyaml.Optional("edge_weight_attr"): strictyaml.Str(),
        strictyaml.Optional("edge_label_attr"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.network.generate` graphs.
"""

#: Maps the value of the ``type`` key to the schema which validates that graph
#: type. Used to drive validation and dispatch so that adding a graph type is a
#: single-line change.
BY_TYPE = {
    "heatmap": heatmap,
    "confusion_matrix": confusion_matrix,
    "stacked_line": stacked_line,
    "histogram": histogram,
    "summary_line": summary_line,
    "network": network,
}

__all__ = [
    "BY_TYPE",
    "HISTOGRAM_KINDS",
    "NETWORK_LAYOUTS",
    "heatmap",
    "histogram",
    "network",
    "stacked_line",
    "summary_line",
]
