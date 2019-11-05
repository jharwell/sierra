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
import pandas as pd
import matplotlib
import matplotlib.patches
import numpy as np
import glob
import re
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
matplotlib.use('Agg')


class StackedSurfaceGraph:
    """
    Generates a 3D plot of a set of 3D surface graphs from a set of .csv files with the specified
    graph visuals. .csv files must be named as``<input_stem_fpath>_X.csv``, where ``X` is
    non-negative integer. Input ``.csv`` files must be 2D grids of the same cardinality.

    This graph does not plot standard deviation.

    If no ``.csv`` files matching the pattern are found, the graph is not generated.

    """

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
        self.norm_comp = kwargs['norm_comp']

    def generate(self):
        dfs = []

        dfs = [pd.read_csv(f, sep=';') for f in glob.glob(
            self.input_stem_pattern + '*.csv') if re.search('_[0-9]+', f)]

        if not dfs:  # empty list
            return

        plt.figure(figsize=(10, 10))
        ax = plt.axes(projection='3d')
        x = np.arange(len(dfs[0].columns))
        y = dfs[0].index
        X, Y = np.meshgrid(x, y)
        proxies = []

        # This gives give quantitatively different colors (i.e. colors 0 and 1 are waayyyy different
        # rather than very similar), which is necessary for overlapping surfaces to look nice.
        colors = plt.cm.Pastel1(np.arange(len(dfs)))

        ax.set_title(self.title, fontsize=24)
        ax.xaxis._axinfo['label']['space_factor'] = 2.8
        ax.yaxis._axinfo['label']['space_factor'] = 2.8
        ax.set_zlabel('\n' + self.zlabel, fontsize=18)
        max_xlen = max([len(str(l)) for l in self.xtick_labels])
        max_ylen = max([len(str(l)) for l in self.ytick_labels])
        ax.set_xlabel('\n' * max_xlen + self.xlabel, fontsize=18)
        ax.set_ylabel('\n' * max_ylen + self.ylabel, fontsize=18)

        for i in range(0, len(dfs)):
            if self.norm_comp:
                ax.plot_surface(X, Y, dfs[i] / dfs[0], alpha=0.75, color=colors[i])
            else:
                ax.plot_surface(X, Y, dfs[i], alpha=0.75, color=colors[i])

            # Legends aren't directly support in 3D plots, so we have to use proxy artists
            proxies.append(matplotlib.patches.Patch(color=colors[i], label=self.legend[i]))

        self.__plot_ticks(ax, x, y)
        self.__plot_legend(ax, proxies)

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

    def __plot_legend(self, ax, proxy_artists):
        # Legend should have ~3 entries per column, in order to maximize real estate on tightly
        # constrained papers.
        ax.legend(handles=proxy_artists,
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
        for angle in range(0, 360, 60):
            ax.view_init(elev=None, azim=angle)
            components = self.output_fpath.split('.')
            path = ''.join(components[0:-2]) + '_' + str(angle) + '.' + components[-1]

            fig.savefig(path, bbox_inches='tight', dpi=100, pad_inches=0)
