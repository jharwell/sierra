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
import numpy as np
import matplotlib.pyplot as plt
import holoviews as hv
import polars as pl

# Project packages
from sierra.core import utils, config, storage, types
from . import pathset as _pathset, graphutils

_logger = logging.getLogger(__name__)


def generate_confusion(  # noqa: PLR0913
    pathset: _pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    title: str,
    backend: str,
    truth_col: str,
    predicted_col: str,
    stats_center: str,
    xlabels_rotate: bool = False,
    large_text: bool = False,
) -> bool:
    """
    Generate a confusion matrix.

    If the necessary input file does not exist, the graph is not generated.
    Dataframe must be constructed with {truth,predicted} columns; e.g.::

        truth,predicted
        a,a
        a,q
        b,b
        c,c
        d,f
        e,e
        ...
    """
    hv.extension(backend, inline=False, logo=False)

    ofile_ext = graphutils.ofile_ext(backend)
    input_fpath = pathset.input_root / (
        input_stem + config.STATS[stats_center].spreads["none"].exts[stats_center]
    )
    output_fpath = pathset.output_root / f"CM-{output_stem}.{ofile_ext}"
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

    # Read .csv and get counts of each <truth, predicted> pair.
    df = storage.df_read(input_fpath, medium)

    # Group by truth and predicted columns and count occurrences
    confusion_df = df.group_by([truth_col, predicted_col]).agg(pl.len().alias("count"))

    # Get category names. Need union in case the sets aren't the same.
    categories = sorted(
        set(df[truth_col].unique().to_list())
        | set(df[predicted_col].unique().to_list())
    )

    # Create all combinations of categories
    all_combinations = pl.DataFrame(
        {
            truth_col: [t for t in categories for _ in categories],
            predicted_col: [p for _ in categories for p in categories],
        }
    )

    # Merge with actual data, filling missing combinations with 0
    confusion_df = all_combinations.join(
        confusion_df, on=[truth_col, predicted_col], how="left"
    )

    # Fill null counts with 0
    confusion_df = confusion_df.with_columns(pl.col("count").fill_null(0))

    # Normalize by row to get fractions rather than counts
    # Calculate sum for each truth value
    row_totals = confusion_df.group_by(truth_col).agg(
        pl.col("count").sum().alias("row_total")
    )

    # Join back and calculate fractions
    confusion_df = confusion_df.join(row_totals, on=truth_col)
    confusion_df = confusion_df.with_columns(
        (pl.col("count") / pl.col("row_total")).alias("fraction")
    )

    # Drop the row_total column
    confusion_df = confusion_df.drop("row_total")

    # Convert to pandas for holoviews
    confusion_pd = confusion_df.to_pandas()
    dataset = hv.Dataset(
        confusion_pd, kdims=[predicted_col, truth_col], vdims="fraction"
    )

    # Finally, plot the data!
    if backend == "matplotlib":
        plot = hv.HeatMap(dataset).opts(show_values=True, alpha=0.65, cmap="RdYlGn")

    elif backend == "bokeh":
        plot = hv.HeatMap(dataset).opts(
            colorbar=True,
            tools=["hover"],
            alpha=0.65,
            cmap="RdYlGn",
        )
    else:
        raise ValueError(f"Bad value for backend: {backend}")

    # Add labels
    plot.opts(xlabel="Predicted Label")
    plot.opts(ylabel="True Label")

    # Set fontsizes
    plot.opts(
        fontsize={
            "title": text_size["title"],
            "labels": text_size["xyz_label"],
            "ticks": text_size["tick_label"],
        }
    )
    if backend == "matplotlib":
        # Add colorbar.
        # 2025-07-08 [JRH]: backend_opts is a mpl-specific Workaround; doing
        # colorbar_opts={"label": ...} doesn't work for unknown reasons.
        plot.opts(colorbar=True, backend_opts={"colorbar.label": ""})

    # Add title
    plot.opts(title=title)
    if xlabels_rotate:
        plot.opts(xrotation=90)

    graphutils.plot_save(plot, output_fpath, backend)

    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(pathset.batchroot),
    )
    return True


