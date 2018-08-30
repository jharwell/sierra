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
from perf_measures.utils import FractionalLosses


class InterExpEmergenceMeasure:
    """
    Calculates the emergence of the swarm configuration across a batched set of experiments within
    the same scenario from collated .csv data.

    Assumes:
    - The batch criteria used to generate the experiment definitions was swarm size, logarithmic,
      and that the swarm size for exp0 was 1.
    - The performance criteria is # blocks gathered.
    - The only source of interference is that from collision avoidance.
    - (robustness): No robot failures occur, and no sensor/actuator noise is present.
    - (flexibility): Arena size/shape is the same across all experiments.
    - (reactivity): No temporal variance of environmental conditions/robot capabilities/etc is
                    present.
    """

    def __init__(self, batch_output_root, batch_graph_root, batch_generation_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root
        self.batch_generation_root = batch_generation_root

    def generate(self):
        """
        Calculate the emergence metric for a given controller, and output a
        nice graph.
        """

        df = FractionalLosses(self.batch_output_root, self.batch_generation_root).calc()
        df_new = pd.DataFrame(columns=[c for c in df.columns if c not in ['exp0']])

        for i in range(1, len(df.columns)):
            df_new['exp' + str(i)] = - (df['exp' + str(i)] - 2 * df['exp' + str(i - 1)])

        int_path = os.path.join(self.batch_output_root, "pm-emergence.csv")
        df.to_csv(int_path, sep=';', index=False)

        RangedSizeGraph(inputy_fpath=int_path,
                        output_fpath=os.path.join(self.batch_graph_root,
                                                  "pm-emergence.eps"),
                        title="Swarm Emergence Due To Sub-Linear Fractional Performance Losses",
                        legend=None,
                        ylabel="").generate()


class ControllerCompEmergenceMeasure:
    """
    Calculates the emergence of the swarm configuration across controllers that have all run the
    same experiment set.
    """

    def __init__(self, sierra_root, controllers, src_stem, dest_stem, ):
        self.sierra_root = sierra_root
        self.controllers = controllers
        self.src_stem = src_stem
        self.dest_stem = dest_stem
        self.comp_graph_root = os.path.join(sierra_root, "comp-graphs")
        self.comp_csv_root = os.path.join(sierra_root, "comp-csvs")

    def generate(self):
        """
        Calculate the scalability metric comparing controllers, and output a nice graph.

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
                df.to_csv(csv_opath, sep=';')

        for s in scenarios:
            print("-- Scenario {0}".format(s))
            csv_opath = os.path.join(self.comp_csv_root, 'comp-' +
                                     self.src_stem + "-" + s + ".csv")

            RangedSizeGraph(inputy_fpath=csv_opath,
                            output_fpath=os.path.join(self.comp_graph_root,
                                                      self.dest_stem) + "-" + s + ".eps",
                            title="Swarm Emergence",
                            ylabel="Emergence Value",
                            legend=self.controllers).generate()
