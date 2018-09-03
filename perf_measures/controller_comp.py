"""
 Copyright 2018 John Harwell, All rights reserved.

This file is part of SIERRA.
nnnnn
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

measures = [
    {
        'src_stem': 'pm-scalability-comp',
        'dest_stem': 'comp-pm-scalability-comp',
        'title': 'Swarm Scalability (Comparitive)',
        'ylabel': 'Scalability Value'
    },
    {
        'src_stem': 'pm-scalability-fl',
        'dest_stem': 'comp-pm-scalability-fl',
        'title': 'Swarm Scalability (Sub-Linear Fractional Losses)',
        'ylabel': 'Scalability Value'
    },
    {
        'src_stem': 'pm-scalability-norm',
        'dest_stem': 'comp-pm-scalability-norm',
        'title': 'Swarm Scalability (Normalized)',
        'ylabel': 'Scalability Value'
    },
    {
        'src_stem': 'pm-self-org',
        'dest_stem': 'comp-pm-self-org',
        'title': 'Swarm Self Organization',
        'ylabel': 'Self Organization Value'
    },
    {
        'src_stem': 'pm-blocks-collected',
        'dest_stem': 'comp-pm-blocks-collected',
        'title': 'Swarm Total Blocks Collected',
        'ylabel': '# Blocks'
    },

]


class ControllerComp:
    """
    Compares controllers on some specified criteria across different scenarios.
    """

    def __init__(self, sierra_root, controllers, src_stem, dest_stem, title, ylabel):
        self.sierra_root = sierra_root
        self.controllers = controllers
        self.src_stem = src_stem
        self.dest_stem = dest_stem
        self.title = title
        self.ylabel = ylabel
        self.comp_graph_root = os.path.join(sierra_root, "comp-graphs")
        self.comp_csv_root = os.path.join(sierra_root, "comp-csvs")

    def generate(self):
        """
        Calculate the metric comparing controllers, and output a nice graph.

        """

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
                                         self.src_stem + ".csv")
                df = df.append(pd.read_csv(csv_ipath, sep=';'))
                csv_opath = os.path.join(self.comp_csv_root, 'comp-' +
                                         self.src_stem + "-" + s + ".csv")
                df.to_csv(csv_opath, sep=';', index=False)

        for s in scenarios:
            csv_opath = os.path.join(self.comp_csv_root, 'comp-' +
                                     self.src_stem + "-" + s + ".csv")

            RangedSizeGraph(inputy_fpath=csv_opath,
                            output_fpath=os.path.join(self.comp_graph_root,
                                                      self.dest_stem) + "-" + s + ".eps",
                            title=self.title,
                            ylabel=self.ylabel,
                            legend=self.controllers).generate()
