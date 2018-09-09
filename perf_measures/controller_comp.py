"""
 Copyright 2018 John Harwell, All rights reserved.

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
import pandas as pd
from graphs.ranged_size_graph import RangedSizeGraph
from graphs.bar_graph import BarGraph
import perf_measures.utils as pm_utils

intra_scenario_measures = [
    {
        'src_stem': 'pm-scalability-comp',
        'dest_stem': 'cc-pm-scalability-comp',
        'title': 'Swarm Scalability (Comparitive)',
        'ylabel': 'Scalability Value'
    },
    {
        'src_stem': 'pm-scalability-fl',
        'dest_stem': 'cc-pm-scalability-fl',
        'title': 'Swarm Scalability (Sub-Linear Fractional Losses)',
        'ylabel': 'Scalability Value'
    },
    {
        'src_stem': 'pm-scalability-norm',
        'dest_stem': 'cc-pm-scalability-norm',
        'title': 'Swarm Scalability (Normalized)',
        'ylabel': 'Scalability Value'
    },
    {
        'src_stem': 'pm-self-org',
        'dest_stem': 'cc-pm-self-org',
        'title': 'Swarm Self Organization',
        'ylabel': 'Self Organization Value'
    },
    {
        'src_stem': 'pm-blocks-collected',
        'dest_stem': 'cc-pm-blocks-collected',
        'title': 'Swarm Total Blocks Collected',
        'ylabel': '# Blocks'
    },
]

inter_scenario_measures = [
    {
        'src_stem': 'pm-scalability-fl',
        'dest_stem': 'sc-pm-scalability-fl',
        'title': 'Weight Unified Swarm Scalability (Sub-Linear Fractional Losses)',
    },
    {
        'src_stem': 'pm-scalability-norm',
        'dest_stem': 'sc-pm-scalability-norm',
        'title': 'Weight Unified Swarm Scalability (Normalized)',
    },
    {
        'src_stem': 'pm-self-org',
        'dest_stem': 'sc-pm-self-org',
        'title': 'Weight Unified Swarm Self Organization',
    },
    {
        'src_stem': 'pm-blocks-collected',
        'dest_stem': 'sc-pm-blocks-collected',
        'title': 'Weight Unified Blocks Collected',
    },

]


class ControllerComp:
    """
    Compares controllers on different criteria across/within different scenarios.
    """

    def __init__(self, sierra_root, controllers, batch_criteria):
        self.sierra_root = sierra_root
        self.controllers = controllers
        self.batch_criteria = batch_criteria
        self.cc_graph_root = os.path.join(sierra_root, "cc-graphs")
        self.cc_csv_root = os.path.join(sierra_root, "cc-csvs")
        self.sc_graph_root = os.path.join(sierra_root, "sc-graphs")
        self.sc_csv_root = os.path.join(sierra_root, "sc-csvs")

    def generate(self):
        self.generate_intra_scenario_graphs()
        self.generate_inter_scenario_graphs()

    def generate_inter_scenario_graphs(self):
        """
        Calculate weight unified estimates of:

        - Swarm scalability
        - Swarm self-organization

        ACROSS scenarios
        """

        for m in inter_scenario_measures:
            self._generate_inter_scenario_graph(src_stem=m['src_stem'],
                                                dest_stem=m['dest_stem'],
                                                title=m['title'])

    def _generate_inter_scenario_graph(self, src_stem, dest_stem, title):
        # We can do this because we have already checked that all controllers executed the same set
        # of batch experiments
        scenarios = os.listdir(os.path.join(self.sierra_root, self.controllers[0]))
        swarm_sizes = []
        df = pd.DataFrame(columns=self.controllers, index=scenarios)

        for s in scenarios:
            generation_root = os.path.join(self.sierra_root,
                                           self.controllers[0],
                                           s,
                                           "exp-inputs")
            swarm_sizes = pm_utils.calc_swarm_sizes(self.batch_criteria,
                                                    generation_root,
                                                    len(os.listdir(generation_root)))
            for c in self.controllers:
                csv_ipath = os.path.join(self.sierra_root,
                                         c,
                                         s,
                                         "exp-outputs/collated-csvs",
                                         src_stem + ".csv")
                df.loc[s, c] = pm_utils.WeightUnifiedEstimate(input_csv_fpath=csv_ipath,
                                                              swarm_sizes=swarm_sizes).calc()
            csv_opath = os.path.join(self.sc_csv_root, 'sc-' +
                                     src_stem + "-" + s + ".csv")
            df.to_csv(csv_opath, sep=';', index=False)

        BarGraph(input_fpath=csv_opath,
                 output_fpath=os.path.join(self.sc_graph_root,
                                           dest_stem + '-wue.eps'),
                 title=title,
                 xlabels=scenarios).generate()

    def generate_intra_scenario_graphs(self):
        """
        Calculate controller comparison metrics WITHIN a scenario:

        - Swarm scalability
        - Swarm self-organization
        """
        for m in intra_scenario_measures:
            self._generate_intra_scenario_graph(src_stem=m['src_stem'],
                                                dest_stem=m['dest_stem'],
                                                title=m['title'],
                                                ylabel=m['ylabel'])

    def _generate_intra_scenario_graph(self, src_stem, dest_stem, title, ylabel):

        # We can do this because we have already checked that all controllers executed the same set
        # of batch experiments
        scenarios = os.listdir(os.path.join(self.sierra_root, self.controllers[0]))
        for s in scenarios:
            df = pd.DataFrame()
            for c in self.controllers:
                csv_ipath = os.path.join(self.sierra_root,
                                         c,
                                         s,
                                         "exp-outputs/collated-csvs",
                                         src_stem + ".csv")
                df = df.append(pd.read_csv(csv_ipath, sep=';'))
                csv_opath = os.path.join(self.cc_csv_root, 'cc-' +
                                         src_stem + "-" + s + ".csv")
                df.to_csv(csv_opath, sep=';', index=False)

        for s in scenarios:
            csv_opath = os.path.join(self.cc_csv_root, 'cc-' +
                                     src_stem + "-" + s + ".csv")

            # All exp have same # experiments, so we can do this safely.
            batch_generation_root = os.path.join(self.sierra_root,
                                                 self.controllers[0],
                                                 s,
                                                 "exp-inputs")

            RangedSizeGraph(inputy_fpath=csv_opath,
                            output_fpath=os.path.join(self.cc_graph_root,
                                                      dest_stem) + "-rng-" + s + ".eps",
                            title=title,
                            ylabel=ylabel,
                            xvals=pm_utils.calc_swarm_sizes(self.batch_criteria,
                                                            batch_generation_root,
                                                            len(df.columns)),
                            legend=self.controllers).generate()
