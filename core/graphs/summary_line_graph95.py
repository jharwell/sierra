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
import os
import typing as tp
import logging

# 3rd party packages
import matplotlib.ticker as mticker
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Project packages
import core.config
import core.utils


class SummaryLinegraph95:
    """
    Generates a linegraph summarizing swarm behavior across a :term:`Batch Experiment`, possibly
    showing the 95% confidence interval (hence the
    name).

    Attributes:
        stats_root: The absolute/relative path to the ``statistics/`` directory for the batch
                    experiment.

        input_stem: Stem of the :term:`Summary .csv` file to generate a graph from.

        output_fpath: The absolute/relative path to the output image file to save generated graph
                       to.

        title: Graph title.

        xlabel: X-label for graph.

        ylabel: Y-label for graph.

        xticks: The xticks for the graph.

        xtick_labels: The xtick labels for the graph (can be different than the xticks; e.g., if the
                      xticxs are 1-10 for categorical data, then then labels would be the
                      categories).

        large_text: Should the labels, ticks, and titles be large, or regular size?

        legend: Legend for graph.

        logyscale: Should the Y axis be in the log2 domain ?

        stats: The type of statistics to include on the graph. If ``conf95``,  95% confidence
               interval will be plotted as a shaded region. Ignored otherwise.

        model_root: The absolute/relative path to the ``models/`` directory for the batch
                     experiment.
    """
    # Maximum # of rows that the input .csv to guarantee unique colors
    kMaxRows = 8

    kLineStyles = ['-', '--', '.-', ':', '-', '--', '.-', ':']
    kMarkStyles = ['o', '^', 's', 'x', 'o', '^', 's', 'x']
    kColors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red',
               'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive']

    def __init__(self,
                 stats_root: str,
                 input_stem: str,
                 output_fpath: str,
                 title: str,
                 xlabel: str,
                 ylabel: str,
                 xticks: tp.List[float],
                 xtick_labels: tp.List[str] = None,
                 large_text: bool = False,
                 legend: tp.List[str] = ['Empirical Data'],
                 logyscale: bool = False,
                 stats: str = 'none',
                 model_root: str = None) -> None:

        # Required arguments
        self.stats_root = stats_root
        self.input_stem = input_stem
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
        self.model_root = model_root
        self.legend = legend
        self.logyscale = logyscale
        self.stats = stats

        self.logger = logging.getLogger(__name__)

    def generate(self):
        input_fpath = os.path.join(self.stats_root, self.input_stem +
                                   core.config.kStatsExtensions['mean'])
        if not core.utils.path_exists(input_fpath):
            self.logger.debug("Not generating %s: %s does not exist",
                              self.output_fpath,
                              input_fpath)
            return

        data_dfy = core.utils.pd_csv_read(input_fpath)
        assert len(data_dfy.values) <= self.kMaxRows, \
            "FATAL: Too many rows to make unique line styles/self.kColors/markers: {0} > {1}".format(
                len(data_dfy.values),
                self.kMaxRows)

        model = self._read_models()

        fig, ax = plt.subplots()

        # Plot lines
        self._plot_lines(data_dfy, model)

        # Add legend
        self._plot_legend(model)

        # Add statistics according to configuration
        stat_dfs = self._read_stats()
        self._plot_stats(ax, self.xticks, data_dfy, stat_dfs)

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

    def _plot_lines(self, data_dfy: pd.DataFrame, model: tp.Tuple[pd.DataFrame, tp.List[str]]):

        for i in range(0, len(data_dfy.values)):
            # Plot data
            plt.plot(self.xticks,
                     data_dfy.values[i],
                     self.kLineStyles[i] if model[0] is None else '-',
                     marker=self.kMarkStyles[i],
                     color=self.kColors[i])

            # Plot model prediction(s)
            if model[0] is not None:
                plt.plot(self.xticks,
                         model[0].values[i],
                         '--',
                         marker=self.kMarkStyles[i],
                         color=self.kColors[i + len(data_dfy.index)])

    def _plot_stats(self, ax, xticks, data_dfy: pd.DataFrame, stat_dfs: tp.Dict[str, pd.DataFrame]):
        """
        Plot statistics for all lines on the graph.
        """
        if self.stats == 'conf95' and 'stddev' in stat_dfs.keys():
            for i in range(0, len(data_dfy.values)):
                # 95% interval = 2 std stdeviations
                plt.fill_between(xticks, data_dfy.values[i] - 2 * stat_dfs['stddev'].abs().values[i],
                                 data_dfy.values[i] + 2 * stat_dfs['stddev'].abs().values[i],
                                 alpha=0.50, color=self.kColors[i], interpolate=True)

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

    def _plot_legend(self, model: tp.Tuple[pd.DataFrame, tp.List[str]]):
        legend = self.legend

        if model[1]:
            legend = [val for pair in zip(self.legend, model[1]) for val in pair]

        plt.legend(legend,
                   fontsize=self.text_size['legend_label'],
                   ncol=max(1, int(len(legend) / 3.0)))

    def _read_stats(self) -> tp.Dict[str, list]:
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
    'SummaryLinegraph95'
]
