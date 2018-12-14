"""
Copyright 2018 London Lowmanstone, John Harwell, All rights reserved.

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
from pipeline.intra_exp_linegraphs import IntraExpLinegraphs
from pipeline.intra_exp_histograms import IntraExpHistograms
from pipeline.intra_exp_heatmaps import IntraExpHeatmaps
from pipeline.intra_exp_targets import Linegraphs, Histograms, Heatmaps
import pandas as pd


class IntraExpGraphGenerator:
    """
    Generates common/basic graphs from averaged output data within a single experiment.

    Attributes:
      exp_output_root(str): Root directory (relative to current dir or absolute) for experiment
                            outputs.
      exp_graph_root(str): Root directory (relative to current dir or absolute) of where the
                           generated graphs should be saved for the experiment.
      generator(str): Fully qualified name of the generator used to create/run the experiments.
      with_hists(bool): If TRUE, then histograms will be generated.
      plot_applied_variances(bool): If TRUE, then plots of the temporal variances that were applied
                                    during simulation will be included in on relevant plots.
    """

    def __init__(self, exp_output_root, exp_graph_root, generator, with_hists,
                 plot_applied_variances):

        self.exp_output_root = os.path.abspath(os.path.join(exp_output_root, 'averaged-output'))
        self.exp_graph_root = os.path.abspath(exp_graph_root)
        self.generator = generator
        self.with_hists = with_hists
        self.plot_applied_variances = plot_applied_variances

        os.makedirs(self.exp_graph_root, exist_ok=True)

    def __call__(self):
        if 'depth2' in self.generator:
            keys = Linegraphs.all_target_keys()
        elif 'depth1' in self.generator:
            keys = Linegraphs.depth0_keys() + Linegraphs.depth1_keys()
        else:
            keys = Linegraphs.depth0_keys()

        targets = Linegraphs.filtered_targets(keys)
        if self.plot_applied_variances:
            self._add_temporal_variances(targets)

        IntraExpLinegraphs(self.exp_output_root,
                           self.exp_graph_root,
                           targets).generate()
        if self.with_hists:
            IntraExpHistograms(self.exp_output_root, self.exp_graph_root,
                               Histograms.all_targets()).generate()

        IntraExpHeatmaps(self.exp_output_root, self.exp_graph_root,
                         Heatmaps.all_targets()).generate()

    def _add_temporal_variances(self, targets):
        """

        Add column to the .csv files for some graphs and modify the graph dictionary so that so that
        the temporal variance can be graphed.
        """
        var_df = pd.read_csv(os.path.join(self.exp_output_root,
                                          IntraExpLinegraphs.kTemporalVarCSV),
                             sep=';')
        for graph_set in targets.values():
            for graph in graph_set:
                has_var = False

                for key in graph.keys():
                    # The 'temporal_var' is optional, so we only want to modify graph generation for
                    # those graphs that have requested it
                    if 'temporal_var' != key:
                        continue

                    has_var = True
                    target_df = pd.read_csv(os.path.join(self.exp_output_root,
                                                         graph['src_stem'] + ".csv"),
                                            sep=';')

                    # It is possible that different sets of columns within same .csv are used to
                    # generate graphs that should have the *same* variance graph on them, so we need
                    # to delete old column so the scaling works out correctly.
                    if graph['temporal_var'] in target_df.columns:
                        target_df = target_df.drop(graph['temporal_var'], axis=1)

                    # Find the maximum value among all the rows of all the columns that will be
                    # included in the graph. This is used for scaling the variance so it looks nice
                    # on the generated graphs.
                    m = 0
                    for c in target_df[graph['cols']]:
                        m = max(m, target_df[c].max())

                    # Scale the applied variance to within the interval [0, max] for the generated
                    # graph. The lower bound is always 0 for the fordyca project, so I rely on that
                    # here.
                    var = var_df[graph['temporal_var']][target_df['clock'] - 1].values
                    var = m * (var - var.min()) / (var.max() - var.min())

                    target_df.insert(1, graph['temporal_var'], var)
                    target_df.to_csv(os.path.join(self.exp_output_root,
                                                  graph['src_stem']) + ".csv", sep=';',
                                     index=False)
                if has_var:
                    graph['cols'].append(graph['temporal_var'])
                    graph['legend'].append('Temporal Variance (scaled)')
                    if 'styles' in graph:
                        graph['styles'].append('--')
