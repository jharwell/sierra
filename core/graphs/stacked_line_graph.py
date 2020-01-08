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
import logging

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams["axes.prop_cycle"] = plt.cycler("color", plt.cm.tab20.colors)


class StackedLineGraph:
    """
    Generates a line graph of one or more lines a column, or set of columns,
    respectively, from the specified .csv with the specified graph visuals.

    If the necessary .csv file does not exist, the graph is not generated.
    If the .stddev file that goes with the .csv does not exist, then no error bars are printed.

    """

    def __init__(self, **kwargs):

        self.input_csv_fpath = os.path.abspath(kwargs['input_stem_fpath']) + ".csv"
        self.input_stddev_fpath = os.path.abspath(kwargs['input_stem_fpath']) + ".stddev"
        self.output_fpath = kwargs['output_fpath']
        self.title = kwargs['title']
        self.xlabel = kwargs['xlabel']
        self.ylabel = kwargs['ylabel']

        self.linestyles = kwargs.get('linestyles', None)
        self.dashes = kwargs.get('dashes', None)
        self.legend = kwargs.get('legend', None)
        self.cols = kwargs.get('cols', None)

    def generate(self):
        if not os.path.exists(self.input_csv_fpath):
            logging.debug("Not generating stacked line graph: %s does not exist",
                          self.input_csv_fpath)
            return

        # Read .csv and scaffold graph
        df = pd.read_csv(self.input_csv_fpath, sep=';')
        if not os.path.exists(self.input_stddev_fpath):
            df2 = None
        else:
            df2 = pd.read_csv(self.input_stddev_fpath, sep=';')

        # Plot specified columns from dataframe
        if self.cols is None:
            ncols = max(1, int(len(df.columns) / 3.0))
            ax = self._plot_selected_cols(df, df2, df.columns)
        else:
            ncols = max(1, int(len(self.cols) / 3.0))
            ax = self._plot_selected_cols(df, df2, self.cols)
        ax.tick_params(labelsize=12)

        # Add legend. Should have ~3 entries per column, in order to maximize real estate on tightly
        # constrained papers.
        if self.legend is not None:
            lines, labels = ax.get_legend_handles_labels()
            ax.legend(lines, self.legend, loc=9, bbox_to_anchor=(
                0.5, -0.1), ncol=ncols, fontsize=14)
        else:
            ax.legend(loc=9, bbox_to_anchor=(0.5, -0.1), ncol=ncols, fontsize=14)

        # Add title
        ax.set_title(self.title, fontsize=24)

        # Add X,Y labels
        ax.set_xlabel(self.xlabel, fontsize=18)
        ax.set_ylabel(self.ylabel, fontsize=18)

        # Output figure
        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        fig.clf()

    def _plot_selected_cols(self, data_df, stddev_df, cols):
        """
        Plots selected columns in a dataframe, (possibly) including:

        - Custom linestyles
        - Custom dash styles
        - Errorbars
        """
        if self.linestyles is None:
            ax = data_df[cols].plot()
            if stddev_df is not None:
                for c in cols:
                    self._plot_col_errorbars(data_df, stddev_df, c)
            return ax
        else:
            if self.dashes is None:
                for c, s in zip(cols, self.linestyles):
                    ax = data_df[c].plot(linestyle=s)
                    if stddev_df is not None:
                        self._plot_col_errorbars(data_df, stddev_df, c)
            else:
                for c, s, d in zip(cols, self.linestyles, self.dashes):
                    ax = data_df[c].plot(linestyle=s, dashes=d)
                    if stddev_df is not None:
                        self._plot_col_errorbars(data_df, stddev_df, c)
            return ax

    def _plot_col_errorbars(self, data_df, stddev_df, col):
        """
        Plot the errorbars for a specific column in a dataframe.
        """
        # plt.errorbar(data_df.index, data_df[c], xerr=0.5,
        #              yerr=2 * stddev_df[c], linestyle = '')
        plt.fill_between(data_df.index, data_df[col] - 2 * stddev_df[col],
                         data_df[col] + 2 * stddev_df[col], alpha=0.25)
