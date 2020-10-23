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


import os
import textwrap
import logging
import glob
import re
import typing as tp

import numpy as np
import matplotlib.pyplot as plt
import mpl_toolkits.axes_grid1
import pandas as pd

import core.utils


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
                 xtick_labels: tp.List[str] = None,
                 ytick_labels: tp.List[str] = None,
                 transpose: bool = False,
                 zlabel: str = None,
                 interpolation: str = 'nearest') -> None:
        self.input_fpath = input_fpath
        self.output_fpath = output_fpath
        self.title = '\n'.join(textwrap.wrap(title, 40))

        self.transpose = transpose
        self.colorbar_label = zlabel
        self.interpolation = interpolation

        self.xlabel = xlabel if self.transpose else ylabel
        self.ylabel = ylabel if self.transpose else xlabel

        if not self.transpose:
            self.xtick_labels = ytick_labels
            self.ytick_labels = xtick_labels
        else:
            self.xtick_labels = xtick_labels
            self.ytick_labels = ytick_labels

    def generate(self):
        if not core.utils.path_exists(self.input_fpath):
            logging.debug("Not generating heatmap: %s does not exist", self.input_fpath)
            return

        # Read .csv and create raw heatmap from default configuration
        data_df = core.utils.pd_csv_read(self.input_fpath)
        self._plot_df(data_df, self.output_fpath)

    def _plot_df(self, df: pd.DataFrame, opath: str):
        fig, ax = plt.subplots()

        # Transpose if requested
        if self.transpose:
            df = df.transpose()

        # Plot heatmap
        plt.imshow(df, cmap='plasma', interpolation=self.interpolation)

        # Add labels
        plt.xlabel(self.xlabel, fontsize=18)
        plt.ylabel(self.ylabel, fontsize=18)

        # Add X,Y ticks
        self._plot_ticks(ax)

        # Add graph title
        plt.title(self.title, fontsize=24)

        # Add colorbar
        self._plot_colorbar(ax)

        # Output figure
        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(opath, bbox_inches='tight', dpi=100)
        plt.close(fig)  # Prevent memory accumulation (fig.clf() does not close everything)

    def _plot_colorbar(self, ax):
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.05)
        bar = plt.colorbar(cax=cax)
        if self.colorbar_label is not None:
            bar.ax.set_ylabel(self.colorbar_label)

    def _plot_ticks(self, ax):
        ax.tick_params(labelsize=12)

        if self.xtick_labels is not None:
            ax.set_xticks(np.arange(len(self.xtick_labels)))
            ax.set_xticklabels(self.xtick_labels, rotation='vertical')

            if isinstance(self.xtick_labels[0], (int, float)):
                # If the labels are too long, then we force scientific notation. The rcParam way of
                # doing this does not seem to have any effect...
                x_format = ax.get_xaxis().get_major_formatter()
                if any([len(str(x)) > 5 for x in x_format.seq]):
                    x_format.seq = ["{:2.2e}".format(float(s)) for s in x_format.seq]

        if self.ytick_labels is not None:
            ax.set_yticks(np.arange(len(self.ytick_labels)))
            ax.set_yticklabels(self.ytick_labels)

            if isinstance(self.ytick_labels[0], (int, float)):
                # If the labels are too long, then we force scientific notation. The rcParam way of
                # doing this does not seem to have any effect...
                y_format = ax.get_yaxis().get_major_formatter()
                if any([len(str(y)) > 5 for y in y_format.seq]):
                    y_format.seq = ["{:2.2e}".format(float(s)) for s in y_format.seq]


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

    def generate(self):
        for ipath, opath, title in zip(self.ipaths, self.opaths, self.titles):
            hm = Heatmap(input_fpath=ipath, output_fpath=opath, title=title, **self.kwargs)
            hm.generate()


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
        self.colorbar_label = kwargs['zlabel']

        self.xlabel = kwargs.get('xlabel', None)
        self.ylabel = kwargs.get('ylabel', None)
        self.xtick_labels = kwargs.get('xtick_labels', None)
        self.ytick_labels = kwargs.get('ytick_labels', None)

    def generate(self):
        dfs = [core.utils.pd_csv_read(f) for f in glob.glob(
            self.input_stem_pattern + '*.csv') if re.search('_[0-9]+', f)]

        if not dfs or len(dfs) != DualHeatmap.kCardinality:
            logging.debug("Not generating dual heatmap graph: %s did not match %s .csv files",
                          self.input_stem_pattern, DualHeatmap.kCardinality)
            return

        # Scaffold graph
        fig, axes = plt.subplots(ncols=2, figsize=(10, 10))
        ax1, ax2 = axes
        y = np.arange(len(dfs[0].columns))
        x = dfs[0].index

        # Plot heatmaps
        im1 = ax1.matshow(dfs[0], cmap='plasma', interpolation='none')
        im2 = ax2.matshow(dfs[1], cmap='plasma', interpolation='none')

        # Add titles
        fig.suptitle(self.title, fontsize=24)
        ax1.xaxis.set_ticks_position('bottom')
        ax1.yaxis.set_ticks_position('left')
        ax2.xaxis.set_ticks_position('bottom')
        ax2.yaxis.set_ticks_position('left')

        if self.legend is not None:
            ax1.set_title("\n".join(textwrap.wrap(self.legend[0], 20)), size=20)
            ax2.set_title("\n".join(textwrap.wrap(self.legend[1], 20)), size=20)

        # Add colorbar
        self._plot_colorbar(fig, im1, ax1)
        self._plot_colorbar(fig, im2, ax2)

        # Add X,Y,Z labels
        self._plot_labels(ax1)
        self._plot_labels(ax2)

        # Add X,Y ticks
        self._plot_ticks(ax1, x, y)
        self._plot_ticks(ax2, x, y)

        # Output figures
        plt.tight_layout()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        plt.close(fig)  # Prevent memory accumulation (fig.clf() does not close everything)

    def _plot_colorbar(self, fig, im, ax):
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(ax)
        cax = divider.append_axes('right', size='5%', pad=0.05)
        bar = fig.colorbar(im, cax=cax)
        if self.colorbar_label is not None:
            bar.ax.set_ylabel(self.colorbar_label)

    def _plot_ticks(self, ax, xvals, yvals):
        """
        Plot ticks and tick labels. If the labels are numerical and the numbers are too large, force
        scientific notation (the ``rcParam`` way of doing this does not seem to work...)
        """
        ax.tick_params(labelsize=12)
        ax.set_xticks(yvals)
        ax.set_xticklabels(self.ytick_labels, rotation='vertical')

        if isinstance(self.xtick_labels[0], (int, float)):
            x_format = ax.get_xaxis().get_major_formatter()
            if any([len(str(x)) > 5 for x in x_format.seq]):
                x_format.seq = ["{:2.2e}".format(float(s)) for s in x_format.seq]

        ax.set_yticks(xvals)
        ax.set_yticklabels(self.xtick_labels, rotation='horizontal')

        if isinstance(self.ytick_labels[0], (int, float)):
            y_format = ax.get_yaxis().get_major_formatter()
            if any([len(str(y)) > 5 for y in y_format.seq]):
                y_format.seq = ["{:2.2e}".format(float(s)) for s in y_format.seq]

    def _plot_labels(self, ax):
        ax.set_ylabel(self.xlabel, fontsize=18)
        # ax.set_xlabel(self.ylabel, fontsize=18)


__api__ = [
    'Heatmap',
    'DualHeatmap'
]
