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
import numpy as np
import matplotlib.pyplot as plt
import itertools


class RangedSizeGraph:
    """
    Generates a graph of SOMETHING vs swarm size across a set of swarm sizes. Only valid for batched
    experiments.

    If the necessary .csv file does not exist, the graph is not generated.

    """

    def __init__(self, inputy_fpath, output_fpath, title, ylabel, legend):

        self.inputy_csv_fpath = os.path.abspath(inputy_fpath)
        self.output_fpath = os.path.abspath(output_fpath)
        self.legend = legend
        self.ylabel = ylabel
        self.title = title

    def generate(self):
        if not os.path.exists(self.inputy_csv_fpath):
            return

        dfy = pd.read_csv(self.inputy_csv_fpath, sep=';')
        fig, ax = plt.subplots()

        x = [2 ** x for x in range(0, len(dfy.columns.values))]

        for v in dfy.values:
            coeffs = np.polyfit(x, v, 3)
            ffit = np.poly1d(coeffs)
            x_new = np.linspace(x[0], x[-1], 50)
            y_new = ffit(x_new)
            plt.plot(x, v, 'o', x_new, y_new, '--')

        if self.legend is not None:
            legend = []
            # Stupid hack to double each item in list sequentially because I'm bad at python
            for l in self.legend:
                legend.append(l)
                legend.append(l)
            plt.legend(legend)

        plt.ylabel(self.ylabel)
        plt.xlabel("Swarm Size")
        plt.title(self.title)

        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        fig.clf()
