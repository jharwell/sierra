# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
Heatmap graph generation classes for stage{4,5}.
"""

# Core packages
import textwrap
import typing as tp
import logging
import pathlib

# 3rd party packages
import matplotlib.pyplot as plt
import networkx as nx
import holoviews as hv
import bokeh
import numpy as np
import matplotlib as mpl

# Project packages
from sierra.core import utils, config
from . import pathset as _pathset

_logger = logging.getLogger(__name__)


def _ofile_ext(backend: str) -> tp.Optional[str]:
    if backend == "matplotlib":
        return str(config.GRAPHS["static_type"])

    if backend == "bokeh":
        return str(config.GRAPHS["interactive_type"])

    return None


def generate(  # noqa: PLR0913
    pathset: _pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    title: str,
    backend: str,
    layout: str,
    node_color_attr: tp.Optional[str] = None,
    node_size_attr: tp.Optional[str] = None,
    edge_color_attr: tp.Optional[str] = None,
    edge_weight_attr: tp.Optional[str] = None,
    edge_label_attr: tp.Optional[str] = None,
    large_text: bool = False,
) -> bool:
    """
    Generate a network (graph) plot from a ``.graphml`` file, using networkx.

    """
    hv.extension(backend, inline=False, logo=False)

    ofile_ext = _ofile_ext(backend)
    input_fpath = pathset.input_root / (input_stem + ".graphml")
    output_fpath = pathset.output_root / f"N-{output_stem}.{ofile_ext}"
    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(pathset.batchroot.resolve()),
            input_fpath.relative_to(pathset.batchroot.resolve()),
        )
        return False

    title = "\n".join(textwrap.wrap(title, 40))

    text_size = (
        config.GRAPHS["text_size_large"]
        if large_text
        else config.GRAPHS["text_size_small"]
    )

    # Read GraphML
    G = nx.read_graphml(input_fpath)

    # 2025-11-24 [JRH]: Sizing nodes according to their degree seems to give
    # good results/highlight interesting areas of graphs, and is a good default
    # when no size attribute is provided. The min/max are
    # empirically determined.
    if not node_size_attr:
        degrees = [G.degree(i) for i in G.nodes()]
        min_size, max_size = 10, 25
        min_degree, max_degree = min(degrees), max(degrees)
        for node in G.nodes():
            G.nodes[node]["size"] = min_size + (G.degree(node) - min_degree) / (
                max(max_degree - min_degree, 1)
            ) * (max_size - min_size)

        node_size_attr = "size"

    # Build plot and configure
    plot, positions = _build_plot(
        G,
        layout,
    )

    plot.opts(
        node_size=node_size_attr,
        node_color=node_color_attr if node_color_attr else "gray",
        edge_color=edge_color_attr if edge_color_attr else "black",
        edge_linewidth=edge_weight_attr if edge_weight_attr else 2,
        xaxis=None,
        yaxis=None,
    )
    if backend == "bokeh" and edge_label_attr is not None:
        plot.opts(edge_label=edge_label_attr)
    elif backend == "matplotlib":

        plot.opts(
            fontsize={
                "title": text_size["title"],
                "labels": text_size["xyz_label"],
                "ticks": text_size["tick_label"],
            }
        )

    plot.opts(title=title)
    try:
        _save(plot, output_fpath, backend)
    except Exception as e:
        _logger.warning("Failed to output plot: %s", e)

    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(pathset.batchroot),
    )
    return True


def _build_plot(G: nx.Graph, layout: str) -> tuple:
    # Create graph
    if layout == "spring":
        nxlayout = nx.spring_layout(G, k=3.0, iterations=100, seed=42, scale=5.0)
    elif layout == "spectral":
        nxlayout = nx.spectral_layout(G, scale=5.0)
    elif layout == "planar":
        nxlayout = nx.planar_layout(G, scale=5.0)
    elif layout == "spiral":
        nxlayout = nx.spiral_layout(G, scale=5.0)
    elif layout == "graphviz_dot":
        root = _find_root_node(G)
        nxlayout = nx.nx_agraph.graphviz_layout(G, prog="dot", root=root)
    elif layout == "graphviz_neato":
        root = _find_root_node(G)
        nxlayout = nx.nx_agraph.graphviz_layout(G, prog="neato", root=root)
    elif layout == "bfs":
        root = _find_root_node(G)
        nxlayout = nx.bfs_layout(G, root, scale=5.0)
    else:
        raise RuntimeError(f"Unknown layout '{layout}'. See docs for valid values.")

    return hv.Graph.from_networkx(G, nxlayout), nxlayout


def _find_root_node(G: nx.Graph):
    """
    Find the root node in a tree (both directed/undirected graphs).

    For directed graphs, root is the node with in-degree = 0.  For undirected
    graphs, root is the center node (minimum eccentricity)
    """

    # Check if it's a tree
    is_directed = G.is_directed()

    if is_directed:
        # Check if it's a directed tree (arborescence)
        if not nx.is_tree(G):
            print("Warning: Not a valid tree structure")
            return None

        # Find node with in-degree = 0 (no incoming edges)
        root_candidates = [node for node in G.nodes() if G.in_degree(node) == 0]

        if len(root_candidates) == 0:
            _logger.warning("No root found (no node with in-degree 0)")
            return None

        if len(root_candidates) > 1:
            _logger.warning("Multiple potential roots found: %s", root_candidates)
            return root_candidates[0]

        return root_candidates[0]

    # Undirected graph - find center
    if not nx.is_tree(G):
        _logger.warning("Not a valid tree structure")
        return None

    # Find center node(s) - node with minimum eccentricity
    center_nodes = nx.center(G)
    return center_nodes[0]  # Return first center node


def _save(plot: hv.Overlay, output_fpath: pathlib.Path, backend: str) -> None:
    if backend == "matplotlib":
        hv.save(
            plot.opts(fig_inches=config.GRAPHS["base_size"]),
            output_fpath,
            fig=config.GRAPHS["static_type"],
            dpi=config.GRAPHS["dpi"],
        )
        plt.close("all")

    elif backend == "bokeh":
        fig = hv.render(plot)

        # 2025-12-02 [JRH]: We don't set dimensions, because that makes the
        # interactive plots fixed size, which makes them unsuitable for
        # embedding into webpages.
        fig.sizing_mode = "scale_width"

        html = bokeh.embed.file_html(fig, resources=bokeh.resources.INLINE)
        with output_fpath.open("w") as f:
            f.write(html)


__all__ = ["generate"]
