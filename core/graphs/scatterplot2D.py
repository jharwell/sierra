# Copyright 2020 John Harwell, All rights reserved.
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


import core.utils
import os
import logging

import numpy as np
import sympy
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


class Scatterplot2D:
    """
    Generates a 2D scatterplot of rows vs. colums (X vs. Y) from the specified `.csv` file.

    If the necessary `.csv` file does not exist, the graph is not generated.
    """

    def __init__(self, **kwargs) -> None:

        self.input_fpath = os.path.abspath(kwargs['input_fpath'])
        self.output_fpath = kwargs['output_fpath']
        self.title = kwargs['title']
        self.xlabel = kwargs['xlabel']
        self.ylabel = kwargs['ylabel']
        self.xcol = kwargs['xcol']
        self.ycol = kwargs['ycol']
        self.regression = kwargs.get('regression', False)
        self.logger = logging.getLogger(__name__)

    def generate(self):
        if not core.utils.path_exists(self.input_fpath):
            self.logger.debug("Not generating 2D scatterplot: %s does not exist",
                              self.input_fpath)
            return

        # Read .csv and scaffold graph
        df = core.utils.pd_csv_read(self.input_fpath)
        ax = df.plot.scatter(x=self.xcol, y=self.ycol)

        # Plot regression line
        if self.regression:
            self.__plot_regression(df)

        # Plot ticks and labels
        ax.tick_params(labelsize=12)
        ax.set_xlabel(self.xlabel, fontsize=18)
        ax.set_ylabel(self.ylabel, fontsize=18)

        # Add title
        ax.set_title(self.title, fontsize=24)

        # Output figure
        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        plt.close(fig)  # Prevent memory accumulation (fig.clf() does not close everything)

    def __plot_regression(self, df):
        # slope, intercept, r_value, p_value, std_err = stats.linregress(df.loc[:, self.xcol],
        #                                                                df.loc[:, self.ycol])
        # x_new = np.linspace(df[self.xcol].min(), df[self.xcol].max(), 50)
        # line = slope * x_new * intercept
        # plt.plot(x_new, line, 'r', label='y={:.2f}x+{:.2f}'.format(slope, intercept))

        # Calculate linear regression line
        coeffs = np.polyfit(x=df.loc[:, self.xcol],
                            y=df.loc[:, self.ycol], deg=1)
        ffit = np.poly1d(coeffs)
        x_new = np.linspace(df[self.xcol].min(), df[self.xcol].max(), 50)
        y_new = ffit(x_new)

        # Plot line and add equation to legend
        xsym = sympy.symbols('x')
        eqn = sum(sympy.S("{:6.2f}".format(v)) * xsym**i for i, v in enumerate(coeffs[::-1]))
        latex = sympy.printing.latex(eqn)
        plt.plot(x_new, y_new, label="${}$".format(latex))
        plt.legend(fontsize=18)


__api__ = [
    'Scatterplot2D'
]
