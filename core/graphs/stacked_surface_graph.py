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
import glob
import re
import pandas as pd
import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
mpl.use('Agg')


class StackedSurfaceGraph:
    """
    Generates a 3D plot of a set of 3D surface graphs from a set of .csv files with the specified
    graph visuals. .csv files must be named as``<input_stem_fpath>_X.csv``, where `X` is
    non-negative integer. Input ``.csv`` files must be 2D grids of the same cardinality.

    This graph does not plot standard deviation.

    If no ``.csv`` files matching the pattern are found, the graph is not generated.

    """
    kMaxSurfaces = 4

    def __init__(self, **kwargs):

        self.input_stem_pattern = os.path.abspath(kwargs['input_stem_pattern'])
        self.output_fpath = kwargs['output_fpath']
        self.title = kwargs['title']
        self.legend = kwargs['legend']
        self.xlabel = kwargs['xlabel']
        self.ylabel = kwargs['ylabel']
        self.zlabel = kwargs['zlabel']
        self.xtick_labels = kwargs['xtick_labels']
        self.ytick_labels = kwargs['ytick_labels']
        self.comp_type = kwargs['comp_type']

    def generate(self):
        dfs = []

        dfs = [pd.read_csv(f, sep=';') for f in glob.glob(
            self.input_stem_pattern + '*.csv') if re.search('_[0-9]+', f)]

        if not dfs:  # empty list
            return
        assert len(dfs) <= 4, "FATAL: Too many surfaces to plot: {0} > {1}".format(len(dfs),
                                                                                   StackedSurfaceGraph.kMaxSurfaces)
        plt.figure(figsize=(10, 10))
        ax = plt.axes(projection='3d')
        x = np.arange(len(dfs[0].columns))
        y = dfs[0].index
        X, Y = np.meshgrid(x, y)

        # Use non-quantitative colormaps in order to get really nice looking surfaces that change
        # color with Z value. From
        # https://stackoverflow.com/questions/55501860/how-to-put-multiple-colormap-patches-in-a-matplotlib-legend
        colors = [plt.cm.Greens, plt.cm.Reds, plt.cm.Purples, plt.cm.Oranges]
        legend_cmap_handles = [mpl.patches.Rectangle((0, 0), 1, 1) for _ in colors]
        legend_handler_map = dict(zip(legend_cmap_handles,
                                      [HandlerColormap(c, num_stripes=8) for c in colors]))

        ax.set_title(self.title, fontsize=24)
        ax.set_zlabel('\n' + self.zlabel, fontsize=18)
        max_xlen = max([len(str(l)) for l in self.xtick_labels])
        max_ylen = max([len(str(l)) for l in self.ytick_labels])
        ax.set_xlabel('\n' * max_xlen + self.xlabel, fontsize=18)
        ax.set_ylabel('\n' * max_ylen + self.ylabel, fontsize=18)

        ax.plot_surface(X, Y, dfs[0], cmap=colors[0])
        for i in range(1, len(dfs)):
            if self.comp_type == 'raw':
                plot_df = dfs[i]
            elif self.comp_type == 'scale3D':
                plot_df = dfs[i] / dfs[0]
            elif self.comp_type == 'diff3D':
                plot_df = dfs[i] - dfs[0]
            ax.plot_surface(X, Y, plot_df, cmap=colors[i], alpha=0.5)

        self.__plot_ticks(ax, x, y)
        self.__plot_legend(ax, legend_cmap_handles, legend_handler_map)

        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        self.__save_figs(fig, ax)
        fig.clf()

    def __plot_ticks(self, ax, xvals, yvals):
        """
        Plot ticks and tick labels. If the labels are numerical and the numbers are too large, force
        scientific notation (the ``rcParam`` way of doing this does not seem to work...)
        """
        ax.tick_params(labelsize=12)
        ax.set_xticks(xvals)
        ax.set_xticklabels(self.xtick_labels, rotation='vertical')

        if isinstance(self.xtick_labels[0], (int, float)):
            x_format = ax.get_xaxis().get_major_formatter()
            if any([len(str(x)) > 5 for x in x_format.seq]):
                x_format.seq = ["{:2.2e}".format(float(s)) for s in x_format.seq]

        ax.set_yticks(yvals)
        ax.set_yticklabels(self.ytick_labels, rotation='vertical')

        if isinstance(self.ytick_labels[0], (int, float)):
            y_format = ax.get_yaxis().get_major_formatter()
            if any([len(str(y)) > 5 for y in y_format.seq]):
                y_format.seq = ["{:2.2e}".format(float(s)) for s in y_format.seq]

    def __plot_legend(self, ax, cmap_handles, handler_map):
        # Legend should have ~3 entries per column, in order to maximize real estate on tightly
        # constrained papers.
        ax.legend(handles=cmap_handles,
                  handler_map=handler_map,
                  labels=self.legend,
                  loc=9,
                  bbox_to_anchor=(0.5, -0.1),
                  ncol=len(self.legend),
                  fontsize=14)

    def __save_figs(self, fig, ax):
        """
        Save multiple rotated copies of the same figure. Necessary for automation of 3D figure
        generation, because you can't really know a priori what views are going to give the best
        results.
        """
        for angle in range(0, 360, 30):
            ax.view_init(elev=None, azim=angle)
            # The path we are passed may contain dots from the controller same, so we extract the
            # leaf of that for manipulation to add the angle of the view right before the file
            # extension.
            path, leaf = os.path.split(self.output_fpath)
            leaf = leaf.split('.')
            leaf = ''.join(leaf[0:-2]) + '_' + str(angle) + '.' + leaf[-1]
            fig.savefig(os.path.join(path, leaf), bbox_inches='tight', dpi=100, pad_inches=0)


class HandlerColormap(mpl.legend_handler.HandlerBase):
    def __init__(self, cmap, num_stripes=8, **kw):
        super().__init__(**kw)
        self.cmap = cmap
        self.num_stripes = num_stripes

    def create_artists(self,
                       legend,
                       orig_handle,
                       xdescent,
                       ydescent,
                       width,
                       height,
                       fontsize,
                       trans):
        stripes = []
        for i in range(self.num_stripes):
            s = mpl.patches.Rectangle([xdescent + i * width / self.num_stripes, ydescent],
                                      width / self.num_stripes,
                                      height,
                                      fc=self.cmap((2 * i + 1) / (2 * self.num_stripes)),
                                      transform=trans)
            stripes.append(s)
        return stripes