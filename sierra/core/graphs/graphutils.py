#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#

# Core packages
import pathlib
import typing as tp
import logging

# 3rd party packages
import holoviews as hv
import matplotlib.pyplot as plt
import bokeh
import polars as pl
import numpy as np

# Project packages
from sierra.core import config, utils, storage

_logger = logging.getLogger(__name__)


def plot_save(plot: hv.Overlay, output_fpath: pathlib.Path, backend: str) -> None:
    output_fpath.parent.mkdir(parents=True, exist_ok=True)

    if backend == "matplotlib":
        hv.save(
            plot.opts(fig_inches=config.GRAPHS["fig_size"]),
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
        with utils.utf8open(output_fpath, "w") as f:
            f.write(html)


def ofile_ext(backend: str) -> tp.Optional[str]:
    if backend == "matplotlib":
        return str(config.GRAPHS["static_type"])

    if backend == "bokeh":
        return str(config.GRAPHS["interactive_type"])

    return None


def read_spread_stats(
    center: str, spread: str, stats_root: pathlib.Path, input_stem: str, medium: str
) -> dict[str, pl.DataFrame]:
    dfs = {}  # type: tp.Dict[str, pl.DataFrame]

    exts = config.STATS[center].spreads[spread].exts

    for k in exts:
        ipath = stats_root / (input_stem + exts[k])
        if utils.path_exists(ipath):
            dfs[k] = storage.df_read(ipath, medium)
        else:
            _logger.warning("%s not found for '%s'", exts[k], input_stem)

    return dfs


def plot_stats(
    dataset: hv.Dataset,
    center: str,
    spread: str,
    stat_dfs: dict[str, pl.DataFrame],
    backend: str,
    vdim_color: dict[str, str],
) -> hv.NdOverlay:
    """
    Plot statistics for all lines on the graph.
    """
    plot = _plot_conf95_stats(dataset, center, spread, stat_dfs, backend, vdim_color)
    plot *= _plot_bw_stats(dataset, center, spread, stat_dfs, backend, vdim_color)
    plot *= _plot_iqr_stats(dataset, center, spread, stat_dfs, backend, vdim_color)

    return plot


def build_color_map(
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


def _plot_conf95_stats(
    dataset: hv.Dataset,
    center: str,
    spread: str,
    stat_dfs: dict[str, pl.DataFrame],
    backend: str,
    vdim_color: dict[str, str],
) -> hv.NdOverlay:
    if center != "mean" or spread != "conf95":
        return hv.Overlay()

    if not all(k in stat_dfs for k in config.STATS["mean"].spreads["conf95"].exts):
        _logger.warning(
            (
                "Cannot plot 95%% confidence intervals: missing some "
                "statistics %s vs %s"
            ),
            stat_dfs.keys(),
            config.STATS["mean"].spreads["conf95"].exts,
        )
        return hv.Overlay()

    # Build stddev columns
    stddev_cols = {}
    for c in dataset.vdims:
        stddev_vals = stat_dfs["stddev"][c.name].abs().to_numpy()
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


def _plot_bw_stats(
    dataset: hv.Dataset,
    center: str,
    spread: str,
    stat_dfs: dict[str, pl.DataFrame],
    backend: str,
    vdim_color: dict[str, str],
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
    if center != "mean" or spread != "bw":
        return hv.Overlay()

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


def _plot_iqr_stats(
    dataset: hv.Dataset,
    center: str,
    spread: str,
    stat_dfs: dict[str, pl.DataFrame],
    backend: str,
    vdim_color: dict[str, str],
) -> hv.NdOverlay:
    if center != "median" or spread != "iqr":
        return hv.Overlay()

    if not all(k in stat_dfs for k in config.STATS["median"].spreads["iqr"].exts):
        _logger.warning(
            ("Cannot plot IQR intervals: missing some statistics: %s vs %s"),
            stat_dfs.keys(),
            config.STATS["median"].spreads["iqr"].exts,
        )
        return hv.Overlay()

    # Build iqr columns
    cols = {}
    for c in dataset.vdims:
        cols[f"{c}_q1"] = dataset.data[c.name] - stat_dfs["q1"][c.name].to_numpy()
        cols[f"{c}_q3"] = dataset.data[c.name] + stat_dfs["q3"][c.name].to_numpy()

    # Add columns to dataset
    for col_name, col_data in cols.items():
        dataset.data[col_name] = col_data

    fill_key = "facecolor" if backend == "matplotlib" else "fill_color"
    return hv.Overlay(
        [
            hv.Area(dataset, vdims=[f"{vdim.name}_q1", f"{vdim.name}_q3"]).opts(
                alpha=0.5, **{fill_key: vdim_color[vdim.name]}
            )
            for vdim in dataset.vdims
        ]
    )
