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
import mpl_toolkits.axes_grid1
import pandas as pd
import holoviews as hv

# Project packages
from sierra.core import utils, config, storage, types
from . import pathset

_logger = logging.getLogger(__name__)


def generate(
    paths: pathset.PathSet,
    input_stem: str,
    output_stem: str,
    medium: str,
    title: str,
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    zlabel: tp.Optional[str] = None,
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

    The ``x``,``y`` columns are the indices, and the ``z`` column is the value
    in that cell.

    """

    hv.extension("matplotlib")

    input_fpath = paths.input_root / (input_stem + ext)
    output_fpath = paths.output_root / "HM-{0}.{1}".format(
        output_stem, config.kImageType
    )
    if not utils.path_exists(input_fpath):
        _logger.debug(
            "Not generating <batchroot>/%s: <batchroot>/%s does not exist",
            output_fpath.relative_to(paths.parent.resolve()),
            input_fpath.relative_to(paths.parent.resolve()),
        )
        return False

    # Required arguments
    title = "\n".join(textwrap.wrap(title, 40))

    # Optional arguments
    if large_text:
        text_size = config.kGraphTextSizeLarge
    else:
        text_size = config.kGraphTextSizeSmall

    # Read .csv and create raw heatmap from default configuration
    df = storage.df_read(input_fpath, medium)
    dataset = hv.Dataset(df, kdims=["x", "y"], vdims="z")

    # Transpose if requested
    if transpose:
        dataset.data = dataset.data.transpose()

    # Plot heatmap, without showing the Z-value in each cell
    plot = hv.HeatMap(dataset, kdims=["x", "y"], vdims=["z"]).opts(show_values=False)

    xticks = dataset.data["x"]
    yticks = dataset.data["y"]

    # Add X,Y ticks
    if xticklabels:
        plot.opts(xformatter=lambda x: xticklabels[xticks.index(x)])
    if yticklabels:
        plot.opts(yformatter=lambda y: yticklabels[yticks.index(y)])

    # Add labels
    if xlabel:
        plot.opts(xlabel=xlabel)
    if ylabel:
        plot.opts(ylabel=ylabel)

    # Set fontsizes
    plot.opts(
        fontsize={
            "title": text_size["title"],
            "labels": text_size["xyz_label"],
            "ticks": text_size["tick_label"],
            "legend": text_size["legend_label"],
        }
    )

    # Add title
    plot.opts(title=title)

    # Add colorbar
    plot.opts(colorbar=True)
    if zlabel:
        plot.opts(colorbar_opts={"label": zlabel})

    hv.save(
        plot.opts(fig_inches=config.kGraphBaseSize),
        output_fpath,
        fig=config.kImageType,
        dpi=config.kGraphDPI,
    )
    plt.close("all")

    _logger.debug(
        "Graph written to <batchroot>/%s",
        output_fpath.relative_to(paths.parent.resolve()),
    )
    return True


class DualHeatmap:
    """Generates a side-by-side plot of two heataps from two CSV files.

    ``.mean`` files must be named as ``<input_stem_fpath>_X.mean``, where `X` is
    non-negative integer. Input ``.mean`` files must be 2D grids of the same
    cardinality.

    This graph does not plot standard deviation.

    If there are not exactly two file paths passed, the graph is not generated.

    """

    @staticmethod
    def set_graph_size(df: pd.DataFrame, fig) -> None:
        """
        Set graph X,Y size based on dataframe dimensions.
        """
        if len(df.index) > len(df.columns):
            xsize = config.kGraphBaseSize
            ysize = xsize * float(len(df.index)) / float(len(df.columns))
        else:
            ysize = config.kGraphBaseSize
            xsize = ysize * float(len(df.columns)) / float(len(df.index))

        fig.set_size_inches(xsize, ysize)

    kCardinality = 2

    def __init__(
        self,
        ipaths: types.PathList,
        output_fpath: pathlib.Path,
        title: str,
        xlabel: tp.Optional[str] = None,
        ylabel: tp.Optional[str] = None,
        zlabel: tp.Optional[str] = None,
        large_text: bool = False,
        xtick_labels: tp.Optional[tp.List[str]] = None,
        ytick_labels: tp.Optional[tp.List[str]] = None,
        legend: tp.Optional[tp.List[str]] = None,
    ) -> None:
        self.ipaths = ipaths
        self.output_fpath = output_fpath
        self.title = title

        self.legend = legend
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.zlabel = zlabel

        self.xtick_labels = xtick_labels
        self.ytick_labels = ytick_labels

        # Optional arguments
        if large_text:
            self.text_size = config.kGraphTextSizeLarge
        else:
            self.text_size = config.kGraphTextSizeSmall

        self.logger = logging.getLogger(__name__)

    def generate(self) -> None:
        dfs = [storage.df_read(f, self.medium) for f in self.ipaths]

        if not dfs or len(dfs) != DualHeatmap.kCardinality:
            self.logger.debug(
                ("Not generating dual heatmap: wrong # files " "(must be %s"),
                DualHeatmap.kCardinality,
            )
            return

        # Scaffold graph. We can use either dataframe for setting the graph
        # size; we assume they have the same dimensions.
        #
        fig, axes = plt.subplots(nrows=1, ncols=2)
        DualHeatmap.set_graph_size(dfs[0], fig)

        y = np.arange(len(dfs[0].columns))
        x = dfs[0].index
        ax1, ax2 = axes

        # Find min, max so the shared colorbar makes sense
        minval = min(dfs[0].min().min(), dfs[1].min().min())
        maxval = max(dfs[0].max().max(), dfs[1].max().max())

        # Plot heatmaps
        im1 = ax1.matshow(dfs[0], interpolation="none", vmin=minval, vmax=maxval)
        im2 = ax2.matshow(dfs[1], interpolation="none", vmin=minval, vmax=maxval)

        # Add titles
        fig.suptitle(self.title, fontsize=self.text_size["title"])
        ax1.xaxis.set_ticks_position("bottom")
        ax1.yaxis.set_ticks_position("left")
        ax2.xaxis.set_ticks_position("bottom")
        ax2.yaxis.set_ticks_position("left")

        if self.legend is not None:
            ax1.set_title(
                "\n".join(textwrap.wrap(self.legend[0], 20)),
                size=self.text_size["legend_label"],
            )
            ax2.set_title(
                "\n".join(textwrap.wrap(self.legend[1], 20)),
                size=self.text_size["legend_label"],
            )

        # Add colorbar.
        #
        # Add, then remove the colorbar for the heatmap on the left so that they
        # both end up the same size. Not pythonic, but it works.
        self._plot_colorbar(fig, im1, ax1, remove=True)
        self._plot_colorbar(fig, im2, ax2, remove=False)

        # Add X,Y,Z labels:
        #
        # - X labels are needed on both heatmaps.
        # - Y label only needed on left heatmap.
        self._plot_labels(ax1, xlabel=True, ylabel=True)
        self._plot_labels(ax2, xlabel=True, ylabel=False)

        # Add X,Y ticks:
        #
        # - X tick labels needed on both heatmaps
        # - Y tick labels only needed on left heatmap.
        self._plot_ticks(ax1, x, y, xlabels=True, ylabels=True)
        self._plot_ticks(ax2, x, y, xlabels=True, ylabels=False)

        # Output figures
        fig.subplots_adjust(wspace=0.0, hspace=0.0)
        fig.savefig(self.output_fpath, bbox_inches="tight", dpi=config.kGraphDPI)
        # Prevent memory accumulation (fig.clf() does not close everything)
        plt.close(fig)

    def _plot_colorbar(self, fig, im, ax, remove: bool) -> None:
        """
        Plot the Z-axis color bar on the dual heatmap.
        """
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)

        bar = fig.colorbar(im, cax=cax)
        if remove:
            fig.delaxes(fig.axes[2])

        # p0 = axes[0].get_position().get_points().flatten()
        # p1 = axes[1].get_position().get_points().flatten()
        # ax_cbar = fig.add_axes([p0[0], , p1[2] - p0[0], 0.05])
        # bar = fig.colorbar(im, cax=ax_cbar, orientation='horizontal')

        if self.zlabel is not None:
            bar.ax.set_ylabel(self.zlabel, fontsize=self.text_size["xyz_label"])

    def _plot_ticks(self, ax, xvals, yvals, xlabels: bool, ylabels: bool) -> None:
        """Plot ticks and tick labels.

        If the labels are numerical and the numbers are too large, force
        scientific notation (the ``rcParam`` way of doing this does not seem to
        work...)

        """
        ax.tick_params(labelsize=self.text_size["tick_label"])

        if xlabels:
            ax.set_xticks(yvals)
            ax.set_xticklabels(self.ytick_labels, rotation="vertical")
        else:
            ax.set_xticks([])
            ax.set_xticklabels([])

        if ylabels:
            ax.set_yticks(xvals)
            ax.set_yticklabels(self.xtick_labels, rotation="horizontal")
        else:
            ax.set_yticks([])
            ax.set_yticklabels([])

    def _plot_labels(self, ax, xlabel: bool, ylabel: bool) -> None:
        """
        Plot X,Y axis labels.
        """
        if xlabel:
            ax.set_xlabel(self.ylabel, fontsize=self.text_size["xyz_label"])

        if ylabel:
            ax.set_ylabel(self.xlabel, fontsize=self.text_size["xyz_label"])


__all__ = ["generate", "DualHeatmap"]
