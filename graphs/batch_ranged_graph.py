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
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib as mpl
mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.use('Agg')


class BatchRangedGraph:
    """
    Generates a linegraph of some performance metric across the range of a univariate batch criteria
    (hence the name).

    If the necessary .csv file does not exist, the graph is not generated.

    Attributes:
        inputy_csv_fpath: The absolute/relative path to the csv file containing the y values to
                           be graphed.
        output_fpath: The absolute/relative path to the output image file to save generated graph
                       to.
        title: Graph title.
        xlabel: X-label for graph.
        ylabel: Y-label for graph.
        legend: Legend for graph. If None, no legend is shown.
        polynomial_fit: The degree of the polynomial to use for interpolating each row in the
                        input .csv (the resulting trendline is then plotted). -1 disables
                        interpolation and plotting.
    """
    # Maximum # of rows that the input .csv to guarantee unique colors
    kMaxRows = 8

    def __init__(self, **kwargs):
        self.inputy_csv_fpath = os.path.abspath(kwargs['inputy_stem_fpath'] + '.csv')
        self.inputy_stddev_fpath = os.path.abspath(kwargs['inputy_stem_fpath'] + '.stddev')
        self.output_fpath = os.path.abspath(kwargs['output_fpath'])
        self.title = kwargs['title']
        self.xlabel = kwargs['xlabel']
        self.ylabel = kwargs['ylabel']
        self.xvals = kwargs['xvals']

        self.legend = kwargs.get('legend', None)
        self.polynomial_fit = kwargs.get('polynomial_fit', -1)

    def generate(self):
        if not os.path.exists(self.inputy_csv_fpath):
            return

        dfy = pd.read_csv(self.inputy_csv_fpath, sep=';')

        fig, ax = plt.subplots()
        line_styles = [':', '--', '.-', '-', ':', '--', '.-', '-']
        mark_styles = ['o', '^', 's', 'x', 'o', '^', 's', 'x']
        colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red',
                  'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive']
        i = 0

        assert len(dfy.values) <= BatchRangedGraph.kMaxRows, \
            "FATAL: Too many rows to make unique line styles/colors/markers {0} > {1}".format(
                len(dfy.values), BatchRangedGraph.kMaxRows)

        for i in range(0, len(dfy.values)):
            plt.plot(self.xvals, dfy.values[i], line_styles[i],
                     marker=mark_styles[i],
                     color=colors[i])
            if -1 != self.polynomial_fit:
                coeffs = np.polyfit(self.xvals, dfy.values[i], self.polynomial_fit)
                ffit = np.poly1d(coeffs)
                x_new = np.linspace(self.xvals[0], self.xvals[-1], 50)
                y_new = ffit(x_new)
                plt.plot(x_new, y_new, line_styles[i])

        # Plot error bars
        self.__plot_errorbars(self.xvals, dfy)

        if self.legend is not None:
            plt.legend(self.legend, fontsize=14, ncol=max(1, int(len(self.legend) / 3.0)))

        plt.ylabel(self.ylabel, fontsize=18)
        plt.xlabel(self.xlabel, fontsize=18)
        plt.title(self.title, fontsize=24)
        ax.tick_params(labelsize=12)

        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        fig.clf()

    def __plot_errorbars(self, xvals, data_df):
        """
        Plot errorbars for all lines on the graph, using a shaded region rather than strict error
        bars--looks much nicer.

        If the necessary ``.stddev`` file does not exist, no errorbars are plotted.
        """
        if not os.path.exists(self.inputy_stddev_fpath):
            return

        stddev_df = pd.read_csv(self.inputy_stddev_fpath, sep=';')

        # plt.errorbar(data_df.index, data_df[c], xerr=0.5,
        #              yerr=2 * stddev_df[c], linestyle = '')
        for i in range(0, len(data_df.values)):
            plt.fill_between(xvals, data_df.values[i] - 2 * stddev_df.values[i],
                             data_df.values[i] + 2 * stddev_df.values[i], alpha=0.25)
