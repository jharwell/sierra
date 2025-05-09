# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
Intra-experiment line graph generation classes for stage{4,5}.
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
    title: str,
    medium: str,
    stats: str = "none",
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    large_text: bool = False,
    legend: tp.Optional[tp.List[str]] = None,
    cols: tp.Optional[tp.List[str]] = None,
    logyscale: bool = False,
    ext=config.kStats["mean"].exts["mean"],
) -> bool:
    """Generate a line graph from a set of columns in a file.

    If the necessary data file does not exist, the graph is not generated.

    If the .stddev file that goes with the .mean does not exist, then no error
    bars are plotted.

    If the .model file that goes with the .mean does not exist, then no model
    predictions are plotted.

    Ideally, model predictions/stddev calculations would be in derived classes,
    but I can't figure out a good way to easily pull that stuff out of here.
    """
    hv.extension("matplotlib")

    # Optional arguments
    if large_text:
        text_size = config.kGraphTextSizeLarge
    else:
        text_size = config.kGraphTextSizeSmall

    input_fpath = paths.input_root / (input_stem + ext)
    output_fpath = paths.output_root / "SLN-{0}.{1}".format(
        output_stem, config.kImageType
    )

    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(paths.parent),
            input_fpath.relative_to(paths.parent),
        )
        return False

    df = storage.df_read(input_fpath, medium)
    dataset = hv.Dataset(
        # Make index a column so we can use it as kdim
        data=df.reset_index(),
        kdims=["index"],
        vdims=cols if cols else df.columns.tolist(),
    )
    model = _read_models(paths.model_root, input_stem, medium)
    stat_dfs = _read_stats(stats, paths.input_root, input_stem, medium)

    # Plot specified columns from dataframe.
    plot = _plot_selected_cols(dataset, model, legend)

    # Plot stats if they have been computed
    if "conf95" in stats and "stddev" in stat_dfs:
        plot *= _plot_stats_stddev(dataset, stat_dfs["stddev"])

    # Plot ticks
    if logyscale:
        plot.opts(logy=True)

    # Let the backend decide # of columns; can override with
    # legend_cols=N in the future if desired.
    plot.opts(legend_position="bottom")

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

    hv.save(
        plot.opts(fig_inches=config.kGraphBaseSize),
        output_fpath,
        fig=config.kImageType,
        dpi=config.kGraphDPI,
    )
    plt.close("all")

    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(paths.parent),
    )
    return True


def _plot_selected_cols(
    dataset: hv.Dataset,
    model_info: models.ModelInfo,
    legend: tp.List[str],
) -> hv.NdOverlay:
    """
    Plot the  selected columns in a dataframe.
    """
    # Always plot the data
    plot = hv.Overlay(
        [
            hv.Curve(
                dataset,
                dataset.kdims[0],
                vdim.name,
                label=legend[dataset.vdims.index(vdim)] if legend else "",
            )
            for vdim in dataset.vdims
        ]
    )
    # Plot the points for each curve
    plot *= hv.Overlay(
        [hv.Points((dataset[dataset.kdims[0]], dataset[v])) for v in dataset.vdims]
    )

    # Plot models if they have been computed
    if model_info.dataset:
        plot *= hv.Overlay(
            [
                hv.Curve(
                    model_info.dataset,
                    model_info.dataset.kdims[0],
                    vdim,
                    label=legend[model_info.dataset.vdims.index(vdim)],
                )
                for vdim in model_info.dataset.vdims
            ]
        )
        # Plot the points for each curve
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


def _plot_stats_stddev(dataset: hv.Dataset, stddev_df: pd.DataFrame) -> hv.NdOverlay:
    """Plot the stddev for a all columns in the dataset."""
    stddevs = pd.DataFrame()
    for c in dataset.vdims:
        stddevs[f"{c}_stddev_l"] = dataset[c] - 2 * stddev_df[c.name].abs()
        stddevs[f"{c}_stddev_u"] = dataset[c] + 2 * stddev_df[c.name].abs()

    # To plot area between lines, you need to add the stddev columns to the
    # dataset
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


def _plot_stats_bw(
    dataset: hv.Dataset, stat_dfs: tp.Dict[str, pd.DataFrame]
) -> hv.NdOverlay:
    """Plot the bw plots for a all columns in the dataset."""
    return hv.Overlay(
        [
            hv.BoxWhisker(dataset.data, dataset.kdims[0], v).opts(
                fig_size=200,
                box_fill_color="skyblue",
                box_line_color="navy",
                title="Box and Whisker Plot by Category",
                xlabel="Category",
                ylabel="Value",
            )
            for v in dataset.vdims
        ]
    )


def _read_stats(
    setting: str, stats_root: pathlib.Path, input_stem: str, medium: str
) -> tp.Dict[str, pd.DataFrame]:
    dfs = {}
    if setting in ["conf95", "bw", "all"]:
        exts = config.kStats["conf95"].exts

        for k in exts:
            ipath = stats_root / (input_stem + exts[k])

            if utils.path_exists(ipath):
                dfs[k] = storage.df_read(ipath, medium)
            else:
                _logger.warning("%sfile not found for '%s'", exts[k], input_stem)

    return dfs


# 2024/09/13 [JRH]: The union is for compatability with type checkers in
# python {3.8,3.11}.
def _read_models(
    model_root: tp.Optional[pathlib.Path], input_stem: str, medium: str
) -> models.ModelInfo:

    if model_root is None:
        return models.ModelInfo()

    modelf = model_root / (input_stem + config.kModelsExt["model"])
    legendf = model_root / (input_stem + config.kModelsExt["legend"])

    if not utils.path_exists(modelf):
        return models.ModelInfo()

    info = models.ModelInfo()
    df = storage.df_read(modelf, medium)
    cols = df.columns.tolist()

    info.dataset = hv.Dataset(data=df.reset_index(), kdims=["index"], vdims=cols)

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
