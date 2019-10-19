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
import copy
import variables.batch_criteria as bc
import typing as tp


class UnivarIntraScenarioComparator:
    """
    Compares a set of controllers on different performance measures in all scenarios, one at a
    time. Which performance measures to generate graphs from for all controllers in a single
    scenario is controlled via a config file.
    """

    def __init__(self, controllers: tp.List[str],
                 graphs: dict,
                 cc_graph_root: str,
                 cc_csv_root: str,
                 main_config: dict,
                 cmdopts: tp.Dict[str, str]):
        self.cmdopts = cmdopts
        self.main_config = main_config
        self.controllers = controllers
        self.graphs = graphs

        self.cc_graph_root = cc_graph_root
        self.cc_csv_root = cc_csv_root

    def __call__(self, batch_criteria: bc.UnivarBatchCriteria):
        # Obtain the list of scenarios to use. We can just take the scenario list of the first
        # controllers, because we have already checked that all controllers executed the same set
        # scenarios
        scenarios = os.listdir(os.path.join(self.cmdopts['sierra_root'], self.controllers[0]))

        # For each controller comparison graph we are interested in, generate it using data from all
        # scenarios
        for graph in self.graphs:
            for s in scenarios:
                self.__gen_csv(scenario=s,
                               src_stem=graph['src_stem'],
                               dest_stem=graph['dest_stem'])

                self.__gen_graph(batch_criteria=batch_criteria,
                                 src_stem=graph['src_stem'],
                                 dest_stem=graph['dest_stem'],
                                 title=graph['title'],
                                 ylabel=graph['label'])

    def __gen_graph(self,
                    scenario: str,
                    batch_criteria: bc.UnivarBatchCriteria,
                    src_stem: str,
                    dest_stem: str,
                    title: str,
                    label: str):
        """
        Generates a :meth:`BatchRangeGraph` comparing the specified controllers within the
        specified scenario after input files have been gathered from each controllers into
        ``cc-csvs/``.
        """
        csv_stem_opath = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)

        # All scenarios are NOT guaranteed to have the same # of experiments, so we need to
        # overwrite key elements of the cmdopts in order to ensure proper processing.
        cmdopts = copy.deepcopy(self.cmdopts)
        batch_generation_root = os.path.join(self.cmdopts['sierra_root'],
                                             self.controllers[0],
                                             scenario,
                                             "exp-inputs")
        batch_output_root = os.path.join(self.cmdopts['sierra_root'],
                                         self.controllers[0],
                                         scenario,
                                         "exp-outputs")
        cmdopts['generation_root'] = batch_generation_root
        cmdopts['output_root'] = batch_output_root

        BatchRangedGraph(inputy_stem_fpath=csv_stem_opath,
                         output_fpath=os.path.join(self.cc_graph_root,
                                                   dest_stem) + '-' + scenario + ".png",
                         title=title,
                         xlabel=batch_criteria.graph_xlabel(cmdopts),
                         ylabel=label,
                         xvals=batch_criteria.graph_xticks(cmdopts),
                         legend=self.controllers,
                         polynomial_fit=-1).generate()

    def __gen_csv(self, scenario: str,
                  src_stem: str,
                  dest_stem: str):
        """
        Generates a set of .csv files for use in intra-scenario graph generation (1 per
        controller).

        """

        df = pd.DataFrame()
        stddev_df = pd.DataFrame()

        for c in self.controllers:
            csv_ipath = os.path.join(self.cmdopts['sierra_root'],
                                     c,
                                     scenario,
                                     'exp-outputs',
                                     self.main_config['sierra']['collate_csv_leaf'],
                                     src_stem + ".csv")
            stddev_ipath = os.path.join(self.cmdopts['sierra_root'],
                                        c,
                                        scenario,
                                        'exp-outputs',
                                        self.main_config['sierra']['collate_csv_leaf'],
                                        src_stem + ".stddev")

            # Some experiments might not generate the necessary performance measure .csvs for
            # graph generation, which is OK.
            if not os.path.exists(csv_ipath):
                continue

            df = df.append(pd.read_csv(csv_ipath, sep=';'))
            if os.path.exists(stddev_ipath):
                stddev_df = stddev_df.append(pd.read_csv(stddev_ipath, sep=';'))

        csv_opath_stem = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)

        df.to_csv(csv_opath_stem + '.csv', sep=';', index=False)

        if not stddev_df.empty:
            stddev_df.to_csv(csv_opath_stem + '.stddev', sep=';', index=False)
