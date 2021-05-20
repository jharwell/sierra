# Copyright 2018 John Harwell, All rights reserved.
#
#  This file is part of SIERRA.
#
#  SIERRA is free software: you can redistribute it and/or modify it under the
#  terms of the GNU General Public License as published by the Free Software
#  Foundation, either version 3 of the License, or (at your option) any later
#  version.
#
#  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
#  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
#  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with
#  SIERRA.  If not, see <http://www.gnu.org/licenses/
#

# Core packages
import os
import textwrap
import logging
import glob
import re
import typing as tp

# 3rd party packages
import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1
import pandas as pd

# Project packages
import sierra.core.utils
import sierra.core.config


class Heatmap:
    """
    Generates a X vs. Y vs. Z heatmap plot of a dataframe in the specified .csv file.

    If the necessary .csv file does not exist, the graph is not generated.

    """

    def __init__(self,
                 input_fpath: str,
                 output_fpath: str,
                 title: str,
                 xlabel: str,
                 ylabel: str,
                 large_text: bool = False,
                 xtick_labels: tp.Optional[tp.List[str]] = None,
                 ytick_labels: tp.Optional[tp.List[str]] = None,
                 transpose: bool = False,
                 zlabel: tp.Optional[str] = None,
                 interpolation: str = 'nearest') -> None:
        # Required arguments
        self.input_fpath = input_fpath
        self.output_fpath = output_fpath
        self.title = '\n'.join(textwrap.wrap(title, 40))
        self.xlabel = xlabel if transpose else ylabel
        self.ylabel = ylabel if transpose else xlabel

        # Optional arguments
        if large_text:
            self.text_size = sierra.core.config.kGraphTextSizeLarge
        else:
            self.text_size = sierra.core.config.kGraphTextSizeSmall

        self.transpose = transpose
        self.zlabel = zlabel
        self.interpolation = interpolation

        if not self.transpose:
            self.xtick_labels = ytick_labels
            self.ytick_labels = xtick_labels
        else:
            self.xtick_labels = xtick_labels
            self.ytick_labels = ytick_labels

        self.logger = logging.getLogger(__name__)

    def generate(self) -> None:
        if not sierra.core.utils.path_exists(self.input_fpath):
            self.logger.debug("Not generating heatmap: %s does not exist", self.input_fpath)
            return

        # Read .csv and create raw heatmap from default configuration
        data_df = sierra.core.utils.pd_csv_read(self.input_fpath)
        self._plot_df(data_df, self.output_fpath)

    def _plot_df(self, df: pd.DataFrame, opath: str) -> None:
        fig, ax = plt.subplots(figsize=(sierra.core.config.kGraphBaseSize, sierra.core.config.kGraphBaseSize))

        # Transpose if requested
        if self.transpose:
            df = df.transpose()

        # Plot heatmap
        plt.imshow(df, cmap='coolwarm', interpolation=self.interpolation, aspect='auto')

        # Add labels
        plt.xlabel(self.xlabel, fontsize=self.text_size['xyz_label'])
        plt.ylabel(self.ylabel, fontsize=self.text_size['xyz_label'])

        # Add X,Y ticks
        self._plot_ticks(ax)

        # Add graph title
        plt.title(self.title, fontsize=self.text_size['title'])

        # Add colorbar
        self._plot_colorbar(ax)

        # Output figure
        self._set_graph_size(df, fig)
        fig = ax.get_figure()

        fig.savefig(opath, bbox_inches='tight', dpi=sierra.core.config.kGraphDPI)
        plt.close(fig)  # Prevent memory accumulation (fig.clf() does not close everything)

    def _set_graph_size(self, df: pd.DataFrame, fig) -> None:
        if len(df.index) > len(df.columns):
            xsize = sierra.core.config.kGraphBaseSize
            ysize = xsize * float(len(df.index)) / float(len(df.columns))
        else:
            ysize = sierra.core.config.kGraphBaseSize
            xsize = ysize * float(len(df.columns)) / float(len(df.index))

        fig.set_size_inches(xsize, ysize)

    def _plot_colorbar(self, ax) -> None:
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.05)
        bar = plt.colorbar(cax=cax)

        if self.zlabel is not None:
            bar.ax.set_ylabel(self.zlabel)

    def _plot_ticks(self, ax) -> None:
        ax.tick_params(labelsize=self.text_size['tick_label'])

        if self.xtick_labels is not None:
            ax.set_xticks(np.arange(len(self.xtick_labels)))
            ax.set_xticklabels(self.xtick_labels, rotation='vertical')

        if self.ytick_labels is not None:
            ax.set_yticks(np.arange(len(self.ytick_labels)))
            ax.set_yticklabels(self.ytick_labels)


