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
import core.config
import core.utils
import matplotlib.pyplot as plt
import logging
import typing as tp
import copy

# 3rd party packages
import pandas as pd
import matplotlib
matplotlib.use('Agg')
plt.rcParams["axes.prop_cycle"] = plt.cycler("color", plt.cm.tab20.colors)

# Project packages


class StackedLineGraph:
    """
    Generates a line graph of one or more lines a column, or set of columns,
    respectively, from the specified .csv with the specified graph visuals.

    If the necessary data .csv file does not exist, the graph is not generated.
    If the .stddev file that goes with the .csv does not exist, then no error bars are plotted.
    if the .model file that goes with the .csv does not exist, then no model predictions are
    plotted.

    Ideally, model predictions/stddev calculations would be in derivade classes, but I can't figure
    out a good way to easily pull that stuff out of here.

    """

    def __init__(self,
                 input_fpath: str,
                 output_fpath: str,
                 title: str,
                 xlabel: str,
                 ylabel: str,
                 large_text: bool = False,
                 legend: tp.List[str] = None,
                 cols: tp.List[str] = None,
                 logyscale: bool = False,
                 stddev_fpath=None,
                 model_fpath: str = None,
                 model_legend_fpath: str = None) -> None:

        # Required arguments
        self.input_fpath = input_fpath
        self.output_fpath = output_fpath
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel

        # Optional arguments
        if large_text:
            self.text_size = core.config.kGraphTextSizeLarge
        else:
            self.text_size = core.config.kGraphTextSizeSmall

        self.legend = legend
        self.cols = cols
        self.logyscale = logyscale

        self.model_fpath = model_fpath
        self.model_legend_fpath = model_legend_fpath
        self.stddev_fpath = stddev_fpath
        self.logger = logging.getLogger(__name__)

    def generate(self):
        if not core.utils.path_exists(self.input_fpath):
            self.logger.debug("Not generating %s: %s does not exist",
                              self.output_fpath,
                              self.input_fpath)
            return

        data_df = core.utils.pd_csv_read(self.input_fpath)
        stddev_df = None
        model_df = None
        model_legend = []

        if self.stddev_fpath is not None and core.utils.path_exists(self.stddev_fpath):
            stddev_df = core.utils.pd_csv_read(self.stddev_fpath)

        if self.model_fpath is not None and core.utils.path_exists(self.model_fpath):
            model_df = core.utils.pd_csv_read(self.model_fpath)

            if self.model_legend_fpath is not None and core.utils.path_exists(self.model_legend_fpath):
                with open(self.model_legend_fpath, 'r') as f:
                    model_legend = f.read().splitlines()
            else:
                self.logger.warning("No legend file for model '%s' found", self.model_fpath)
                model_legend = ['Model Prediction']

        # Plot specified columns from dataframe.
        if self.cols is None:
            ncols = max(1, int(len(data_df.columns) / 3.0))
            ax = self._plot_selected_cols(data_df, stddev_df, data_df.columns, model_df)
        else:
            ncols = max(1, int(len(self.cols) / 3.0))
            ax = self._plot_selected_cols(data_df, stddev_df, self.cols, model_df)

        if self.logyscale:
            plt.yscale('symlog')

        ax.tick_params(labelsize=self.text_size['tick_label'])

        # Add legend. Should have ~3 entries per column, in order to maximize real estate on tightly
        # constrained papers.
        self._plot_legend(ax, model_legend, ncols)

        # Add title
        ax.set_title(self.title, fontsize=self.text_size['title'])

        # Add X,Y labels
        ax.set_xlabel(self.xlabel, fontsize=self.text_size['xyz_label'])
        ax.set_ylabel(self.ylabel, fontsize=self.text_size['xyz_label'])

        # Output figure
        fig = ax.get_figure()
        fig.set_size_inches(10, 10)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=100)
        plt.close(fig)  # Prevent memory accumulation (fig.clf() does not close everything)

    def _plot_selected_cols(self,
                            data_df: pd.DataFrame,
                            stddev_df: pd.DataFrame,
                            cols: tp.List[str],
                            model_df: pd.DataFrame):
        """
        Plots selected columns in a dataframe, (possibly) including:

        - Errorbars
        - Models
        """
        # Always plot the data
        ax = data_df[cols].plot()

        # Plot models if they have been computed
        if model_df is not None:
            model_df[model_df.columns].plot(ax=ax)

        # Plot stddev if it has been computed
        if stddev_df is not None:
            for c in cols:
                self._plot_col_errorbars(data_df, stddev_df, c)

        return ax

    def _plot_col_errorbars(self,
                            data_df: pd.DataFrame,
                            stddev_df: pd.DataFrame,
                            col: str):
        """
        Plot the errorbars for a specific column in a dataframe.
        """
        # plt.errorbar(data_df.index, data_df[c], xerr=0.5,
        #              yerr=2 * stddev_df[c], linestyle = '')
        plt.fill_between(data_df.index, data_df[col] - 2 * stddev_df[col],
                         data_df[col] + 2 * stddev_df[col], alpha=0.25)

    def _plot_legend(self, ax, model_legend: tp.List[str], ncols: int):
        # If the legend is not specified, then we assume this is not a graph that will contain any
        # models.
        if self.legend:
            legend = copy.deepcopy(self.legend)
            if model_legend:
                legend.extend(model_legend)

            lines, _ = ax.get_legend_handles_labels()
            ax.legend(lines,
                      legend,
                      loc=9,
                      bbox_to_anchor=(0.5, -0.1),
                      ncol=ncols,
                      fontsize=self.text_size['legend_label'])
        else:
            ax.legend(loc=9,
                      bbox_to_anchor=(0.5, -0.1),
                      ncol=ncols,
                      fontsize=self.text_size['legend_label'])


__api__ = [
    'StackedLineGraph'
]
