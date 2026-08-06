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
    xticks: tp.Optional[list[float]] = None,
    stats: tp.Optional[str] = None,
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    points: bool = False,
    large_text: bool = False,
    legend: tp.Optional[list[str]] = None,
    xticklabels: tp.Optional[list[str]] = None,
    cols: tp.Optional[list[str]] = None,
    logyscale: bool = False,
    ext: str = config.STATS["mean"].exts["mean"],
) -> bool:
    """Generate a line graph from a set of columns in a file.

    If the necessary data file does not exist, the graph is not generated.

    If the .stddev file that goes with the .mean does not exist, then no error
    bars are plotted.

    If the .model file that goes with the .mean does not exist, then no model
    predictions are plotted.
    """
    hv.extension(backend, inline=False, logo=False)

    input_fpath = pathset.input_root / (input_stem + ext)
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
    stat_dfs = _read_stats(stats, pathset.input_root, input_stem, medium)

    # Plot stats if they have been computed FIRST, so they appear behind the
    # actual data.
    #
    # Build the vdim-name -> color map ONCE here so the curves (drawn by
    # _plot_selected_cols) and the bw boxes (drawn by _plot_stats_bw) agree on
    # color. HoloViews colors an NdOverlay by its SORTED key order, so we must
    # replicate that sort here rather than using dataframe/vdim order, otherwise
    # the boxes and curves drift out of sync whenever the labels don't sort into
    # the same order as the dataframe columns.
    vdim_color = _build_color_map(dataset, legend)

    if stats and "conf95" in stats and "stddev" in stat_dfs:
        plot = _plot_stats_stddev(
            dataset, stat_dfs["stddev"], backend=backend, vdim_color=vdim_color
        )
        plot *= _plot_selected_cols(
            dataset, model, legend, points, backend, vdim_color=vdim_color
        )
    elif (
        stats and "bw" in stats and all(k in stat_dfs for k in config.STATS["bw"].exts)
    ):
        # bw glyphs are drawn as 4 merged elements (see _plot_stats_bw), which
        # keeps the overlay small enough that curves, points, and the legend all
        # coexist on the matplotlib backend.
        plot = _plot_stats_bw(dataset, stat_dfs, vdim_color, backend)
        plot *= _plot_selected_cols(
            dataset, model, legend, points, backend, vdim_color=vdim_color
        )
    else:
        # Plot specified columns from dataframe.
        plot = _plot_selected_cols(
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

    graphutils.save_plot(plot, output_fpath, backend)
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


def _plot_stats_stddev(
    dataset: hv.Dataset,
    stddev_df: pl.DataFrame,
    backend: str,
    vdim_color: dict[str, str],
) -> hv.NdOverlay:
    """Plot the stddev for all columns in the dataset."""

    # Build stddev columns dictionary
    stddev_cols = {}
    for c in dataset.vdims:
        stddev_vals = stddev_df[c.name].abs().to_numpy()
        stddev_cols[f"{c}_stddev_l"] = dataset.data[c.name] - 2 * stddev_vals
        stddev_cols[f"{c}_stddev_u"] = dataset.data[c.name] + 2 * stddev_vals

    # Add stddev columns to dataset
    for col_name, col_data in stddev_cols.items():
        dataset.data[col_name] = col_data

    fill_key = "facecolor" if backend == "matplotlib" else "fill_color"
    return hv.Overlay(
        [
            hv.Area(
                dataset, vdims=[f"{vdim.name}_stddev_l", f"{vdim.name}_stddev_u"]
            ).opts(alpha=0.5, **{fill_key: vdim_color[vdim.name]})
            for vdim in dataset.vdims
        ]
    )


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


def _plot_stats_bw(
    dataset: hv.Dataset,
    stat_dfs: dict[str, pl.DataFrame],
    vdim_color: dict[str, str],
    backend: str,
) -> hv.Overlay:
    """Box-and-whisker glyphs at each datapoint.

    All columns' glyphs of a given type are merged into a SINGLE element
    (one Segments for all whiskers, one Rectangles for all boxes, etc.),
    with per-column color carried as a 'color' value dimension. This keeps
    the total element count at 4 regardless of column count.

    The merge matters for more than tidiness: when curves + points + a large
    per-datapoint box overlay all land in one overlay, HoloViews' matplotlib
    backend stops propagating curve labels to the legend once the element
    count gets high enough. Collapsing the boxes from 4-per-column to 4 total
    keeps the overlay small enough that the legend (and the points) survive.
    """
    xs = dataset.data[dataset.kdims[0].name].to_numpy()
    w = 0.3 * float(np.min(np.diff(np.sort(xs)))) if len(xs) > 1 else 0.3
    cw = w * 0.6

    q1_df, q3_df = stat_dfs["q1"], stat_dfs["q3"]
    median_df = stat_dfs["median"]
    whislo_df, whishi_df = stat_dfs["whislo"], stat_dfs["whishi"]
    cilo_df, cihi_df = stat_dfs["cilo"], stat_dfs["cihi"]

    # (x0, y0, x1, y1, color) rows accumulated across ALL columns. Color comes
    # from the shared vdim_color map (built in generate() to match how
    # HoloViews colors the curve NdOverlay), so box color == curve color for
    # every column regardless of dataframe vs sorted-label ordering.
    box_rows: list = []
    whisk_rows: list = []
    med_rows: list = []
    ci_rows: list = []

    for vdim in dataset.vdims:
        c = vdim.name
        if c not in q1_df.columns:
            continue
        color = vdim_color[c]

        q1, q3 = q1_df[c].to_numpy(), q3_df[c].to_numpy()
        med = median_df[c].to_numpy()
        wlo, whi = whislo_df[c].to_numpy(), whishi_df[c].to_numpy()
        clo, chi = cilo_df[c].to_numpy(), cihi_df[c].to_numpy()

        for i, x in enumerate(xs):
            box_rows.append((x - w, q1[i], x + w, q3[i], color))
            whisk_rows.append((x, wlo[i], x, whi[i], color))
            med_rows.append((x - w, med[i], x + w, med[i], color))
            ci_rows.append((x - cw, clo[i], x + cw, clo[i], color))
            ci_rows.append((x - cw, chi[i], x + cw, chi[i], color))

    whiskers = hv.Segments(whisk_rows, vdims="color").opts(
        color="color", alpha=0.6, show_legend=False
    )
    boxes = hv.Rectangles(box_rows, vdims="color").opts(
        color="color", alpha=0.25, show_legend=False
    )
    medians = hv.Segments(med_rows, vdims="color").opts(
        color="color", alpha=0.9, show_legend=False
    )
    # CI (median confidence interval) markers get a DASHED style so they read
    # as distinct from the solid median line. The dash opt differs by backend:
    # matplotlib uses linestyle, bokeh uses line_dash (as a STRING keyword, not
    # a list -- a list is unhashable in this Segments context on bokeh).
    #
    # At small N the CI half-width (1.57*IQR/sqrt(N)) can exceed the box, so
    # these marks may sit well outside the box; that is correct and shrinks as
    # sqrt(N) grows for production runs.
    if backend == "matplotlib":
        ci_style: dict[str, tp.Any] = {"linestyle": "--"}
    else:
        ci_style = {"line_dash": "dashed"}
    ci = hv.Segments(ci_rows, vdims="color").opts(
        color="color", alpha=0.9, show_legend=False, **ci_style
    )

    # 4 elements total, not 4 per column.
    return whiskers * boxes * medians * ci


def _read_stats(
    setting: tp.Optional[str], stats_root: pathlib.Path, input_stem: str, medium: str
) -> dict[str, pl.DataFrame]:
    dfs = {}  # type: tp.Dict[str, pl.DataFrame]

    if setting is None or setting == "none":
        return dfs

    settings = ["conf95", "bw"] if setting == "all" else [setting]

    if setting in settings:
        exts = config.STATS[setting].exts

        for k in exts:
            ipath = stats_root / (input_stem + exts[k])
            if utils.path_exists(ipath):
                dfs[k] = storage.df_read(ipath, medium)
            else:
                _logger.warning("%s not found for '%s'", exts[k], input_stem)

    return dfs


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
