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
import numpy as np
import textwrap
import matplotlib.pyplot as plt


class Heatmap:
    """
    Generates a X vs. Y vs. Z heatmap plot.

    If the necessary .csv file does not exist, the graph is not generated.

    """

    def __init__(self, **kwargs):
        self.input_csv_fpath = os.path.abspath(kwargs['input_fpath'])
        self.output_fpath = os.path.abspath(kwargs['output_fpath'])
        self.title = '\n'.join(textwrap.wrap(kwargs['title'], 40))
        self.xlabel = kwargs['xlabel']
        self.ylabel = kwargs['ylabel']

        self.xtick_labels = kwargs.get('xtick_labels', None)
        self.ytick_labels = kwargs.get('ytick_labels', None)

    def generate(self):
        if not os.path.exists(self.input_csv_fpath):
            return

        df = pd.read_csv(self.input_csv_fpath, sep=';')
        fig, ax = plt.subplots()
        plt.imshow(df, cmap='coolwarm', interpolation='nearest')

        plt.xlabel(self.xlabel, fontsize=18)
        plt.ylabel(self.ylabel, fontsize=18)
        self.__plot_ticks(ax)

        plt.title(self.title, fontsize=24)
        plt.colorbar(fraction=0.046, pad=0.04)
        ax.tick_params(labelsize=12)

        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        fig.clf()

    def __plot_ticks(self, ax):
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
