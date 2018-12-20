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
import copy
from pipeline.intra_exp_linegraphs import IntraExpLinegraphs
from pipeline.intra_exp_histograms import IntraExpHistograms
from pipeline.intra_exp_heatmaps import IntraExpHeatmaps
from pipeline.intra_exp_targets import Linegraphs, Histograms, Heatmaps
import pandas as pd


class IntraExpGraphGenerator:
    """
    Generates common/basic graphs from averaged output data within a single experiment.

    Attributes:
      cmdopts(dict): Dictionary of commandline arguments used during intra-experiment graph
                     generation.
    """

    def __init__(self, cmdopts):
        self.cmdopts = copy.deepcopy(cmdopts)
        self.cmdopts["output_root"] = os.path.join(self.cmdopts["output_root"], 'averaged-output')

        os.makedirs(self.cmdopts["graph_root"], exist_ok=True)

    def __call__(self):
        if 'depth2' in self.cmdopts["generator"]:
            keys = Linegraphs.all_target_keys()
        elif 'depth1' in self.cmdopts["generator"]:
            keys = Linegraphs.depth0_keys() + Linegraphs.depth1_keys()
        else:
            keys = Linegraphs.depth0_keys()

        targets = Linegraphs.filtered_targets(keys)
        if self.cmdopts["plot_applied_variances"]:
            self._add_temporal_variances(targets)

        IntraExpLinegraphs(self.cmdopts["output_root"],
                           self.cmdopts["graph_root"],
                           targets).generate()
        if self.cmdopts["with_hists"]:
            IntraExpHistograms(self.cmdopts["output_root"], self.cmdopts["graph_root"],
                               Histograms.all_targets()).generate()

        IntraExpHeatmaps(self.cmdopts["output_root"], self.cmdopts["graph_root"],
                         Heatmaps.all_targets()).generate()

    def _add_temporal_variances(self, targets):
        """

        Add column to the .csv files for some graphs and modify the graph dictionary so that so that
        the temporal variance can be graphed.
        """
        var_df = pd.read_csv(os.path.join(self.cmdopts["ouput_root"],
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
                    target_df = pd.read_csv(os.path.join(self.cmdopts["ouput_root"],
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
                    target_df.to_csv(os.path.join(self.cmdopts["ouput_root"],
                                                  graph['src_stem']) + ".csv", sep=';',
                                     index=False)
                if has_var:
                    graph['cols'].append(graph['temporal_var'])
                    graph['legend'].append('Temporal Variance (scaled)')
                    if 'styles' in graph:
                        graph['styles'].append('--')
