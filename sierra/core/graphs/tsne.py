# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""
Intra-experiment 2D t-SNE plot generation for stage{4,5}.
"""

# Core packages
import logging
import typing as tp

# 3rd party packages
import holoviews as hv
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import polars as pl

# Project packages
from sierra.core import config, utils, storage
from . import pathset, graphutils

_logger = logging.getLogger(__name__)


def generate(  # noqa: PLR0913,PLR0917
    pathset: pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    title: str,
    backend: str,
    stats_center: str,
    vcols: list[str],
    labelcol: str,
    perplexity: int,
    target_samples: int,
    *,
    legend: tp.Optional[list[str]] = None,
    large_text: bool = False,
) -> bool:
    """Generate a scatterplot from a set of columns in a file.

    If the necessary data file does not exist, the graph is not generated.

    Parameters:
        pathset: Set of run-time tree paths for the batch experiment.

        input_stem: Stem of the :term:`Batch Summary Data` file to generate a
                    graph from.

        title: Graph title.

        vcols: The columns to use for the datapoint value dimensions.

        labelcol: The column to use for the label of each datapoint.

        perplexity: The perplexity value for the t-SNE plot.

        target_samples: The target # samples (-1 disables).

        stats_center: The measure of centeral tendency to use as the main data
                      input. (from ``--center``).

        backend: The holoviews backend to use.

        large_text: Should the labels, ticks, and titles be large, or regular
                    size?
        legend: The legend for the graph. If ``None``, the categorical label
                values themselves are used (stringified). If supplied, entries
                map positionally to the sorted unique label values and must be
                the same length.

    """
    hv.extension(backend, inline=False, logo=False)

    ofile_ext = graphutils.ofile_ext(backend)

    input_fpath = pathset.input_root / (
        input_stem + config.STATS[stats_center].spreads["none"].exts[stats_center]
    )
    output_fpath = pathset.output_root / f"tSNE-{output_stem}.{ofile_ext}"

    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(pathset.batchroot),
            input_fpath.relative_to(pathset.batchroot),
        )
        return False

    text_size = (
        config.GRAPHS["text_size_large"]
        if large_text
        else config.GRAPHS["text_size_small"]
    )
    df = storage.df_read(input_fpath, medium)

    if target_samples == -1:
        target_samples = len(df)

    total_samples = len(df)
    df = df.sample(n=min(target_samples, len(df)), seed=0)

    _logger.debug("Downsampled from %s -> %s samples", total_samples, len(df))

    unique_labels = sorted(df[labelcol].unique().to_list())

    # Keying the colormap on the display names keeps points and legend swatches
    # in sync.
    if legend is None:
        legend = [str(lab) for lab in unique_labels]

    if len(legend) != len(unique_labels):
        raise ValueError(
            f"legend has {len(legend)} entries but '{labelcol}' has "
            f"{len(unique_labels)} unique values"
        )

    name_map = dict(zip(unique_labels, legend))

    # Colors are keyed on the RAW label value (not the display name), so the
    # points and the legend swatches stay in sync without ever rewriting the
    # label column's dtype. The label column is left untouched: display names
    # are applied only at the overlay `label=` below.
    palette = hv.Cycle().values
    cmap = {lab: palette[i % len(palette)] for i, lab in enumerate(unique_labels)}

    scaled = StandardScaler().fit_transform(df[vcols])

    # Since this is a stochastic algorithm, seed the initial state so t-SNE plot
    # generation is idempotent.
    embedding = TSNE(
        n_components=2, perplexity=min(perplexity, len(df) - 1), random_state=0
    ).fit_transform(scaled)

    # Attach coordinates back so we can split by label
    plot_df = df.with_columns(
        pl.Series("x", embedding[:, 0]),
        pl.Series("y", embedding[:, 1]),
    )

    # One Scatter element per label -> Holoviews emits a categorical legend
    # entry per element. Filtering compares the untouched label column against
    # the raw label value (float-to-float), and coloring/naming both read from
    # the raw-keyed maps above.
    overlays = []
    for lab in unique_labels:
        sub = plot_df.filter(pl.col(labelcol) == lab)
        overlays.append(
            hv.Scatter(
                (sub["x"], sub["y"]),
                kdims=["x"],
                vdims=["y"],
                label=name_map[lab],
            ).opts(
                alpha=0.5,
                color=cmap[lab],
            )
        )

    plot = hv.Overlay(overlays).opts(
        title=title,
        xlabel="",
        ylabel="",
        show_legend=True,
        legend_position="right",
    )
    # Set fontsizes
    plot.opts(
        fontsize={
            "title": text_size["title"],
            "labels": text_size["xyz_label"],
            "ticks": text_size["tick_label"],
            "legend": text_size["legend_label"],
        },
    )

    graphutils.plot_save(plot, output_fpath, backend)

    _logger.debug(
        "Graph written to <batchroot>/%s", output_fpath.relative_to(pathset.batchroot)
    )

    return True


__all__ = ["generate"]
