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
import pandas as pd
import numpy as np
import yaml

from pipeline.intra_exp_linegraphs import IntraExpLinegraphs
from pipeline.intra_exp_histograms import IntraExpHistograms
from pipeline.intra_exp_heatmaps import IntraExpHeatmaps


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
        self.linegraph_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                            'intra-graphs-line.yaml')))
        self.hm_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                     'intra-graphs-hm.yaml')))

        self.controller_config = yaml.load(open(os.path.join(self.cmdopts['config_root'],
                                                             'controllers.yaml')))

    def __call__(self):
        for category in list(self.controller_config.keys()):
            if category not in self.cmdopts['generator']:
                continue
            for controller in self.controller_config[category]['controllers']:
                if controller['name'] not in self.cmdopts['generator']:
                    continue
                keys = controller['graphs']
                if 'graphs_inherit' in controller:
                    [keys.extend(l) for l in controller['graphs_inherit']]  # optional

        filtered_keys = [k for k in self.linegraph_config if k in keys]
        targets = [self.linegraph_config[k] for k in filtered_keys]
        self._add_temporal_variances(targets)

        IntraExpLinegraphs(self.cmdopts["output_root"],
                           self.cmdopts["graph_root"],
                           targets).generate()
        # if self.cmdopts["with_hists"]:
        #     IntraExpHistograms(self.cmdopts["output_root"], self.cmdopts["graph_root"],
        #                        Histograms.all_targets()).generate()

        filtered_keys = [k for k in self.hm_config if k in keys]
        targets = [self.hm_config[k] for k in filtered_keys]
        IntraExpHeatmaps(self.cmdopts["output_root"],
                         self.cmdopts["graph_root"],
                         targets).generate()

    def _add_temporal_variances(self, targets):
        """

        Add column to the .csv files for some graphs and modify the graph dictionary so that so that
        the temporal variance can be graphed.
        """
        var_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                          IntraExpLinegraphs.kTemporalVarCSV),
                             sep=';')

        # For each category of graphs we are generating
        for category in targets:
            # For each graph in each category
            for graph in category['graphs']:
                # For each individual graph in each graph set
                for key in graph.keys():
                    # The 'temporal_var' key is optional, so we only want to modify graph
                    # generation for those graphs that have requested it.
                    if 'temporal_var' != key:
                        continue

                    target_df = pd.read_csv(os.path.join(self.cmdopts["output_root"],
                                                         graph['src_stem'] + ".csv"),
                                            sep=';')

                    for col in graph['temporal_var']:
                        added = self._add_temporal_variance_cols(target_df, var_df, graph, col)

                        # OK to disable static checking here because I *know* the graphs are
                        # hardcoded before runtime and the selected attributes *are* lists.
                        graph['cols'].extend(  # pytype: disable=attribute-error
                            [a for a in added for c in graph['cols'] if c in a])

                        graph['legend'].extend(  # pytype: disable=attribute-error
                            ['Applied Variance (scaled {0})'.format(x) for x in added])
                        if 'styles' in graph:
                            graph['styles'].extend(  # pytype: disable=attribute-error
                                ['--' for x in range(0, len(added))])

    def _add_temporal_variance_cols(self, target_df, var_df, graph, col):
        added = []

        # Need a copy because we modify columns as we iterate over it.
        #
        # We need to be sure that we don't generate variance columns for clock (duh), but also check
        # that we don't generate variance columns for columns that are themselves the result of a
        # previous invocation of this function (can happen if there are multiple types of temporal
        # variance included on a single plot).
        orig_cols = [c for c in target_df.columns if c not in 'clock' and col not in c]

        for c in orig_cols:
            m = target_df[c].max()

            # Scale the applied variance to within the interval [0, max] for the generated
            # graph. The lower bound is always 0 for the fordyca project, so I rely on that
            # here.
            var = var_df[col].reindex(index=target_df['clock'] - 1).values

            var = m * (var - var.min()) / (var.max() - var.min())

            # Only include variance if it is non-zero for at least some of the time, and is an
            # actual # (can be NaN if it is a type of variance we want to include on plots in
            # general, but that is not enabled for the current experiment)

            if not np.any(var) or any(np.isnan(var)):
                continue

            new_col = c + "_" + col
            added.append(new_col)

            # Can happen if we run graph generation more than once on the same experiment
            if new_col in target_df.columns:
                continue

            target_df.insert(1, new_col, var)

        target_df.to_csv(os.path.join(self.cmdopts["output_root"],
                                      graph['src_stem']) + ".csv", sep=';',
                         index=False)
        return added
