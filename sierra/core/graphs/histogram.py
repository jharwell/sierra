# Copyright 2026 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
Intra-experiment histograph generation for stage{4,5}.
"""

# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages
import polars as pl
import holoviews as hv
import matplotlib.pyplot as plt
import bokeh

# Project packages
from sierra.core import config, utils, storage
from . import pathset, graphutils

_logger = logging.getLogger(__name__)


def generate(  # noqa: PLR0913
    pathset: pathset.PathSet,
    input_stem: str,
    output_stem: str,
    title: str,
    medium: str,
    backend: str,
    cols: tp.Optional[list[str]],
    kind: str,
    bins: tp.Optional[str] = None,
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    legend: tp.Optional[list[str]] = None,
    large_text: bool = False,
) -> bool:
    """Generate a histogram from one or more columns in a file.

    If the necessary data file does not exist, the graph is not generated.

    All columns are binned over a shared range so that bins line up and the
    distributions are directly comparable.

    """
    hv.extension(backend, inline=False, logo=False)

    input_fpath = pathset.input_root / (input_stem + config.STATS["mean"].exts["mean"])
    output_fpath = pathset.output_root / "HG-{}.{}".format(
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

    # Normalize to a list so the single- and multi-column cases share a code
    # path.
    selected = cols if cols else list(df.columns)

    missing = [c for c in selected if c not in df.columns]
    if missing:
        _logger.error(
            "Not generating <batchroot>/%s: column(s) %s not in <batchroot>/%s",
            output_fpath.relative_to(pathset.batchroot),
            missing,
            input_fpath.relative_to(pathset.batchroot),
        )
        return False

    num_bins = int(bins) if bins is not None else None
    bin_range = _shared_bin_range(df, selected)

    # holoviews has no polars interface, so each column is handed over as a
    # numpy array. For a non-null numeric column this is zero-copy.
    hists = {
        c: _histogram(hv.Dataset(df[c].to_numpy(), c), num_bins, bin_range)
        for c in selected
    }
    labels = _build_labels(selected, legend)

    if kind == "overlay":
        plot = _plot_overlay(hists, labels)
    elif kind == "steps":
        plot = _plot_steps(hists, labels)
    else:
        plot = _plot_facet(hists, labels, text_size)

    # Let the backend decide # of columns; can override with
    # legend_cols=N in the future if desired.
    #
    # 2026-07-22 [JRH]: Faceting puts each column in its own subplot, so there
    # is nothing for a legend to disambiguate.
    if kind != "facet":
        plot.opts(legend_position="bottom")

    # Add title
    plot.opts(title=title)

    # Add X,Y labels.
    #
    # 2026-07-22 [JRH]: NdLayout rejects xlabel/ylabel at the container level,
    # so for faceting they have to be pushed down onto the constituent
    # elements. Doing it that way unconditionally works for all 3 kinds.
    label_opts = {}  # type: tp.Dict[str, str]

    if xlabel is not None:
        label_opts["xlabel"] = xlabel

    if ylabel is not None:
        label_opts["ylabel"] = ylabel

    if label_opts:
        element = "Curve" if kind == "steps" else "Histogram"
        plot = plot.opts(getattr(hv.opts, element)(**label_opts))

    # Set fontsizes
    plot.opts(
        fontsize={
            "title": text_size["title"],
            "labels": text_size["xyz_label"],
            "ticks": text_size["tick_label"],
            "legend": text_size["legend_label"],
        },
    )

    graphutils.save_plot(plot, output_fpath, backend)
    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(pathset.batchroot),
    )
    return True


def _shared_bin_range(
    df: pl.DataFrame, cols: list[str]
) -> tp.Optional[tuple[float, float]]:
    """Compute a bin range spanning all selected columns.

    Without this each column would be binned over its own min/max, so bins
    would not line up between columns and the histograms would not be
    comparable.
    """
    mins = [df[c].min() for c in cols]
    maxs = [df[c].max() for c in cols]

    if any(m is None for m in mins + maxs):
        # All-null column; let holoviews decide.
        return None

    mins_f = tp.cast(list[float], mins)
    maxs_f = tp.cast(list[float], maxs)
    lo, hi = min(mins_f), max(maxs_f)

    if lo == hi:
        # Constant data; a zero-width range is not a valid set of bins.
        return None

    return (float(lo), float(hi))


def _histogram(
    dataset: hv.Dataset,
    num_bins: tp.Optional[int],
    bin_range: tp.Optional[tuple[float, float]],
) -> hv.Histogram:
    """Bin a single dataset into a :class:`~holoviews.Histogram`."""
    kwargs = {}  # type: tp.Dict[str, tp.Any]

    if num_bins is not None:
        kwargs["num_bins"] = num_bins

    if bin_range is not None:
        kwargs["bin_range"] = bin_range

    return hv.operation.histogram(dataset, **kwargs)


def _build_labels(cols: list[str], legend: tp.Optional[list[str]]) -> dict[str, str]:
    """Map each column to its display label, defaulting to the column name."""
    if legend is None:
        return {c: c for c in cols}

    if len(legend) != len(cols):
        _logger.warning(
            "Legend length mismatch: %d labels for %d columns; using column names",
            len(legend),
            len(cols),
        )
        return {c: c for c in cols}

    return dict(zip(cols, legend))


def _plot_overlay(hists: dict[str, hv.Histogram], labels: dict[str, str]) -> hv.Overlay:
    """Plot all columns on shared axes as translucent filled histograms."""
    return hv.Overlay([hists[c].relabel(labels[c]).opts(alpha=0.55) for c in hists])


def _plot_steps(hists: dict[str, hv.Histogram], labels: dict[str, str]) -> hv.Overlay:
    """Plot all columns on shared axes as outline-only step curves.

    Reuses the bin centers/counts already computed by
    :func:`holoviews.operation.histogram` rather than re-binning.
    """
    return hv.Overlay(
        [
            hv.Curve(
                (hists[c].dimension_values(0), hists[c].dimension_values(1)),
                label=labels[c],
            ).opts(interpolation="steps-mid")
            for c in hists
        ]
    )


def _plot_facet(
    hists: dict[str, hv.Histogram], labels: dict[str, str], text_size: dict
) -> hv.NdLayout:
    """Plot each column into its own subplot."""
    ncols = min(len(hists), 2)
    fontsize = {
        "title": text_size["title"],
        "labels": text_size["xyz_label"],
        "ticks": text_size["tick_label"],
        "legend": text_size["legend_label"],
    }

    # You have to set the font sizes on each sub-plot/sub-histogram, because
    # setting it on the NdLayout and/or the overall plot has no effect.
    return hv.NdLayout(
        {labels[c]: hists[c].opts(fontsize=fontsize) for c in hists},
        kdims="column",
    ).cols(ncols)


__all__ = ["generate"]
