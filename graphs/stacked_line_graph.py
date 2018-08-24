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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class StackedLineGraph:
    """
    Generates a line graph of one or more lines a column, or set of columns,
    respectively, from the specified .csv with the specified graph visuals.

    If the necessary .csv file does not exist, the graph is not generated.
    If the .stats file that goes with the .csv does not exist, then no error bars are printed.

    """

    def __init__(self, input_stem_fpath, output_fpath, cols, title, legend, xlabel, ylabel):

        self.input_csv_fpath = os.path.abspath(input_stem_fpath) + ".csv"
        self.input_stats_fpath = os.path.abspath(input_stem_fpath) + ".stats"
        self.output_fpath = output_fpath
        self.cols = cols
        self.title = title
        self.legend = legend
        self.xlabel = xlabel
        self.ylabel = ylabel

    def generate(self):
        if not os.path.exists(self.input_csv_fpath):
            return

        df = pd.read_csv(self.input_csv_fpath, sep=';')
        if not os.path.exists(self.input_stats_fpath):
            df2 = None
        else:
            df2 = pd.read_csv(self.input_stats_fpath, sep=';')

        if self.cols is None:
            ax = df.plot(title=self.title)
        else:
            ax = df[self.cols].plot(title=self.title)

        # @BUG This makes all lines appear 1 color...
        # if df2 is not None:
        #     for c in self.cols:
        #         plt.errorbar(df.index, df[c], yerr=df2[c],
        #                      ecolor='gray', lw=2, capsize=5, capthick=2)

        if self.legend is not None:
            lines, labels = ax.get_legend_handles_labels()
            ax.legend(lines, self.legend, loc=9, bbox_to_anchor=(0.5, -0.1), ncol=2)
        else:
            ax.legend(loc=9, bbox_to_anchor=(0.5, -0.1), ncol=2)

        ax.set_xlabel(self.xlabel)
        ax.set_ylabel(self.ylabel)
        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        fig.clf()
