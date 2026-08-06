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
from sierra.core.yaml import sources as sources_spec


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
        # src and sources are mutually exclusive input spellings, both
        # optional at this level; gconfig enforces exactly-one. With 'sources',
        # the x/y/z columns are drawn from the joined frame (intra-exp only).
        strictyaml.Optional("src"): strictyaml.Str(),
        strictyaml.Optional("sources"): strictyaml.Seq(sources_spec.source),
        strictyaml.Optional("dest"): strictyaml.Str(),
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
        # src and sources are mutually exclusive input spellings, both
        # optional at this level; gconfig enforces exactly-one. Multi-source is
        # a natural fit here: the truth and predicted columns often live in
        # different files (e.g. labels vs model output), joined per experiment.
        strictyaml.Optional("src"): strictyaml.Str(),
        strictyaml.Optional("sources"): strictyaml.Seq(sources_spec.source),
        strictyaml.Optional("dest"): strictyaml.Str(),
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
        # src and sources are mutually exclusive spellings of the input,
        # both optional at this level; gconfig enforces exactly-one. src is
        # the single-file input (the common case); sources draws columns from
        # several files, joined per experiment (intra-exp only). See
        # :data:`~sierra.core.yaml.sources.source`.
        strictyaml.Optional("src"): strictyaml.Str(),
        strictyaml.Optional("sources"): strictyaml.Seq(sources_spec.source),
        strictyaml.Optional("dest"): strictyaml.Str(),
        "type": strictyaml.Enum(["stacked_line"]),
        # Only optional for intra-exp, but there's not a simple way to mark it
        # as such at this level. With 'sources', columns come from inside each
        # source instead, and top-level 'cols' must be absent (enforced in
        # gconfig).
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
        # src and sources are mutually exclusive input spellings, both
        # optional at this level; gconfig enforces exactly-one. sources (columns
        # from several files, joined per experiment) is intra-exp only.
        strictyaml.Optional("src"): strictyaml.Str(),
        strictyaml.Optional("sources"): strictyaml.Seq(sources_spec.source),
        strictyaml.Optional("dest"): strictyaml.Str(),
        "type": strictyaml.Enum(["histogram"]),
        # Required with src for both intra- and inter-exp: intra-exp plots
        # these columns directly; inter-exp uses them during collation. With
        # 'sources' the columns come from inside each source instead, and
        # top-level 'cols' must be absent (enforced in gconfig).
        strictyaml.Optional("cols"): strictyaml.Seq(strictyaml.Str()),
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

scatterplot = strictyaml.Map(
    {
        # src and sources are mutually exclusive input spellings, both
        # optional at this level; gconfig enforces exactly-one. sources (columns
        # from several files, joined per experiment) is intra-exp only.
        strictyaml.Optional("src"): strictyaml.Str(),
        strictyaml.Optional("sources"): strictyaml.Seq(sources_spec.source),
        strictyaml.Optional("dest"): strictyaml.Str(),
        "type": strictyaml.Enum(["scatterplot"]),
        strictyaml.Optional("xcol", default="xcol"): strictyaml.Str(),
        strictyaml.Optional("ycol", default="ycol"): strictyaml.Str(),
        strictyaml.Optional("title", default=""): strictyaml.Str(),
        strictyaml.Optional("xlabel", default=""): strictyaml.Str(),
        strictyaml.Optional("ylabel", default=""): strictyaml.Str(),
        strictyaml.Optional("legend"): strictyaml.Seq(strictyaml.Str()),
        strictyaml.Optional("show_best_fit", default=False): strictyaml.Bool(),
        strictyaml.Optional("best_fit_kind", default="linear"): strictyaml.Enum(
            ["linear", "quadratic", "cubic", "log", "exp"]
        ),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for :func:`~sierra.core.graphs.scatterplot.generate` graphs.
"""

summary_line = strictyaml.Map(
    {
        "src": strictyaml.Str(),
        strictyaml.Optional("dest"): strictyaml.Str(),
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
        "src": strictyaml.Str(),
        strictyaml.Optional("dest"): strictyaml.Str(),
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
    "scatterplot": scatterplot,
}

__all__ = [
    "BY_TYPE",
    "HISTOGRAM_KINDS",
    "NETWORK_LAYOUTS",
    "heatmap",
    "histogram",
    "network",
    "scatterplot",
    "stacked_line",
    "summary_line",
]
