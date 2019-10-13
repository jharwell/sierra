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
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats


class ComparisonGraph:
    """
    Generates a X vs. Y single-line plot with a linear best fit line to compare two columns within
    two different .csv files (or possibly the same .csv file).

    If the necessary .csv files do not exist, the graph is not generated.

    """

    def __init__(self, inputx_fpath, inputy_fpath, output_fpath, colx, coly,
                 title, xlabel, ylabel):

        self.inputx_csv_fpath = os.path.abspath(inputx_fpath)
        self.inputy_csv_fpath = os.path.abspath(inputy_fpath)
        self.output_fpath = os.path.abspath(output_fpath)
        self.colx = colx
        self.coly = coly
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

    def generate(self):
        if not os.path.exists(self.inputx_csv_fpath):
            return
        if not os.path.exists(self.inputy_csv_fpath):
            return

        dfx = pd.read_csv(self.inputx_csv_fpath, sep=';')
        dfy = pd.read_csv(self.inputy_csv_fpath, sep=';')
        fig, ax = plt.subplots()

        slope, intercept, r_value, p_value, std_err = stats.linregress(dfx[self.colx].values,
                                                                       dfy[self.coly].values)
        line = slope * dfx[self.colx].values + intercept
        plt.plot(dfx[self.colx].values, line, label='y={:.2f}x+{:.2f}'.format(slope, intercept))
        plt.scatter(x=dfx[self.colx].values, y=dfy[self.coly].values, color=["r", "b"])
        plt.legend(fontsize=9)
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.title(self.title)

        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        fig.clf()