class DualHeatmap:
    """
    Generates a side-by-side plot of two heataps from a set of .csv files with the specified
    graph visuals. .csv files must be named as``<input_stem_fpath>_X.csv``, where `X` is
    non-negative integer. Input ``.csv`` files must be 2D grids of the same cardinality.

    This graph does not plot standard deviation.

    If there are not exactly two  ``.csv`` files matching the pattern found, the graph is not
    generated.
    """
    kCardinality = 2

    def __init__(self, **kwargs) -> None:

        self.input_stem_pattern = os.path.abspath(kwargs['input_stem_pattern'])
        self.output_fpath = kwargs['output_fpath']
        self.title = kwargs['title']
        self.legend = kwargs.get('legend', None)
        self.zlabel = kwargs['zlabel']

        self.xlabel = kwargs.get('xlabel', None)
        self.ylabel = kwargs.get('ylabel', None)
        self.xtick_labels = kwargs.get('xtick_labels', None)
        self.ytick_labels = kwargs.get('ytick_labels', None)

        # Optional arguments
        if kwargs.get('large_text', False):
            self.text_size = sierra.core.config.kGraphTextSizeLarge
        else:
            self.text_size = sierra.core.config.kGraphTextSizeSmall

        self.logger = logging.getLogger(__name__)

    def generate(self) -> None:
        dfs = [sierra.core.utils.pd_csv_read(f) for f in glob.glob(
            self.input_stem_pattern + '*.csv') if re.search('_[0-9]+', f)]

        if not dfs or len(dfs) != DualHeatmap.kCardinality:
            self.logger.debug("Not generating dual heatmap graph: %s did not match %s .csv files",
                              self.input_stem_pattern, DualHeatmap.kCardinality)
            return

        # Scaffold graph
        fig, axes = plt.subplots(ncols=2,
                                 figsize=(sierra.core.config.kGraphBaseSize * 2.0,
                                          sierra.core.config.kGraphBaseSize))
        y = np.arange(len(dfs[0].columns))
        x = dfs[0].index
        ax1, ax2 = axes

        # Find min, max so the shared colorbar makes sense
        minval = min(dfs[0].min().min(), dfs[1].min().min())
        maxval = max(dfs[0].max().max(), dfs[1].max().max())

        # Plot heatmaps
        im1 = ax1.matshow(dfs[0], cmap='coolwarm', interpolation='none', vmin=minval, vmax=maxval)
        im2 = ax2.matshow(dfs[1], cmap='coolwarm', interpolation='none', vmin=minval, vmax=maxval)

        # Add titles
        fig.suptitle(self.title, fontsize=self.text_size['title'])
        ax1.xaxis.set_ticks_position('bottom')
        ax1.yaxis.set_ticks_position('left')
        ax2.xaxis.set_ticks_position('bottom')
        ax2.yaxis.set_ticks_position('left')

        if self.legend is not None:
            ax1.set_title("\n".join(textwrap.wrap(self.legend[0], 20)),
                          size=self.text_size['legend_label'])
            ax2.set_title("\n".join(textwrap.wrap(self.legend[1], 20)),
                          size=self.text_size['legend_label'])

        # Add colorbar.
        #
        # Add, then remove the colorbar for the heatmap on the left so that they both end up the
        # same size. Not pythonic, but it works.
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
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=sierra.core.config.kGraphDPI)
        plt.close(fig)  # Prevent memory accumulation (fig.clf() does not close everything)

    def _plot_colorbar(self, fig, im, ax, remove: bool) -> None:
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.05)

        bar = fig.colorbar(im, cax=cax)
        if remove:
            fig.delaxes(fig.axes[2])

        # p0 = axes[0].get_position().get_points().flatten()
        # p1 = axes[1].get_position().get_points().flatten()
        # ax_cbar = fig.add_axes([p0[0], , p1[2] - p0[0], 0.05])
        # bar = fig.colorbar(im, cax=ax_cbar, orientation='horizontal')

        if self.zlabel is not None:
            bar.ax.set_ylabel(self.zlabel, fontsize=self.text_size['xyz_label'])

    def _plot_ticks(self, ax, xvals, yvals, xlabels: bool, ylabels: bool) -> None:
        """
        Plot ticks and tick labels. If the labels are numerical and the numbers are too large, force
        scientific notation (the ``rcParam`` way of doing this does not seem to work...)
        """
        ax.tick_params(labelsize=self.text_size['tick_label'])

        if xlabels:
            ax.set_xticks(yvals)
            ax.set_xticklabels(self.ytick_labels, rotation='vertical')
        else:
            ax.set_xticks([])
            ax.set_xticklabels([])

        if ylabels:
            ax.set_yticks(xvals)
            ax.set_yticklabels(self.xtick_labels, rotation='horizontal')
        else:
            ax.set_yticks([])
            ax.set_yticklabels([])

    def _plot_labels(self, ax, xlabel: bool, ylabel: bool) -> None:
        if xlabel:
            ax.set_xlabel(self.ylabel, fontsize=self.text_size['xyz_label'])

        if ylabel:
            ax.set_ylabel(self.xlabel, fontsize=self.text_size['xyz_label'])


class HeatmapSet():
    """
    Generates a :class:`Heatmap` plot for each of the specified input/output path pairs.
    """

    def __init__(self,
                 ipaths: tp.List[str],
                 opaths: tp.List[str],
                 titles: tp.List[str],
                 **kwargs) -> None:
        self.ipaths = ipaths
        self.opaths = opaths
        self.titles = titles
        self.kwargs = kwargs

    def generate(self) -> None:
        for ipath, opath, title in zip(self.ipaths, self.opaths, self.titles):
            hm = Heatmap(input_fpath=ipath, output_fpath=opath, title=title, **self.kwargs)
            hm.generate()


__api__ = [
    'Heatmap',
    'DualHeatmap',
    'HeatmapSet'
]
