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
import bokeh
import pandas as pd
from pandas.api.types import CategoricalDtype

# Project packages
from sierra.core import utils, config, storage, types
from . import pathset as _pathset

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
    xlabels_rotate: bool = False,
    large_text: bool = False,
) -> bool:
    """
    Generate a confusion matrix from a ``.mean`` file.

    If the necessary ``.mean`` file does not exist, the graph is not generated.
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

    ofile_ext = _ofile_ext(backend)
    input_fpath = pathset.input_root / (input_stem + config.STATS["mean"].exts["mean"])
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
    confusion_df = (
        df.groupby([truth_col, predicted_col], observed=False)
        .size()
        .reset_index(name="count")
    )

    # Get category names. Need union in case the sets aren't the same.
    categories = sorted(set(df[truth_col].unique()) | set(df[predicted_col].unique()))

    # We need to use pandas' categorical datatypes here to ensure the same
    # ordering of categories on both axes for a true confusion matrix.
    cat_type = CategoricalDtype(categories=categories, ordered=True)
    confusion_df[truth_col] = confusion_df[truth_col].astype(cat_type)
    confusion_df[predicted_col] = confusion_df[predicted_col].astype(cat_type)

    # Fill in missing combinations with 0.0 to avoid duplicate/missing index
    # issues.
    all_combinations = pd.MultiIndex.from_product(
        [categories, categories], names=[truth_col, predicted_col]
    ).to_frame(index=False)
    all_combinations[truth_col] = all_combinations[truth_col].astype(cat_type)
    all_combinations[predicted_col] = all_combinations[predicted_col].astype(cat_type)
    confusion_df = all_combinations.merge(
        confusion_df,
        on=[truth_col, predicted_col],
        how="left",
    )

    confusion_df["count"] = confusion_df["count"].fillna(0)

    # Normalize by row to get fractions rather than counts, which are generally
    # more useful.
    row_totals = confusion_df.groupby(truth_col, observed=False)["count"].transform(
        "sum"
    )
    confusion_df["fraction"] = confusion_df["count"] / row_totals

    # Convert categorical back to string to avoid HoloViews internal warnings
    confusion_df[truth_col] = confusion_df[truth_col].astype(str)
    confusion_df[predicted_col] = confusion_df[predicted_col].astype(str)
    dataset = hv.Dataset(
        confusion_df, kdims=[predicted_col, truth_col], vdims="fraction"
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

    _save(plot, output_fpath, backend)

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
    ext=config.STATS["mean"].exts["mean"],
) -> bool:
    """
    Generate a X vs. Y vs. Z heatmap plot of a ``.mean`` file.

    If the necessary ``.mean`` file does not exist, the graph is not generated.
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

    ofile_ext = _ofile_ext(backend)
    input_fpath = pathset.input_root / (input_stem + ext)
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
    dataset = hv.Dataset(df, kdims=[colnames[0], colnames[1]], vdims=colnames[2])

    # Transpose if requested
    if transpose:
        dataset.data = dataset.data.transpose()

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

    _save(plot, output_fpath, backend)

    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(pathset.batchroot),
    )
    return True


def generate_dual_numeric(  # noqa: PLR0913
    pathset: _pathset.PathSet,
    ipaths: types.PathList,
    output_stem: pathlib.Path,
    medium: str,
    title: str,
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    zlabel: tp.Optional[str] = None,
    large_text: bool = False,
    xticklabels: tp.Optional[list[str]] = None,
    yticklabels: tp.Optional[list[str]] = None,
) -> bool:
    """Generate a side-by-side plot of two heataps from two CSV files.

    ``.mean`` files must be named as ``<input_stem_fpath>_X.mean``, where `X` is
    non-negative integer. Input ``.mean`` files must be 2D grids of the same
    cardinality.

    This graph does not plot standard deviation.

    If there are not exactly two file paths passed, the graph is not generated.

    """
    hv.extension("matplotlib", inline=False, logo=False)

    output_fpath = (
        pathset.output_root / f"HM-{output_stem}.{config.GRAPHS['static_type']}"
    )

    # Optional arguments
    text_size = (
        config.GRAPHS["text_size_large"]
        if large_text
        else config.GRAPHS["text_size_small"]
    )

    dfs = [storage.df_read(f, medium) for f in ipaths]

    if not dfs or len(dfs) != 2:
        _logger.debug(
            ("Not generating dual heatmap: wrong # files %s (must be 2)"), len(dfs)
        )
        return False

    yticks = np.arange(len(dfs[0].columns))
    xticks = dfs[0].index

    # Plot heatmaps
    plot = hv.Image(dfs[0]) + hv.Image(dfs[1])

    # Add X,Y ticks
    if xticklabels:
        plot.opts(xformatter=lambda x: xticklabels[xticks.index(x)])
    if yticklabels:
        plot.opts(yformatter=lambda y: yticklabels[yticks.index(y)])

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

    # Add colorbar.
    plot.opts(
        hv.opts.Layout(shared_axes=False),
        hv.opts.Image(
            colorbar=True,
            colorbar_position="right",
            backend_opts={"colorbar.label": zlabel},
        ),
    )

    # Output figures
    plot.opts(fig_inches=config.GRAPHS["base_size"])

    hv.save(
        plot,
        output_fpath,
        fig=config.GRAPHS["static_type"],
        dpi=config.GRAPHS["dpi"],
    )
    plt.close("all")

    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(pathset.batchroot),
    )
    return True


def _ofile_ext(backend: str) -> tp.Optional[str]:
    if backend == "matplotlib":
        return str(config.GRAPHS["static_type"])

    if backend == "bokeh":
        return str(config.GRAPHS["interactive_type"])

    return None


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


__all__ = ["generate_confusion", "generate_dual_numeric", "generate_numeric"]
