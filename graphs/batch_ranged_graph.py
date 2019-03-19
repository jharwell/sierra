"""
Copyright 2018 John Harwell, All rights reserved.

  This file is part of SIERRA.

  SIERRA is free software: you can redistribute it and/or modify it under the
  terms of the GNU General Public License as published by the Free Software
  Foundation, either version 3 of the License, or (at your option) any later
  version.

  SIERRA is distributed in the hope that it will be useful, but WITHOUT ANY
  WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
  A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

  You should have received a copy of the GNU General Public License along with
  SIERRA.  If not, see <http://www.gnu.org/licenses/

"""

import os
import pandas as pd
import matplotlib as mpl
mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.use('Agg')
import numpy as np
import matplotlib.pyplot as plt
import itertools

# Maximum # of rows that the input .csv can have
kMaxRows = 4


class BatchRangedGraph:
    """
    Generates a graph of some performance metric vs some batch criteria (swarm size, swarm density,
    etc.). Only valid for batched experiments.

    If the necessary .csv file does not exist, the graph is not generated.

    Attributes:
      inputy_csv_fpath(str): The absolute/relative path to the csv file containing the y values to
                             be graphed.
      output_fpath(str): The absolute/relative path to the output image file to save generated graph
                         to.
      title(str): Graph title.
      xlabel(str): X-label for graph.
      ylabel(str): Y-label for graph.
      legend(str): Legend for graph. If None, no legend is shown.
      polynomial_fit(int): The degree of the polynomial to use for interpolating each row in the
                           input .csv (the resulting trendline is then plotted). -1 disables
                           interpolation and plotting.
      corr(dict): Dictionary of correlation information to include on the plot. Really only useful
                  for single-line plots. Valid keys:

                  coeff -> (float) The calculated r^2 value

    """

    def __init__(self, inputy_fpath, output_fpath, title, xlabel, ylabel, legend, xvals,
                 polynomial_fit, corr={}):

        self.inputy_csv_fpath = os.path.abspath(inputy_fpath)
        self.output_fpath = os.path.abspath(output_fpath)
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.legend = legend
        self.xvals = xvals
        self.polynomial_fit = polynomial_fit
        self.corr = corr

    def generate(self):
        if not os.path.exists(self.inputy_csv_fpath):
            return

        dfy = pd.read_csv(self.inputy_csv_fpath, sep=';')
        fig, ax = plt.subplots()
        line_styles = [':', '--', '.-', '-']
        mark_styles = ['o', '^', 's', 'x']
        colors = ['tab:blue', 'tab:green', 'tab:red', 'tab:brown']
        i = 0

        assert len(dfy.values) < kMaxRows, "FATAL: Too many rows {0} >= {1}".format(len(dfy.values),
                                                                                    kMaxRows)
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

        if 'coeff' in self.corr:
            plt.annotate('$R^2 = {:.4f}'.format(self.corr['coeff']))

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
