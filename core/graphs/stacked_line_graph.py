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
import copy
import os

# 3rd party packages
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt

# Project packages
import core.config
import core.utils

matplotlib.use('Agg')
plt.rcParams["axes.prop_cycle"] = plt.cycler("color", plt.cm.tab20.colors)


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
                 stats_root: str,
                 input_stem: str,
                 output_fpath: str,
                 title: str,
                 xlabel: str,
                 ylabel: str,
                 large_text: bool = False,
                 legend: tp.List[str] = [],
                 cols: tp.List[str] = [],
                 linestyles: tp.List[str] = [],
                 dashstyles: tp.List[str] = [],
                 logyscale: bool = False,
                 stddev_fpath=None,
                 stats: str = 'none',
                 model_root: str = None) -> None:

        # Required arguments
        self.stats_root = stats_root
        self.input_stem = input_stem
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
        self.linestyles = linestyles
        self.dashstyles = dashstyles
        self.stats = stats
        self.model_root = model_root
        self.stddev_fpath = stddev_fpath
        self.logger = logging.getLogger(__name__)

    def generate(self):
        input_fpath = os.path.join(self.stats_root, self.input_stem +
                                   core.config.kStatsExtensions['mean'])
        if not core.utils.path_exists(input_fpath):
            self.logger.debug("Not generating %s: %s does not exist",
                              self.output_fpath,
                              input_fpath)
            return

        data_df = core.utils.pd_csv_read(input_fpath)

        model = self._read_models()
        stat_dfs = self._read_stats()

        # Plot specified columns from dataframe.
        if not self.cols:
            ncols = max(1, int(len(data_df.columns) / 2.0))
            ax = self._plot_selected_cols(data_df, stat_dfs, data_df.columns, model)
        else:
            ncols = max(1, int(len(self.cols) / 2.0))
            ax = self._plot_selected_cols(data_df, stat_dfs, self.cols, model)

        self._plot_ticks(ax)

        self._plot_legend(ax, model[1], ncols)

        # Add title
        ax.set_title(self.title, fontsize=self.text_size['title'])

        # Add X,Y labels
        ax.set_xlabel(self.xlabel, fontsize=self.text_size['xyz_label'])
        ax.set_ylabel(self.ylabel, fontsize=self.text_size['xyz_label'])

        # Output figure
        fig = ax.get_figure()
        fig.set_size_inches(core.config.kGraphBaseSize, core.config.kGraphBaseSize)
        fig.savefig(self.output_fpath, bbox_inches='tight', dpi=core.config.kGraphDPI)
        plt.close(fig)  # Prevent memory accumulation (fig.clf() does not close everything)

    def _plot_ticks(self, ax):
        if self.logyscale:
            plt.yscale('symlog')

        ax.tick_params(labelsize=self.text_size['tick_label'])

    def _plot_selected_cols(self,
                            data_df: pd.DataFrame,
                            stat_dfs: tp.Dict[str, pd.DataFrame],
                            cols: tp.List[str],
                            model: tp.Tuple[pd.DataFrame, tp.List[str]]):
        """
        Plots selected columns in a dataframe, (possibly) including:

        - Errorbars
        - Models
        - Custom line styles
        - Custom dash styles
        """
        # Always plot the data
        if not self.linestyles:
            ax = data_df[cols].plot()
            return ax
        else:
            if not self.dashstyles:
                for c, s in zip(cols, self.linestyles):
                    ax = data_df[c].plot(linestyle=s)
                return ax
            else:
                for c, s, d in zip(cols, self.linestyles, self.dashstyles):
                    ax = data_df[c].plot(linestyle=s, dashes=d)
                return ax

        # Plot models if they have been computed
        if model[0] is not None:
            model[0][model[0].columns].plot(ax=ax)

        # Plot stddev if it has been computed
        if 'stddev' in stat_dfs.keys():
            for c in cols:
                self._plot_col_errorbars(data_df, stat_dfs['stddev'], c)
        return ax

    def _plot_col_errorbars(self,
                            data_df: pd.DataFrame,
                            stddev_df: pd.DataFrame,
                            col: str):
        """
        Plot the errorbars for a specific column in a dataframe.
        """
        plt.fill_between(data_df.index,
                         data_df[col] - 2 * stddev_df[col].abs(),
                         data_df[col] + 2 * stddev_df[col].abs(),
                         alpha=0.50)

    def _plot_legend(self, ax, model_legend: tp.List[str], ncols: int):
        # Should have ~3 entries per column, in order to maximize real estate on tightly
        # constrained papers.

        # If the legend is not specified, then we assume this is not a graph that will contain any
        # models.
        if self.legend:
            legend = copy.deepcopy(self.legend)
            if model_legend:
                legend.extend(model_legend)

            lines, _ = ax.get_legend_handles_labels()
            ax.legend(lines,
                      legend,
                      loc='lower center',
                      bbox_to_anchor=(0.5, -0.5),
                      ncol=ncols,
                      fontsize=self.text_size['legend_label'])
        else:
            ax.legend(loc='lower center',
                      bbox_to_anchor=(0.5, -0.5),
                      ncol=ncols,
                      fontsize=self.text_size['legend_label'])

    def _read_stats(self) -> tp.Dict[str, pd.DataFrame]:
        dfs = {}
        if self.stats == 'conf95':
            stddev_ipath = os.path.join(self.stats_root,
                                        self.input_stem + core.config.kStatsExtensions['stddev'])
            if core.utils.path_exists(stddev_ipath):
                dfs['stddev'] = core.utils.pd_csv_read(stddev_ipath)
            else:
                self.logger.warning("Stddev file not found for '%s'", self.input_stem)

        return dfs

    def _read_models(self) -> tp.Tuple[pd.DataFrame, tp.List[str]]:
        if self.model_root is not None:
            model_fpath = os.path.join(self.model_root, self.input_stem + '.model')
            model_legend_fpath = os.path.join(self.model_root, self.input_stem + '.legend')
            if core.utils.path_exists(model_fpath):
                model = core.utils.pd_csv_read(model_fpath)
                if core.utils.path_exists(model_legend_fpath):
                    with open(model_legend_fpath, 'r') as f:
                        model_legend = f.read().splitlines()
                else:
                    self.logger.warning("No legend file for model '%s' found", model_fpath)
                    model_legend = ['Model Prediction']

                return (model, model_legend)

        return (None, [])


__api__ = [
    'StackedLineGraph'
]
