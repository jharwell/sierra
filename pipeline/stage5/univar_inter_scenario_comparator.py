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


import os
import pandas as pd
from graphs.batch_ranged_graph import BatchRangedGraph
from graphs.bar_graph import BarGraph

import perf_measures.common as pm_common
import utils
import copy
import yaml
import perf_measures.vcs


class UnivarInterScenarioComparator:
    """
    Compares controllers on different performance measures ACROSS different scenarios.
    """

    def __init__(self, controllers, graphs, sc_csv_root, sc_graph_root, cmdopts, main_config):
        self.cmdopts = cmdopts
        self.main_config = main_config
        self.controllers = controllers
        self.graphs = graphs

        self.sc_csv_root = sc_csv_root
        self.sc_graph_root = sc_graph_root

    def __call__(self, batch_criteria):
        for graph in self.graphs:
            self.__generate_graph(batch_criteria=batch_criteria,
                                  src_stem=graph['src_stem'],
                                  dest_stem=graph['dest_stem'],
                                  title=graph['title'])

    def __generate_graph(self, batch_criteria, src_stem, dest_stem, title):
        # We can do this because we have already checked that all controllers executed the same set
        # of batch experiments
        scenarios = batch_criteria.sort_scenarios(os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                                                          self.controllers[0])))

        swarm_sizes = []
        df = pd.DataFrame(columns=self.controllers, index=scenarios)

        for s in scenarios:
            cmdopts = copy.deepcopy(self.cmdopts)
            cmdopts['generation_root'] = os.path.join(self.cmdopts['sierra_root'],
                                                      self.controllers[0],
                                                      s,
                                                      "exp-inputs")
            cmdopts['n_exp'] = len(os.listdir(cmdopts['generation_root']))
            swarm_sizes = batch_criteria.swarm_sizes(cmdopts)
            for c in self.controllers:
                csv_ipath = os.path.join(self.cmdopts['sierra_root'],
                                         c,
                                         s,
                                         'exp-outputs',
                                         self.main_config['sierra']['collate_csv_leaf'],
                                         src_stem + ".csv")

                # Some experiments might not generate the necessary performance measure .csvs for
                # graph generation, which is OK.
                if not os.path.exists(csv_ipath):
                    continue
                df.loc[s, c] = pm_common.WeightUnifiedEstimate(input_csv_fpath=csv_ipath,
                                                               swarm_sizes=swarm_sizes).calc()

        csv_opath = os.path.join(self.sc_csv_root, 'sc-' +
                                 src_stem + "-wue.csv")
        df.to_csv(csv_opath, sep=';', index=False)

        scenarios = batch_criteria.sc_graph_labels(scenarios)

        BarGraph(input_fpath=csv_opath,
                 output_fpath=os.path.join(self.sc_graph_root,
                                           dest_stem + '-wue.png'),
                 title=title,
                 xlabels=scenarios).generate()
