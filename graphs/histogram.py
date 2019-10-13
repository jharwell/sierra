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
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from scipy.stats import norm


class Histogram:
    """
    Generates a histogram from a single column within a .csv

    If the necessary .csv file does not exist, the graph is not generated.

    """

    def __init__(self, input_fpath, output_fpath, col, title, xlabel, ylabel):

        self.input_csv_fpath = os.path.abspath(input_fpath)
        self.output_fpath = os.path.abspath(output_fpath)
        self.col = col
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

    def generate(self):
        if not os.path.exists(self.input_csv_fpath):
            return

        df = pd.read_csv(self.input_csv_fpath, sep=';')
        fig, ax = plt.subplots()
        n, bins, patches = plt.hist(x=df[self.col].values, bins=50)

        (mu, sigma) = norm.fit(df[self.col])
        y = mlab.normpdf(bins, mu, sigma)
        plt.plot(bins, y, 'r--', linewidth=2)

        plt.xlabel(self.xlabel, fontsize=18)
        plt.ylabel(self.ylabel, fontsize=18)
        plt.title(r'$\mathrm{Histogram\ of\ IQ:}\ \mu=%.3f,\ \sigma=%.3f$' % (mu, sigma),
                  fontsize=24)
        ax.tick_params(labelsize=12)

        plt.title(self.title + r" ($\mu=%.3f, \sigma=%.3f$)" % (mu, sigma))
        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        fig.clf()
