# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
{Intra,Inter}-experiment line graph generation for stage{4,5}.
"""

# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages
import polars as pl
import holoviews as hv
import numpy as np

# Project packages
from sierra.core import config, utils, storage, models, types
from . import pathset, graphutils

_logger = logging.getLogger(__name__)


def generate(  # noqa: PLR0913
    pathset: pathset.PathSet,
    input_stem: str,
    output_stem: str,
    title: str,
    medium: str,
    backend: str,
    stats_center: str,
    stats_spread: str,
    xticks: tp.Optional[list[float]] = None,
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    points: bool = False,
    large_text: bool = False,
    legend: tp.Optional[list[str]] = None,
    xticklabels: tp.Optional[list[str]] = None,
    cols: tp.Optional[list[str]] = None,
    logyscale: bool = False,
) -> bool:
    """Generate a line graph from a set of columns in a file.

    If the necessary data file does not exist, the graph is not generated.

    If the .stddev file that goes with the .mean does not exist, then no error
    bars are plotted.

    If the .model file that goes with the .mean does not exist, then no model
    predictions are plotted.
    """
    hv.extension(backend, inline=False, logo=False)

    input_fpath = pathset.input_root / (
        input_stem + config.STATS[stats_center].spreads["none"].exts[stats_center]
    )
    output_fpath = pathset.output_root / "SLN-{}.{}".format(
        output_stem, graphutils.ofile_ext(backend)
    )

    text_size = (
        config.GRAPHS["text_size_large"]
        if large_text
        else config.GRAPHS["text_size_small"]
    )

    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(pathset.batchroot),
            input_fpath.relative_to(pathset.batchroot),
        )
        return False

    df = storage.df_read(input_fpath, medium)

    # Use xticks if provided, otherwise default to using row indices as xticks
    dfcols = df.columns

    # Add row index first
    df = df.with_row_index("index")

    # Add xticks column
    if xticks is not None:
        df = df.with_columns(pl.Series("xticks", xticks))
    else:
        df = df.with_columns(pl.col("index").cast(pl.Float64).alias("xticks"))

    # Convert to pandas for holoviews compatibility
    df_pd = df.to_pandas()

    dataset = hv.Dataset(
        data=df_pd,
        kdims=["index"],
        vdims=cols if cols else list(dfcols),
    )
    assert len(df) == len(
        df["xticks"]
    ), "Length mismatch between xticks,# data points: {} vs {}".format(
        len(df["xticks"]), len(df)
    )

    model = _read_models(pathset.model_root, input_stem, medium)

    stat_dfs = graphutils.read_spread_stats(
        stats_center, stats_spread, pathset.input_root, input_stem, medium
    )

    # Plot stats if they have been computed FIRST, so they appear behind the
    # actual data.
    #
    # Build the vdim-name -> color map ONCE here so the curves (drawn by
    # _plot_selected_cols) and the bw boxes (drawn by _plot_stats_bw) agree on
    # color. HoloViews colors an NdOverlay by its SORTED key order, so we must
    # replicate that sort here rather than using dataframe/vdim order, otherwise
    # the boxes and curves drift out of sync whenever the labels don't sort into
    # the same order as the dataframe columns.
    vdim_color = graphutils.build_color_map(dataset, legend)

    plot = graphutils.plot_stats(
        dataset,
        stats_center,
        stats_spread,
        stat_dfs,
        backend=backend,
        vdim_color=vdim_color,
    )

    # Plot specified columns from dataframe.
    plot *= _plot_selected_cols(
        dataset, model, legend, points, backend, vdim_color=vdim_color
    )

    # Let the backend decide # of columns; can override with
    # legend_cols=N in the future if desired.
    plot.opts(show_legend=True, legend_position="bottom")

    # Add title
    plot.opts(title=title)

    # Add X,Y labels
    if xlabel is not None:
        plot.opts(xlabel=xlabel)

    if ylabel is not None:
        plot.opts(ylabel=ylabel)

    # Set fontsizes
    plot.opts(
        fontsize={
            "title": text_size["title"],
            "labels": text_size["xyz_label"],
            "ticks": text_size["tick_label"],
            "legend": text_size["legend_label"],
        },
    )

    if logyscale:
        _min = min(dataset[vdim].min() for vdim in dataset.vdims)
        _max = max(dataset[vdim].max() for vdim in dataset.vdims)

        plot.opts(
            logy=True,
            ylim=(
                _min * 0.9,
                _max * 1.1,
            ),
        )

    graphutils.plot_save(plot, output_fpath, backend)
    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(pathset.batchroot),
    )
    return True


def _plot_selected_cols(
    dataset: hv.Dataset,
    model_info: models.ModelInfo,
    legend: tp.Optional[list[str]],
    show_points: bool,
    backend: str,
    vdim_color: dict[str, str],
) -> hv.NdOverlay:
    """
    Plot the  selected columns in a dataframe.
    """
    # Build the data curves as an NdOverlay keyed by a 'series' dimension. The
    # matplotlib backend generates a legend from an NdOverlay's key dimension
    # automatically; a plain Overlay of individually-labeled Curves mixed with
    # many other element types (e.g. the bw Segments/Rectangles) does not
    # reliably produce a legend.
    curves = {}
    for i, vdim in enumerate(dataset.vdims):
        label = legend[i] if legend else vdim.name
        curves[label] = hv.Curve(dataset, dataset.kdims[0], vdim.name)

    plot: hv.Overlay = hv.NdOverlay(curves, kdims="series")

    # Plot the points for each curve if configured to do so, OR if there aren't
    # that many. If you print them and there are a lot, you essentially get
    # really fat lines which doesn't look good. Points carry no legend entry.
    #
    # Each point element is colored explicitly from the shared vdim_color map.
    # Without this, HoloViews auto-cycles the Points by overlay position, which
    # is a DIFFERENT order than the sorted-key order it uses for the curve
    # NdOverlay -- so points would end up a different color than their own curve
    # (e.g. gold markers on the red curve).
    pts = []
    for v in dataset.vdims:
        if len(dataset[v]) <= 50 or show_points:
            p = hv.Points((dataset[dataset.kdims[0]], dataset[v]))
            if vdim_color is not None:
                p = p.opts(color=vdim_color[v.name])
            pts.append(p)

    if pts:
        points_size = tp.cast(dict[str, tp.Any], config.GRAPHS["points_size"])
        plot *= hv.Overlay(pts).opts(
            hv.opts.Points(show_legend=False, **points_size[backend])
        )

    # Plot models if they have been computed
    if model_info.dataset:
        plot = _plot_model(dataset, plot, model_info, show_points, backend, vdim_color)

    return plot


def _plot_model(
    dataset: hv.Dataset,
    plot: hv.Overlay,
    model_info: models.ModelInfo,
    show_points: bool,
    backend: str,
    vdim_color: dict[str, str],
) -> hv.NdOverlay:
    """
    Plot the model for the graph, if one exists.
    """
    # Plot models if they have been computed
    model_curves = {}
    curve_style = tp.cast(dict[str, tp.Any], config.GRAPHS["curve_style"])

    for i, vdim in enumerate(model_info.dataset.vdims):
        model_curves[model_info.legend[i]] = hv.Curve(
            model_info.dataset,
            model_info.dataset.kdims[0],
            vdim.name,
        ).opts(**curve_style[backend])
    plot = plot * hv.NdOverlay(model_curves, kdims="model_series")

    # Plot the points for each curve
    model_pts = [
        hv.Points(
            (
                model_info.dataset[model_info.dataset.kdims[0]],
                model_info.dataset[v],
            )
        )
        for v in model_info.dataset.vdims
        if len(model_info.dataset[v]) <= 50 or show_points
    ]
    if model_pts:
        plot = plot * hv.Overlay(model_pts).opts(hv.opts.Points(show_legend=False))

    return plot


def _build_color_map(
    dataset: hv.Dataset, legend: tp.Optional[list[str]]
) -> dict[str, str]:
    """Map each vdim NAME to the color HoloViews will use for its curve.

    The curves are drawn as an NdOverlay keyed by label, and HoloViews assigns
    colors from the default Cycle in SORTED key order (not dataframe order). To
    keep the bw boxes color-matched to their curves, we replicate that exact
    assignment here: sort the labels, zip them against the cycle, then map back
    from label to the originating vdim name.
    """
    colors = hv.Cycle().values
    # vdim-name -> label (falls back to the name itself when no legend given)
    name_to_label = {
        vdim.name: (legend[i] if legend else vdim.name)
        for i, vdim in enumerate(dataset.vdims)
    }
    # HoloViews colors NdOverlay entries in sorted-key order.
    sorted_labels = sorted(name_to_label.values())
    label_to_color = {
        lab: colors[i % len(colors)] for i, lab in enumerate(sorted_labels)
    }
    return {name: label_to_color[label] for name, label in name_to_label.items()}


# 2024/09/13 [JRH]: The union is for compatability with type checkers in
# python {3.8,3.11}.
def _read_models(
    model_root: tp.Optional[pathlib.Path], input_stem: str, medium: str
) -> models.ModelInfo:

    if model_root is None:
        return models.ModelInfo()

    modelf = model_root / (input_stem + config.MODELS_EXT["model"])
    legendf = model_root / (input_stem + config.MODELS_EXT["legend"])

    if not utils.path_exists(modelf):
        _logger.trace("Model file %s missing for graph", str(modelf))
        return models.ModelInfo()

    info = models.ModelInfo()
    df = storage.df_read(modelf, medium)
    cols = list(df.columns)

    # Add index and convert to pandas for holoviews
    df = df.with_row_index("index")
    df_pd = df.to_pandas()

    info.dataset = hv.Dataset(data=df_pd, kdims=["index"], vdims=cols)

    with utils.utf8open(legendf, "r") as f:
        info.legend = f.read().splitlines()

    _logger.trace(
        "Loaded model='%s',legend='%s'",
        modelf.relative_to(model_root),
        legendf.relative_to(model_root),
    )

    return info


__all__ = ["generate"]
