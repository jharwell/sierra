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
import math
import numpy as np
from graphs.stacked_line_graph import StackedLineGraph
from graphs.scalability_graph import ScalabilityGraph

kTargetIntCSV = "blocks-collected-int.csv"
kTargetCumCSV = "blocks-collected-cum.csv"


class InterExpScalabilityMeasure:
    """
    Calculates the scalability of the swarm configuration across a batched set of experiments within
    the same scenario from collated .csv data.

    Assumes:
    - The batch criteria used to generate the experiment definitions was swarm size, logarithmic,
      and that the swarm size for exp0 was 1.
    - The performance criteria is # blocks gathered.
    - (robustness): No robot failures occur, and no sensor/actuator noise is present.
    - (flexibility): Arena size/shape is the same across all experiments
    - (Reactivity): No temporal variance of environmental conditions/robot capabilities/etc is
                    present.

    """

    def __init__(self, batch_output_root, batch_graph_root):
        self.batch_output_root = batch_output_root
        self.batch_graph_root = batch_graph_root

    def generate(self):
        """Calculate the scalability metric within each interval for a given controller,
        and output a nice graph."""

        path = os.path.join(self.batch_output_root, kTargetIntCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock', 'exp0']]
        for c in scale_cols:
            df[c] = (df[c] / ((math.pow(2, int(c[3:]))) * df['exp0'])).replace(np.inf, 0)
        df = df.drop(['exp0'], 1)
        int_stem = os.path.join(self.batch_output_root, "pm-scalability-int")
        df.to_csv(int_stem + ".csv", sep=';', index=False)

        path = os.path.join(self.batch_output_root, kTargetCumCSV)
        assert(os.path.exists(path)), "FATAL: {0} does not exist".format(path)
        df = pd.read_csv(path, sep=';')
        scale_cols = [c for c in df.columns if c not in ['clock', 'exp0']]
        cum_stem = os.path.join(self.batch_output_root, "pm-scalability-cum")
        df_new = pd.DataFrame(columns=scale_cols)
        for c in scale_cols:
            df_new[c] = df.tail(1)[c] / (df.tail(1)['exp0'] * 2 ** (int(c[3:])))

        df_new.to_csv(cum_stem + ".csv", sep=';', index=False)

        StackedLineGraph(input_stem_fpath=int_stem,
                         output_fpath=os.path.join(self.batch_graph_root,
                                                   "pm-scalability-int.eps"),
                         cols=None,
                         title="Swarm Scalability (interval)",
                         legend=None,
                         xlabel="Timestep",
                         ylabel="Scalability").generate()

        ScalabilityGraph(inputy_fpath=cum_stem + ".csv",
                         output_fpath=os.path.join(self.batch_graph_root,
                                                   "pm-scalability-cum.eps")).generate()


class ControllerCompScalabilityMeasure:
    """
    Calculates the scalability of the swarm configuration across controllers that have all run the
    same experiment set.

    Assumes:
    - The batch criteria used to generate the experiment definitions was swarm size, logarithmic,
      and that the swarm size for exp0 was 1.
    - The performance criteria is # blocks gathered.
    - (robustness): No robot failures occur, and no sensor/actuator noise is present.
    - (flexibility): Arena size/shape is the same across all experiments
    - (Reactivity): No temporal variance of environmental conditions/robot capabilities/etc is
                    present.

    """

    def __init__(self, sierra_root, controllers, src_stem, dest_stem, title, xlabel, ylabel):
        self.sierra_root = sierra_root
        self.controllers = controllers
        self.src_stem = src_stem
        self.dest_stem = dest_stem
        self.title = title
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.comp_graph_root = os.path.join(sierra_root, "comp-graphs")
        self.comp_csv_root = os.path.join(sierra_root, "comp-csvs")

        os.makedirs(self.comp_graph_root, exist_ok=True)
        os.makedirs(self.comp_csv_root, exist_ok=True)

    def generate(self):
        """
        Calculate the scalability metric comparing controllers, and output a nice graph.

        """

        # We can do this because we have already checked that all controllers executed the same set
        # of batch experiments
        print(self.controllers)
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
            ScalabilityGraph(inputy_fpath=csv_opath,
                             output_fpath=os.path.join(self.comp_graph_root,
                                                       self.dest_stem) + "-" + s + ".eps",
                             legend=self.controllers).generate()
