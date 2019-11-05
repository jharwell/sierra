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
import copy
import logging
import typing as tp
import pandas as pd

from graphs.stacked_surface_graph import StackedSurfaceGraph
import variables.batch_criteria as bc
import pipeline.root_dirpath_generator as rdg


class BivarIntraScenarioComparator:
    """
    Compares a set of controllers on different performance measures in all scenarios, one at a
    time. Which performance measures to generate graphs from for all controllers in a single
    scenario is controlled via a config file.
    """

    def __init__(self,
                 controllers: tp.List[str],
                 cc_csv_root: str,
                 cc_graph_root: str,
                 cmdopts: tp.Dict[str, str],
                 cli_args: dict,
                 main_config: dict,
                 ):
        self.controllers = controllers
        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config
        self.cc_csv_root = cc_csv_root
        self.cc_graph_root = cc_graph_root

    def __call__(self,
                 graphs: dict,
                 legend: tp.List[str],
                 norm_comp: bool):
        # Obtain the list of scenarios to use. We can just take the scenario list of the first
        # controllers, because we have already checked that all controllers executed the same set
        # scenarios.
        dirs = os.listdir(os.path.join(self.cmdopts['sierra_root'], self.controllers[0]))
        scenarios = [rdg.parse_batch_root(d)[1] for d in dirs]

        cmdopts = copy.deepcopy(self.cmdopts)
        # For each controller comparison graph we are interested in, generate it using data from all
        # scenarios
        for graph in graphs:
            for s in scenarios:
                for controller in self.controllers:
                    dirs = [d for d in os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                                               controller)) if s in d]

                    if 0 == len(dirs):
                        logging.warning("No graph generated")
                        continue

                    # We need to generate the root directory paths for each batched experiment
                    # (which # lives inside of the scenario dir), because they are all
                    # different. We need generate these paths for EACH controller, because the
                    # controller is part of the batch root.
                    paths = rdg.regen_from_exp(self.cli_args.sierra_root,
                                               self.cli_args.batch_criteria,
                                               dirs[0],
                                               controller)
                    cmdopts.update(paths)

                    # For each scenario, we have to create the batch criteria for it, because they
                    # are all different.
                    criteria = bc.Factory(self.cli_args,
                                          cmdopts,
                                          dirs[0])

                    self.__gen_csv(cmdopts=cmdopts,
                                   controller=controller,
                                   batch_root=dirs[0],
                                   src_stem=graph['src_stem'],
                                   dest_stem=graph['dest_stem'])

                self.__gen_graph(scenario=rdg.parse_batch_root(dirs[0])[1],
                                 batch_criteria=criteria,
                                 cmdopts=cmdopts,
                                 dest_stem=graph['dest_stem'],
                                 title=graph['title'],
                                 zlabel=graph['label'],
                                 legend=legend,
                                 norm_comp=norm_comp)

    def __gen_graph_title(self, title: str, norm_comp: bool):
        """
        If we are normalizing comparisons, put that on the graph title.
        """
        if norm_comp:
            return title + ' (Normalized)'
        return title

    def __gen_graph(self,
                    scenario: str,
                    batch_criteria: bc.UnivarBatchCriteria,
                    cmdopts: tp.Dict[str, str],
                    dest_stem: str,
                    title: str,
                    zlabel: str,
                    legend: tp.List[str],
                    norm_comp: bool):
        """
        Generates a :class:`~graphs.stacked_surface_graph.StackedSurfaceGraph` comparing the
        specified controllers within thespecified scenario after input files have been gathered from
        each controllers into ``cc-csvs/``.
        """
        csv_stem_opath = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)
        StackedSurfaceGraph(input_stem_pattern=csv_stem_opath,
                            output_fpath=os.path.join(self.cc_graph_root,
                                                      dest_stem) + '-' + scenario + ".png",
                            title=self.__gen_graph_title(title, norm_comp),
                            ylabel=batch_criteria.graph_xlabel(cmdopts),
                            xlabel=batch_criteria.graph_ylabel(cmdopts),
                            zlabel=zlabel,
                            xtick_labels=batch_criteria.graph_yticklabels(cmdopts),
                            ytick_labels=batch_criteria.graph_xticklabels(cmdopts),
                            legend=legend,
                            norm_comp=norm_comp).generate()

    def __gen_csv(self,
                  cmdopts: tp.Dict[str, str],
                  batch_root: str,
                  controller: str,
                  src_stem: str,
                  dest_stem: str):
        """
        Helper function for generating a set of .csv files for use in intra-scenario graph
        generation (1 per controller). Because each ``.csv`` file corresponding to performance
        measures are 2D arrays, and we are generating :meth:`StackedSurfaceGraph`s, we actually just
        copy and rename the performance measure ``.csv`` files for each controllers into
        ``cc-csvs``.

        :meth:`StackedSurfaceGraph` expects an ``_[0-9]+.csv`` pattern for each 2D surfaces to graph
        in order to disambiguate which files belong to which controller without having the
        controller name in the filepath (contains dots), so we do that here.

        """
        csv_ipath = os.path.join(cmdopts['sierra_root'],
                                 controller,
                                 batch_root,
                                 'exp-outputs',
                                 self.main_config['sierra']['collate_csv_leaf'],
                                 src_stem + ".csv")

        # Some experiments might not generate the necessary performance measure .csvs for
        # graph generation, which is OK.
        if not os.path.exists(csv_ipath):
            return

        df = pd.read_csv(csv_ipath, sep=';')

        scenario = rdg.parse_batch_root(batch_root)[1]
        leaf = dest_stem + "-" + scenario + '_' + str(self.controllers.index(controller))

        csv_opath_stem = os.path.join(self.cc_csv_root, leaf)
        df.to_csv(csv_opath_stem + '.csv', sep=';', index=False)
