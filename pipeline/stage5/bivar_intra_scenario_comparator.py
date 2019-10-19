# Copyright 2019 John Harwell, All rights reserved.
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
from graphs.stacked_surface_graph import StackedSurfaceGraph
import copy
import typing as tp
import variables.batch_criteria as bc


class BivarIntraScenarioComparator:
    """
    Compares a set of controllers on different performance measures in all scenarios, one at a
    time. Which performance measures to generate graphs from for all controllers in a single
    scenario is controlled via a config file.
    """

    def __init__(self,
                 controllers: tp.List[str],
                 graphs: dict,
                 cc_csv_root: str,
                 cc_graph_root: str,
                 cmdopts: tp.Dict[str, str],
                 main_config: dict,
                 norm_comp: bool):
        self.cmdopts = cmdopts
        self.main_config = main_config
        self.controllers = controllers
        self.graphs = graphs
        self.norm_comp = norm_comp

        self.cc_csv_root = cc_csv_root
        self.cc_graph_root = cc_graph_root

    def __call__(self, batch_criteria: bc.UnivarBatchCriteria):
        # Obtain the list of scenarios to use. We can just take the scenario list of the first
        # controllers, because we have already checked that all controllers executed the same set
        # scenarios
        scenarios = os.listdir(os.path.join(self.cmdopts['sierra_root'], self.controllers[0]))

        # For each controller comparison graph we are interested in, generate it using data from all
        # scenarios
        for graph in self.graphs:
            for s in scenarios:
                self.__gen_csvs(scenario=s,
                                src_stem=graph['src_stem'],
                                dest_stem=graph['dest_stem'])

                self.__gen_graph(scenario=s,
                                 batch_criteria=batch_criteria,
                                 src_stem=graph['src_stem'],
                                 dest_stem=graph['dest_stem'],
                                 title=graph['title'],
                                 zlabel=graph['label'])

    def __gen_graph(self,
                    scenario: str,
                    batch_criteria: bc.UnivarBatchCriteria,
                    src_stem: str,
                    dest_stem: str,
                    title: str,
                    zlabel: str):
        """
        Generates a :meth:`StackedSurfaceGraph` comparing the specified controllers within the
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
        batch_criteria.set_batch_generation_root(batch_generation_root)

        cmdopts['generation_root'] = batch_generation_root
        cmdopts['output_root'] = batch_output_root

        StackedSurfaceGraph(input_stem_pattern=csv_stem_opath,
                            output_fpath=os.path.join(self.cc_graph_root,
                                                      dest_stem) + '-' + scenario + ".png",
                            title=title,
                            zlabel=zlabel,
                            xtick_labels=batch_criteria.graph_xticklabels(cmdopts),
                            ytick_labels=batch_criteria.graph_yticklabels(cmdopts),
                            legend=self.controllers,
                            norm_comp=self.norm_comp).generate()

    def __gen_csvs(self,
                   scenario: str,
                   src_stem: str,
                   dest_stem: str):
        """
        Generates a set of .csv files for use in intra-scenario graph generation (1 per
        controller). Because each ``.csv`` file corresponding to performance measures are 2D arrays,
        and we are generating :meth:`StackedSurfaceGraph`s, we actually just copy and rename the
        performance measure ``.csv`` files for each controllers into ``cc-csvs``.

        :meth:`StackedSurfaceGraph` expects an ``_[0-9]+.csv`` pattern for each 2D surfaces to graph
        in order to disambiguate which files belong to which controller without having the
        controller name in the filepath (contains dots), so we do that here.

        """
        for c in self.controllers:
            csv_ipath = os.path.join(self.cmdopts['sierra_root'],
                                     c,
                                     scenario,
                                     'exp-outputs',
                                     self.main_config['sierra']['collate_csv_leaf'],
                                     src_stem + ".csv")

            # Some experiments might not generate the necessary performance measure .csvs for
            # graph generation, which is OK.
            if not os.path.exists(csv_ipath):
                continue

            df = pd.read_csv(csv_ipath, sep=';')

            csv_opath_stem = os.path.join(self.cc_csv_root,
                                          dest_stem + "-" + scenario + '_' + str(self.controllers.index(c)))

            df.to_csv(csv_opath_stem + '.csv', sep=';', index=False)
