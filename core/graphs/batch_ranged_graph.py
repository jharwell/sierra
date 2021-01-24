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

# Core packages
import logging
import typing as tp

# 3rd party packages
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.ticker as mticker

# Project packages
import core.utils
import core.config

mpl.rcParams['lines.linewidth'] = 3
mpl.rcParams['lines.markersize'] = 10
mpl.use('Agg')


class BatchRangedGraph:
    """
    Generates a linegraph of some performance metric across the range of a univariate batch criteria
    (hence the name).

    If the necessary .csv file does not exist, the graph is not generated.

    Attributes:
        input_fpath: The absolute/relative path to the csv file containing the y values to
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

    def __init__(self,
                 input_fpath: str,
                 output_fpath: str,
                 title: str,
                 xlabel: str,
                 ylabel: str,
                 xticks: tp.List[float],
                 xtick_labels: tp.List[str] = None,
                 large_text: bool = False,
                 legend: tp.List[str] = ['Empirical Data'],
                 logyscale: bool = False,
                 stddev_fpath=None,
                 model_fpath: str = None,
                 model_legend_fpath: str = None,
                 polynomial_fit: int = -1) -> None:

        # Required arguments
        self.input_fpath = input_fpath
        self.output_fpath = output_fpath
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.xticks = xticks

        # Optional arguments
        if large_text:
            self.text_size = core.config.kGraphTextSizeLarge
        else:
            self.text_size = core.config.kGraphTextSizeSmall

        self.xtick_labels = xtick_labels
        self.stddev_fpath = stddev_fpath
        self.model_fpath = model_fpath
        self.model_legend_fpath = model_legend_fpath
        self.legend = legend
        self.polynomial_fit = polynomial_fit
        self.logyscale = logyscale

        self.logger = logging.getLogger(__name__)

    def generate(self):
        if not core.utils.path_exists(self.input_fpath):
            self.logger.debug("Not generating %s: %s does not exist",
                              self.output_fpath,
                              self.input_fpath)
            return

        data_dfy = core.utils.pd_csv_read(self.input_fpath)
        assert len(data_dfy.values) <= self.kMaxRows, \
            "FATAL: Too many rows to make unique line styles/colors/markers: {0} > {1}".format(
                len(data_dfy.values),
                self.kMaxRows)

        stddev_dfy = None
        model_dfy = None
        model_legend = []

        if self.stddev_fpath is not None and core.utils.path_exists(self.stddev_fpath):
            stddev_dfy = core.utils.pd_csv_read(self.stddev_fpath)

        if self.model_fpath is not None and core.utils.path_exists(self.model_fpath):
            model_dfy = core.utils.pd_csv_read(self.model_fpath)
            if self.model_legend_fpath is not None and core.utils.path_exists(self.model_legend_fpath):
                with open(self.model_legend_fpath, 'r') as f:
                    model_legend = f.read().splitlines()
            else:
                self.logger.warning("No legend file for model '%s' found", self.model_fpath)
                model_legend = ['Model Prediction']

        fig, ax = plt.subplots()

        # Plot lines
        self._plot_lines(data_dfy, model_dfy)

        # Add legend
        self._plot_legend(model_legend)

        # Add error bars according to configuration
        self._plot_errorbars(self.xticks, data_dfy, stddev_dfy)

        # Add X,Y labelsg
        plt.ylabel(self.ylabel, fontsize=self.text_size['xyz_label'])
        plt.xlabel(self.xlabel, fontsize=self.text_size['xyz_label'])

        # Add ticks
        self._plot_ticks(ax)

        # Add title
        plt.title(self.title, fontsize=self.text_size['title'])

        # Output figure
        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        plt.close(fig)  # Prevent memory accumulation (fig.clf() does not close everything)

    def _plot_lines(self, data_dfy: pd.DataFrame, model_dfy: pd.DataFrame):
        line_styles = ['-', '--', '.-', ':', '-', '--', '.-', ':']
        mark_styles = ['o', '^', 's', 'x', 'o', '^', 's', 'x']
        colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red',
                  'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive']

        for i in range(0, len(data_dfy.values)):
            # Plot data, including polynomial fit line if configured
            plt.plot(self.xticks,
                     data_dfy.values[i],
                     line_styles[i] if model_dfy is None else '-',
                     marker=mark_styles[i],
                     color=colors[i])

            # Plot model prediction(s)
            if model_dfy is not None:
                plt.plot(self.xticks,
                         model_dfy.values[i],
                         '--',
                         marker=mark_styles[i],
                         color=colors[i + len(data_dfy.index)])

            if -1 != self.polynomial_fit:
                coeffs = np.polyfit(self.xticks, data_dfy.values[i], self.polynomial_fit)
                ffit = np.poly1d(coeffs)
                x_new = np.linspace(self.xticks[0], self.xticks[-1], 50)
                y_new = ffit(x_new)
                plt.plot(x_new, y_new, line_styles[i])

    def _plot_errorbars(self, xticks, data_dfy: pd.DataFrame, stddev_dfy: pd.DataFrame):
        """
        Plot errorbars for all lines on the graph, using a shaded region rather than strict error
        bars--looks much nicer.
        """
        if stddev_dfy is None:
            return

        for i in range(0, len(data_dfy.values)):
            plt.fill_between(xticks, data_dfy.values[i] - 2 * stddev_dfy.values[i],
                             data_dfy.values[i] + 2 * stddev_dfy.values[i], alpha=0.25)

    def _plot_ticks(self, ax):
        if self.logyscale:
            ax.set_yscale('symlog', base=2)
            # Use scientific or decimal notation--whichever has fewer chars
            ax.yaxis.set_minor_formatter(mticker.ScalarFormatter())

            # ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.02g"))

        ax.tick_params(labelsize=self.text_size['tick_label'])

        # For ordered, qualitative data
        if self.xtick_labels is not None:
            ax.set_xticks(self.xticks)
            ax.set_xticklabels(self.xtick_labels, rotation='vertical')

    def _plot_legend(self, model_legend: tp.List[str]):
        legend = self.legend

        if model_legend:
            legend = [val for pair in zip(self.legend, model_legend) for val in pair]

        plt.legend(legend,
                   fontsize=self.text_size['legend_label'],
                   ncol=max(1, int(len(legend) / 3.0)))


__api__ = [
    'BatchRangedGraph'
]
