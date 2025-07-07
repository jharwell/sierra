# Copyright 2018 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""
Linegraph for summarizing the results of a :term:`Batch Experiment`.

Graphs one datapoint per :term:`Experiment`.
"""

# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages
import pandas as pd
import holoviews as hv
import matplotlib.pyplot as plt

# Project packages
from sierra.core import config, utils, storage, models
from . import pathset

_logger = logging.getLogger(__name__)


def generate(
    paths: pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    title: str,
    xlabel: str,
    ylabel: str,
    legend: tp.List[str],
    xticks: tp.List[float],
    xticklabels: tp.Optional[tp.List[str]] = None,
    large_text: bool = False,
    logyscale: bool = False,
    stats: str = "none",
) -> bool:
    """Generate a linegraph from a :term:`Batch Summary Data` file.

    Possibly shows the 95% confidence interval or box and whisker plots,
    according to configuration.

    Attributes:
        paths: Set of run-time tree paths for the batch experiment.

        input_stem: Stem of the :term:`Batch Summary Data` file to generate a
                    graph from.

        output_fpath: The absolute path to the output image file to save
                      generated graph to.

        title: Graph title.

        xlabel: X-label for graph.

        ylabel: Y-label for graph.

        xticks: The xticks for the graph.

        xticklabels: The xtick labels for the graph (can be different than the
                      xticks; e.g., if the xticxs are 1-10 for categorical data,
                      then then labels would be the categories).

        large_text: Should the labels, ticks, and titles be large, or regular
                    size?

        legend: Legend for graph.

        logyscale: Should the Y axis be in the log2 domain ?

        stats: The type of statistics to include on the graph (from
               ``--dist-stats``).

        model_root: The absolute path to the ``models/`` directory for the batch
                     experiment.

    """
    hv.extension("matplotlib")
    # Optional arguments
    if large_text:
        text_size = config.kGraphTextSizeLarge
    else:
        text_size = config.kGraphTextSizeSmall

    input_fpath = paths.input_root / (input_stem + config.kStats["mean"].exts["mean"])
    output_fpath = paths.output_root / (
        "SM-{0}.{1}".format(output_stem, config.kImageType)
    )

    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(paths.batchroot),
            input_fpath.relative_to(paths.batchroot),
        )
        return False

    df = storage.df_read(input_fpath, medium, index_col="Experiment ID")
    # Column 0 is the 'Experiment ID' index, which we don't want included as
    # a vdim
    cols = df.columns.tolist()
    df["xticks"] = xticks

    dataset = hv.Dataset(data=df.reset_index(), kdims=["xticks"], vdims=cols)
    assert len(df.index) == len(
        xticks
    ), "Length mismatch between xticks,# data points: {0} vs {1}".format(
        len(xticks), len(df.index)
    )

    model_info = _read_model_info(paths.model_root, input_stem, medium, xticks)

    # Add statistics according to configuration
    stat_dfs = _read_stats(stats, medium, paths.input_root, input_stem)
    plot = _plot_stats(dataset, stats, stat_dfs)

    # Add legend
    plot.opts(legend_position="bottom")

    # Plot lines after stats so they show on top
    plot *= _plot_lines(dataset, model_info, legend)

    # Add X,Y labels
    plot.opts(ylabel=ylabel, xlabel=xlabel)

    # Configure ticks (must be last so not overwritten by what you get from
    # plotting the lines)
    plot = _plot_ticks(plot, logyscale, xticks, xticklabels)

    # Set fontsizes
    plot.opts(
        fontsize={
            "title": text_size["title"],
            "labels": text_size["xyz_label"],
            "ticks": text_size["tick_label"],
            "legend": text_size["legend_label"],
        },
    )

    # Add title
    plot.opts(title=title)

    hv.save(
        plot.opts(fig_inches=config.kGraphBaseSize),
        output_fpath,
        fig=config.kImageType,
        dpi=config.kGraphDPI,
    )
    plt.close("all")

    _logger.debug(
        "Graph written to <batchroot>/%s", output_fpath.relative_to(paths.batchroot)
    )

    return True


def _plot_lines(
    dataset: hv.Dataset, model_info: models.ModelInfo, legend: tp.List[str]
) -> hv.NdOverlay:
    # Plot the curve(s)
    plot = hv.Overlay(
        [
            hv.Curve(
                dataset,
                kdims=dataset.kdims[0],
                vdims=vdim,
                label=legend[dataset.vdims.index(vdim)],
            )
            for vdim in dataset.vdims
        ]
    )

    # Plot the points for each curve
    plot *= hv.Overlay(
        [hv.Points((dataset[dataset.kdims[0]], dataset[v])) for v in dataset.vdims]
    )

    if model_info.dataset:
        # TODO: This currently only works for a single model being put onto a
        # summary line graph.
        plot *= hv.Overlay(
            [
                hv.Curve(
                    model_info.dataset,
                    kdims=dataset.kdims[0],
                    vdims=dataset.vdims,
                    label=model_info.legend[0],
                )
            ]
        )
        plot *= hv.Overlay(
            [
                hv.Points(
                    (
                        model_info.dataset[model_info.dataset.kdims[0]],
                        model_info.dataset[v],
                    )
                )
                for v in model_info.dataset.vdims
            ]
        )
    return plot


def _plot_stats(
    dataset: hv.Dataset, setting: str, stat_dfs: tp.Dict[str, pd.DataFrame]
) -> hv.NdOverlay:
    """
    Plot statistics for all lines on the graph.
    """
    plot = _plot_conf95_stats(dataset, setting, stat_dfs)
    plot *= _plot_bw_stats(dataset, setting, stat_dfs)

    return plot


def _plot_conf95_stats(
    dataset: hv.Dataset, setting: str, stat_dfs: tp.Dict[str, pd.DataFrame]
) -> hv.NdOverlay:
    if setting not in ["conf95", "all"]:
        return hv.Overlay()

    if not all(k in stat_dfs.keys() for k in config.kStats["conf95"].exts):
        _logger.warning(
            (
                "Cannot plot 95%% confidence intervals: "
                "missing some statistics: %s vs %s"
            ),
            stat_dfs.keys(),
            config.kStats["conf95"].exts,
        )
        return hv.Overlay()

    # Stddevs have to be added to dataset to be able to plot via overlays,
    # afaict.
    stddevs = pd.DataFrame()

    for c in dataset.vdims:
        stddevs[f"{c}_stddev_l"] = dataset[c] - 2 * stat_dfs["stddev"][c.name].abs()
        stddevs[f"{c}_stddev_u"] = dataset[c] + 2 * stat_dfs["stddev"][c.name].abs()
    stddevs.index = dataset.data.index
    dataset.data = pd.concat([dataset.dframe(), stddevs], axis=1)

    return hv.Overlay(
        [
            hv.Area(
                dataset, vdims=[f"{vdim.name}_stddev_l", f"{vdim.name}_stddev_u"]
            ).opts(
                alpha=0.5,
            )
            for vdim in dataset.vdims
        ]
    )


def _plot_bw_stats(
    dataset: hv.Dataset, setting: str, stat_dfs: tp.Dict[str, pd.DataFrame]
) -> hv.NdOverlay:
    if setting not in ["bw", "all"]:
        return hv.Overlay()

    if not all(k in stat_dfs.keys() for k in config.kStats["bw"].exts):
        _logger.warning(
            ("Cannot plot box-and-whisker plots: " "missing some statistics: %s vs %s"),
            stat_dfs.keys(),
            config.kStats["bw"].exts,
        )
        return hv.Overlay()

    elements = []

    # For each value dimension (set of datapoints from a batch experiment)
    for i in range(0, len(dataset.vdims)):

        # For each datapoint captured from an experiment in the batch
        for j in range(0, len(dataset.data.values)):
            col = dataset.vdims[i].name

            # Read stats from file
            q1 = stat_dfs["q1"][col].iloc[j]
            median = stat_dfs["median"][col].iloc[j]
            q3 = stat_dfs["q3"][col].iloc[j]
            whishi = stat_dfs["whislo"][col].iloc[j]
            whislo = stat_dfs["whishi"][col].iloc[j]

            # Box (Rectangle from q1 to q3).
            # Args: x center, y center, x width, y height
            box = hv.Box(dataset.data["xticks"][j], median, (0.2, (q3 - q1))).opts(
                linewidth=2
            )

            # Median line
            median_line = hv.Segments(
                (
                    dataset.data["xticks"][j] - 0.2,
                    median,
                    dataset.data["xticks"][j] + 0.2,
                    median,
                )
            ).opts(color="darkred", linewidth=2)

            # Whisker lines (vertical lines from box to min/max)
            lower_whisker = hv.Segments(
                (dataset.data["xticks"][j], q1, dataset.data["xticks"][j], whislo)
            ).opts(color="black", linewidth=2)
            upper_whisker = hv.Segments(
                (dataset.data["xticks"][j], q3, dataset.data["xticks"][j], whishi)
            ).opts(color="black", linewidth=2)

            # Whisker caps (horizontal lines at min/max)
            lower_cap = hv.Segments(
                (
                    dataset.data["xticks"][j] - 0.1,
                    whislo,
                    dataset.data["xticks"][j] + 0.1,
                    whislo,
                )
            ).opts(color="black", linewidth=2)
            upper_cap = hv.Segments(
                (
                    dataset.data["xticks"][j] - 0.1,
                    whishi,
                    dataset.data["xticks"][j] + 0.1,
                    whishi,
                )
            ).opts(color="black", linewidth=2)
            # Combine all elements
            elements.append(
                box
                * median_line
                * lower_whisker
                * upper_whisker
                * lower_cap
                * upper_cap
            )

    return hv.Overlay(elements)


def _plot_ticks(
    plot: hv.NdOverlay,
    logyscale: bool,
    xticks: tp.List[float],
    xticklabels: tp.List[str],
) -> hv.NdOverlay:
    if logyscale:
        plot.opts(logy=True)

    # For ordered, qualitative data
    if xticklabels is not None:
        plot.opts(xticks=[(i, j) for i, j in zip(xticks, xticklabels)], xrotation=90)

    return plot


def _read_stats(
    setting: str, medium: str, stats_root: pathlib.Path, input_stem: str
) -> tp.Dict[str, tp.List[pd.DataFrame]]:
    dfs = {}

    dfs.update(_read_conf95_stats(setting, medium, stats_root, input_stem))
    dfs.update(_read_bw_stats(setting, medium, stats_root, input_stem))

    return dfs


def _read_conf95_stats(
    setting: str,
    medium: str,
    stats_root: pathlib.Path,
    input_stem: str,
) -> tp.Dict[str, tp.List[pd.DataFrame]]:
    dfs = {}

    exts = config.kStats["conf95"].exts
    if setting in ["conf95", "all"]:
        for k in exts:
            ipath = stats_root / (input_stem + exts[k])

            if utils.path_exists(ipath):
                dfs[k] = storage.df_read(ipath, medium, index_col="Experiment ID")
            else:
                _logger.warning("%s file not found for '%s'", exts[k], input_stem)

    return dfs


def _read_bw_stats(
    setting: str,
    medium: str,
    stats_root: pathlib.Path,
    input_stem: str,
) -> tp.Dict[str, tp.List[pd.DataFrame]]:
    dfs = {}

    exts = config.kStats["bw"].exts

    if setting in ["bw", "all"]:
        for k in exts:
            ipath = stats_root / (input_stem + exts[k])

            if utils.path_exists(ipath):
                dfs[k] = storage.df_read(ipath, medium, index_col="Experiment ID")
            else:
                _logger.warning("%s file not found for '%s'", exts[k], input_stem)

    return dfs


# 2024/09/13 [JRH]: The union is for compatability with type checkers in
# python {3.8,3.11}.
def _read_model_info(
    model_root: tp.Optional[pathlib.Path],
    input_stem: str,
    medium: str,
    xticks: tp.List[float],
) -> models.ModelInfo:

    if model_root is None:
        return models.ModelInfo()

    _logger.trace("Model root='%s'", model_root)  # type: ignore

    exts = config.kModelsExt
    modelf = model_root / (input_stem + exts["model"])
    legendf = model_root / (input_stem + exts["legend"])

    if not utils.path_exists(modelf):
        _logger.trace(
            "No model file=<batch_model_root>/%s found",
            modelf.relative_to(model_root),
        )  # type: ignore
        return models.ModelInfo()

    info = models.ModelInfo()

    df = storage.df_read(modelf, medium, index_col="Experiment ID")

    # Column 0 is the 'Experiment ID' index, which we don't want included as
    # a vdim
    cols = df.columns.tolist()
    df["xticks"] = xticks

    info.dataset = hv.Dataset(data=df.reset_index(), kdims=["xticks"], vdims=cols)

    if utils.path_exists(legendf):
        with utils.utf8open(legendf, "r") as f:
            info.legend = f.read().splitlines()
    else:
        _logger.warning(
            "No legend file=<batch_model_root>/%s found",
            legendf.relative_to(model_root),
        )
        info.legend = ["Model Prediction"]

    _logger.trace(
        "Loaded model='%s',legend='%s'",  # type: ignore
        modelf.relative_to(model_root),
        legendf.relative_to(model_root),
    )

    return info


__all__ = ["generate"]
