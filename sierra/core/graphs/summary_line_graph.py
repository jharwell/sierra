# Copyright 2018 John Harwell, All rights reserved.
#
# This file is part of SIERRA.
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
"""
Linegraph for summarizing the results of a batch experiment in different ways.
"""

# Core packages
import os
import typing as tp
import logging

# 3rd party packages
import matplotlib.ticker as mticker
import matplotlib.pyplot as plt
import pandas as pd

# Project packages
from sierra.core import config, utils, storage


class SummaryLineGraph:
    """Generates a linegraph from a :term:`Summary .csv`.

    Possibly shows the 95% confidence interval or box and whisker plots,
    according to configuration.

    Attributes:
        stats_root: The absolute/relative path to the ``statistics/`` directory
                    for the batch experiment.

        input_stem: Stem of the :term:`Summary .csv` file to generate a graph
                    from.

        output_fpath: The absolute/relative path to the output image file to
                      save generated graph to.

        title: Graph title.

        xlabel: X-label for graph.

        ylabel: Y-label for graph.

        xticks: The xticks for the graph.

        xtick_labels: The xtick labels for the graph (can be different than the
                      xticks; e.g., if the xticxs are 1-10 for categorical data,
                      then then labels would be the categories).

        large_text: Should the labels, ticks, and titles be large, or regular
                    size?

        legend: Legend for graph.

        logyscale: Should the Y axis be in the log2 domain ?

        stats: The type of statistics to include on the graph (from
               ``--dist-stats``).

        model_root: The absolute/relative path to the ``models/`` directory for
                     the batch experiment.

    """
    kLineStyles = ['-', '--', '.-', ':', '-', '--', '.-', ':']
    kMarkStyles = ['o', '^', 's', 'x', 'o', '^', 's', 'x']

    def __init__(self,
                 stats_root: str,
                 input_stem: str,
                 output_fpath: str,
                 title: str,
                 xlabel: str,
                 ylabel: str,
                 xticks: tp.List[float],
                 xtick_labels: tp.Optional[tp.List[str]] = None,
                 large_text: bool = False,
                 legend: tp.List[str] = ['Empirical Data'],
                 logyscale: bool = False,
                 stats: str = 'none',
                 model_root: tp.Optional[str] = None) -> None:

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
            self.text_size = config.kGraphTextSizeLarge
        else:
            self.text_size = config.kGraphTextSizeSmall

        self.xtick_labels = xtick_labels
        self.model_root = model_root
        self.legend = legend
        self.logyscale = logyscale
        self.stats = stats

        self.logger = logging.getLogger(__name__)

    def generate(self) -> None:
        input_fpath = os.path.join(self.stats_root, self.input_stem +
                                   config.kStatsExt['mean'])
        if not utils.path_exists(input_fpath):
            self.logger.debug("Not generating %s: %s does not exist",
                              self.output_fpath,
                              input_fpath)
            return

        data_dfy = storage.DataFrameReader('storage.csv')(input_fpath)
        model = self._read_models()

        fig, ax = plt.subplots()

        # Plot lines
        self._plot_lines(data_dfy, model)

        # Add legend
        self._plot_legend(model)

        # Add statistics according to configuration
        stat_dfs = self._read_stats()
        self._plot_stats(ax, self.xticks, data_dfy, stat_dfs)

        # Add X,Y labels
        plt.ylabel(self.ylabel, fontsize=self.text_size['xyz_label'])
        plt.xlabel(self.xlabel, fontsize=self.text_size['xyz_label'])

        # Add ticks
        self._plot_ticks(ax)

        # Add title
        plt.title(self.title, fontsize=self.text_size['title'])

        # Output figure
        fig = ax.get_figure()
        fig.set_size_inches(config.kGraphBaseSize,
                            config.kGraphBaseSize)
        fig.savefig(self.output_fpath, bbox_inches='tight',
                    dpi=config.kGraphDPI)
        # Prevent memory accumulation (fig.clf() does not close everything)
        plt.close(fig)

    def _plot_lines(self, data_dfy: pd.DataFrame, model: tp.Tuple[pd.DataFrame, tp.List[str]]) -> None:
        for i in range(0, len(data_dfy.values)):
            assert len(data_dfy.values[i]) == len(self.xticks),\
                "Length mismatch between xticks,data: {0} vs {1}/{2} vs {3}".format(
                    len(self.xticks),
                    len(data_dfy.values[i]),
                    self.xticks,
                    data_dfy.values[i])

            # Plot data
            plt.plot(self.xticks,
                     data_dfy.values[i],
                     marker=self.kMarkStyles[i],
                     color=f"C{i}")

            # Plot model prediction(s)
            if model[0] is not None:
                # The model might be of different dimensions than the data. If
                # so, truncate it to fit.
                if len(self.xticks) < len(model[0].values[i]):
                    self.logger.warning("Truncating model: model/data lengths disagree: %s vs. %s",
                                        len(model[0].values[i]),
                                        len(self.xticks))
                    xvals = model[0].values[i][:len(self.xticks)]
                else:
                    xvals = model[0].values[i]

                plt.plot(self.xticks,
                         xvals,
                         '--',
                         marker=self.kMarkStyles[i],
                         color="C{}".format(i + len(data_dfy.index)))

    def _plot_stats(self,
                    ax,
                    xticks,
                    data_dfy: pd.DataFrame,
                    stat_dfs: tp.Dict[str, pd.DataFrame]) -> None:
        """
        Plot statistics for all lines on the graph.
        """
        if self.stats in ['conf95', 'all'] and 'stddev' in stat_dfs.keys():
            for i in range(0, len(data_dfy.values)):
                # 95% interval = 2 std stdeviations
                plt.fill_between(xticks, data_dfy.values[i] - 2 * stat_dfs['stddev'].abs().values[i],
                                 data_dfy.values[i] + 2 *
                                 stat_dfs['stddev'].abs().values[i],
                                 alpha=0.25, color="C{}".format(i), interpolate=True)

        if self.stats in ['bw', 'all'] and all(k in stat_dfs.keys() for k in
                                               ['whislo',
                                                'whishi',
                                                'median',
                                                'q1',
                                                'q3',
                                                'cilo',
                                                'cihi']):
            for i in range(0, len(data_dfy.values)):
                boxes = []
                for j in range(0, len(data_dfy.columns)):
                    boxes.append({
                        # Bottom whisker position
                        'whislo': stat_dfs['whislo'].iloc[i, j],
                        # Top whisker position
                        'whishi': stat_dfs['whishi'].iloc[i, j],
                        # First quartile (25th percentile)
                        'q1': stat_dfs['q1'].iloc[i, j],
                        # Median         (50th percentile)
                        'med': stat_dfs['median'].iloc[i, j],
                        # Third quartile (75th percentile)
                        'q3': stat_dfs['q3'].iloc[i, j],
                        # Confidence interval lower bound
                        'cilo': stat_dfs['cilo'].iloc[i, j],
                        # Confidence interval upper bound
                        'cihi': stat_dfs['cihi'].iloc[i, j],
                        'fliers': []  # Ignoring outliers
                    })

                ax.bxp(boxes, manage_ticks=False,
                       positions=self.xticks, shownotches=True)

    def _plot_ticks(self, ax) -> None:
        if self.logyscale:
            ax.set_yscale('symlog', base=2)
            ax.yaxis.set_minor_formatter(mticker.ScalarFormatter())

            # Use scientific or decimal notation--whichever has fewer chars
            # ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.02g"))

        ax.tick_params(labelsize=self.text_size['tick_label'])

        # For ordered, qualitative data
        if self.xtick_labels is not None:
            ax.set_xticks(self.xticks)
            ax.set_xticklabels(self.xtick_labels, rotation='vertical')

    def _plot_legend(self, model: tp.Tuple[pd.DataFrame, tp.List[str]]) -> None:
        legend = self.legend

        if model[1]:
            legend = [val for pair in zip(self.legend, model[1])
                      for val in pair]

        plt.legend(legend,
                   fontsize=self.text_size['legend_label'],
                   ncol=max(1, int(len(legend) / 3.0)))

    def _read_stats(self) -> tp.Dict[str, list]:
        dfs = {}

        if self.stats in ['conf95', 'all']:
            stddev_ipath = os.path.join(self.stats_root,
                                        self.input_stem + config.kStatsExt['stddev'])

            if utils.path_exists(stddev_ipath):
                dfs['stddev'] = storage.DataFrameReader(
                    'storage.csv')(stddev_ipath)
            else:
                self.logger.warning("stddev file not found for '%s'",
                                    self.input_stem)

        if self.stats in ['bw', 'all']:
            whislo_ipath = os.path.join(self.stats_root,
                                        self.input_stem + config.kStatsExt['whislo'])
            whishi_ipath = os.path.join(self.stats_root,
                                        self.input_stem + config.kStatsExt['whishi'])
            median_ipath = os.path.join(self.stats_root,
                                        self.input_stem + config.kStatsExt['median'])
            q1_ipath = os.path.join(self.stats_root,
                                    self.input_stem + config.kStatsExt['q1'])
            q3_ipath = os.path.join(self.stats_root,
                                    self.input_stem + config.kStatsExt['q3'])

            cihi_ipath = os.path.join(self.stats_root,
                                      self.input_stem + config.kStatsExt['cihi'])
            cilo_ipath = os.path.join(self.stats_root,
                                      self.input_stem + config.kStatsExt['cilo'])

            if utils.path_exists(whislo_ipath):
                dfs['whislo'] = storage.DataFrameReader(
                    'storage.csv')(whislo_ipath)
            else:
                self.logger.warning(
                    "whislo file not found for '%s'", self.input_stem)

            if utils.path_exists(whishi_ipath):
                dfs['whishi'] = storage.DataFrameReader(
                    'storage.csv')(whishi_ipath)
            else:
                self.logger.warning(
                    "whishi file not found for '%s'", self.input_stem)

            if utils.path_exists(cilo_ipath):
                dfs['cilo'] = storage.DataFrameReader('storage.csv')(cilo_ipath)
            else:
                self.logger.warning(
                    "cilo file not found for '%s'", self.input_stem)

            if utils.path_exists(cihi_ipath):
                dfs['cihi'] = storage.DataFrameReader('storage.csv')(cihi_ipath)
            else:
                self.logger.warning(
                    "cihi file not found for '%s'", self.input_stem)

            if utils.path_exists(median_ipath):
                dfs['median'] = storage.DataFrameReader(
                    'storage.csv')(median_ipath)
            else:
                self.logger.warning(
                    "median file not found for '%s'", self.input_stem)

            if utils.path_exists(q1_ipath):
                dfs['q1'] = storage.DataFrameReader('storage.csv')(q1_ipath)
            else:
                self.logger.warning(
                    "q1 file not found for '%s'", self.input_stem)

            if utils.path_exists(q3_ipath):
                dfs['q3'] = storage.DataFrameReader('storage.csv')(q3_ipath)
            else:
                self.logger.warning(
                    "q3 file not found for '%s'", self.input_stem)

        return dfs

    def _read_models(self) -> tp.Tuple[pd.DataFrame, tp.List[str]]:
        if self.model_root is not None:
            self.logger.trace("Model root='%s',stem='%s'",   # type: ignore
                              self.model_root,
                              self.input_stem)

            model_fpath = os.path.join(
                self.model_root, self.input_stem + config.kModelsExt['model'])
            model_legend_fpath = os.path.join(
                self.model_root, self.input_stem + config.kModelsExt['legend'])

            if utils.path_exists(model_fpath):
                model = storage.DataFrameReader('storage.csv')(model_fpath)
                if utils.path_exists(model_legend_fpath):
                    with utils.utf8open(model_legend_fpath, 'r') as f:
                        model_legend = f.read().splitlines()
                else:
                    self.logger.warning(
                        "No legend file for model '%s' found", model_fpath)
                    model_legend = ['Model Prediction']

                return (model, model_legend)

        return (None, [])


__api__ = [
    'SummaryLineGraph'
]