def generate_numeric(  # noqa: PLR0913
    pathset: _pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    title: str,
    backend: str,
    stats_center: str,
    colnames: tuple[str, str, str] = ("x", "y", "z"),
    xlabel: tp.Optional[str] = "",
    ylabel: tp.Optional[str] = "",
    zlabel: tp.Optional[str] = "",
    large_text: bool = False,
    xticklabels: tp.Optional[list[str]] = None,
    yticklabels: tp.Optional[list[str]] = None,
    xticks: tp.Optional[list[float]] = None,
    yticks: tp.Optional[list[float]] = None,
    transpose: bool = False,
) -> bool:
    """
    Generate a X vs. Y vs. Z heatmap plot.

    If the necessary input file does not exist, the graph is not generated.
    Dataframe must be constructed with {x,y,z} columns; e.g.::

       x,y,z
       0,0,4
       0,1,5
       0,2,6
       0,3,4
       1,0,4
       0,1,4
       ...

    The ``x``, ``y`` columns are the indices, and the ``z`` column is the value
    in that cell. The names of these columns are configurable.

    """
    hv.extension(backend, inline=False, logo=False)

    ofile_ext = graphutils.ofile_ext(backend)
    input_fpath = pathset.input_root / (
        input_stem + config.STATS[stats_center].spreads["none"].exts[stats_center]
    )
    output_fpath = pathset.output_root / f"HM-{output_stem}.{ofile_ext}"
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

    # Read .csv and create raw heatmap from default configuration
    df = storage.df_read(input_fpath, medium)

    # Convert to pandas for holoviews
    df_pd = df.to_pandas()

    # Transpose if requested
    kdims = [colnames[1], colnames[0]] if transpose else [colnames[0], colnames[1]]

    dataset = hv.Dataset(df_pd, kdims=kdims, vdims=colnames[2])

    # Plot heatmap, without showing the Z-value in each cell, which generally
    # obscures things more than it helps. Plus, statistical significance isn't
    # observable from a heatmap, so numerical values are kind of moot.
    if backend == "matplotlib":
        plot = hv.HeatMap(
            dataset, kdims=[colnames[0], colnames[1]], vdims=[colnames[2]]
        ).opts(show_values=False)
    elif backend == "bokeh":
        plot = hv.HeatMap(
            dataset, kdims=[colnames[0], colnames[1]], vdims=[colnames[2]]
        )
    else:
        raise ValueError(f"Bad value for backend: {backend}")

    if not xticks:
        xticks = dataset.data[colnames[0]]
    if not yticks:
        yticks = dataset.data[colnames[1]]
    # Add X,Y ticks
    if xticklabels:
        plot.opts(xticks=list(zip(xticks, xticklabels)))
    if yticklabels:
        plot.opts(yticks=list(zip(yticks, yticklabels)))

    # Add labels
    plot.opts(xlabel=xlabel)
    plot.opts(ylabel=ylabel)

    # Set fontsizes
    plot.opts(
        fontsize={
            "title": text_size["title"],
            "labels": text_size["xyz_label"],
            "ticks": text_size["tick_label"],
        }
    )

    # Add title
    plot.opts(title=title)

    if backend == "matplotlib":
        # Add colorbar.
        # 2025-07-08 [JRH]: backend_opts is a mpl-specific Workaround; doing
        # colorbar_opts={"label": ...} doesn't work for unknown reasons.
        plot.opts(colorbar=True, backend_opts={"colorbar.label": zlabel})

    graphutils.plot_save(plot, output_fpath, backend)

    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(pathset.batchroot),
    )
    return True


__all__ = ["generate_confusion", "generate_numeric"]
