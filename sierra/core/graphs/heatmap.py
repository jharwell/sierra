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

# Project packages
from sierra.core import utils, config, storage, types
from . import pathset as _pathset

_logger = logging.getLogger(__name__)


def _ofile_ext(backend: str) -> tp.Optional[str]:
    if backend == "matplotlib":
        return config.kStaticImageType
    elif backend == "bokeh":
        return config.kInteractiveImageType

    return None


def generate(
    pathset: _pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    title: str,
    backend: str,
    colnames: tp.Tuple[str, str, str] = ("x", "y", "z"),
    xlabel: tp.Optional[str] = "",
    ylabel: tp.Optional[str] = "",
    zlabel: tp.Optional[str] = "",
    large_text: bool = False,
    xticklabels: tp.Optional[tp.List[str]] = None,
    yticklabels: tp.Optional[tp.List[str]] = None,
    transpose: bool = False,
    ext=config.kStats["mean"].exts["mean"],
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
    hv.extension(backend)

    input_fpath = pathset.input_root / (input_stem + ext)
    output_fpath = pathset.output_root / "HM-{0}.{1}".format(
        output_stem, _ofile_ext(backend)
    )
    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(pathset.batchroot.resolve()),
            input_fpath.relative_to(pathset.batchroot.resolve()),
        )
        return False

    title = "\n".join(textwrap.wrap(title, 40))

    if large_text:
        text_size = config.kGraphs["text_size_large"]
    else:
        text_size = config.kGraphs["text_size_small"]

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

    xticks = dataset.data[colnames[0]]
    yticks = dataset.data[colnames[1]]

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


def _save(plot: hv.Overlay, output_fpath: pathlib.Path, backend: str) -> None:
    if backend == "matplotlib":
        hv.save(
            plot.opts(fig_inches=config.kGraphs["base_size"]),
            output_fpath,
            fig=config.kStaticImageType,
            dpi=config.kGraphs["dpi"],
        )
        plt.close("all")

    elif backend == "bokeh":
        fig = hv.render(plot)
        fig.width = int(config.kGraphs["dpi"] * config.kGraphs["base_size"])
        fig.height = int(config.kGraphs["dpi"] * config.kGraphs["base_size"])
        html = bokeh.embed.file_html(fig, resources=bokeh.resources.INLINE)
        with open(output_fpath, "w") as f:
            f.write(html)


def generate2(
    pathset: _pathset.PathSet,
    ipaths: types.PathList,
    output_stem: pathlib.Path,
    medium: str,
    title: str,
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    zlabel: tp.Optional[str] = None,
    large_text: bool = False,
    xticklabels: tp.Optional[tp.List[str]] = None,
    yticklabels: tp.Optional[tp.List[str]] = None,
) -> bool:
    """Generate a side-by-side plot of two heataps from two CSV files.

    ``.mean`` files must be named as ``<input_stem_fpath>_X.mean``, where `X` is
    non-negative integer. Input ``.mean`` files must be 2D grids of the same
    cardinality.

    This graph does not plot standard deviation.

    If there are not exactly two file paths passed, the graph is not generated.

    """
    hv.extension("matplotlib")

    output_fpath = pathset.output_root / "HM-{0}.{1}".format(
        output_stem, config.kStaticImageType
    )
    # @staticmethod
    # def set_graph_size(df: pd.DataFrame, fig) -> None:
    #     """
    #     Set graph X,Y size based on dataframe dimensions.
    #     """
    #     if len(df.index) > len(df.columns):
    #         xsize = config.kGraphBaseSize
    #         ysize = xsize * float(len(df.index)) / float(len(df.columns))
    #     else:
    #         ysize = config.kGraphBaseSize
    #         xsize = ysize * float(len(df.columns)) / float(len(df.index))

    #     fig.set_size_inches(xsize, ysize)

    # kCardinality = 2

    # Optional arguments
    if large_text:
        text_size = config.kGraphs["text_size_large"]
    else:
        text_size = config.kGraphs["text_size_small"]

    dfs = [storage.df_read(f, medium) for f in ipaths]

    if not dfs or len(dfs) != 2:
        _logger.debug(
            ("Not generating dual heatmap: wrong # files %s (must be 2)"), len(dfs)
        )
        return False

    # Scaffold graph. We can use either dataframe for setting the graph
    # size; we assume they have the same dimensions.
    #
    # fig, axes = plt.subplots(nrows=1, ncols=2)
    # DualHeatmap.set_graph_size(dfs[0], fig)

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
    plot.opts(fig_inches=config.kGraphs["base_size"])

    hv.save(
        plot,
        output_fpath,
        fig=config.kStaticImageType,
        dpi=config.kGraphs["dpi"],
    )
    plt.close("all")

    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(pathset.batchroot),
    )
    return True


__all__ = ["generate", "generate2"]
