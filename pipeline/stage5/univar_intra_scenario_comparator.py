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
import copy
import pandas as pd
from graphs.batch_ranged_graph import BatchRangedGraph
import variables.batch_criteria as bc
import typing as tp
import pipeline.root_dirpath_generator as rdg


class UnivarIntraScenarioComparator:
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
                 cli_args,
                 main_config,
                 norm_comp):
        self.controllers = controllers
        self.graphs = graphs
        self.cc_graph_root = cc_graph_root
        self.cc_csv_root = cc_csv_root

        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config
        self.norm_comp = norm_comp

    def __call__(self):
        # Obtain the list of scenarios to use. We can just take the scenario list of the first
        # controllers, because we have already checked that all controllers executed the same set
        # scenarios
        scenarios = os.listdir(os.path.join(self.cmdopts['sierra_root'], self.controllers[0]))

        # For each controller comparison graph we are interested in, generate it using data from all
        # scenarios
        cmdopts = copy.deepcopy(self.cmdopts)
        for graph in self.graphs:
            for s in scenarios:
                for controller in self.controllers:
                    # We need to generate the root directory paths for each batched experiment
                    # (which # lives inside of the scenario dir), because they are all
                    # different. We need generate these paths for EACH controller, because the
                    # controller is part of the batch root.
                    paths = rdg.regen_from_exp(self.cli_args.sierra_root,
                                               self.cli_args.batch_criteria,
                                               s,
                                               controller)
                    cmdopts.update(paths)
                    # For each scenario, we have to create the batch criteria for it, because they
                    # are all different.
                    criteria = bc.Factory(self.cli_args,
                                          cmdopts,
                                          rdg.parse_batch_root(s)[1])

                    self.__gen_csv(cmdopts=cmdopts,
                                   scenario=s,
                                   controller=controller,
                                   src_stem=graph['src_stem'],
                                   dest_stem=graph['dest_stem'])

                self.__gen_graph(scenario=s,
                                 batch_criteria=criteria,
                                 cmdopts=cmdopts,
                                 dest_stem=graph['dest_stem'],
                                 title=graph['title'],
                                 label=graph['label'])

    def __gen_graph(self,
                    scenario: str,
                    batch_criteria: bc.UnivarBatchCriteria,
                    cmdopts: tp.Dict[str, str],
                    dest_stem: str,
                    title: str,
                    label: str):
        """
        Generates a :meth:`BatchRangeGraph` comparing the specified controllers within the
        specified scenario after input files have been gathered from each controllers into
        ``cc-csvs/``.
        """
        csv_stem_opath = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)

        BatchRangedGraph(inputy_stem_fpath=csv_stem_opath,
                         output_fpath=os.path.join(self.cc_graph_root,
                                                   dest_stem) + '-' + scenario + ".png",
                         title=title,
                         xlabel=batch_criteria.graph_xlabel(cmdopts),
                         ylabel=label,
                         xvals=batch_criteria.graph_xticks(cmdopts),
                         legend=self.controllers,
                         polynomial_fit=-1).generate()

    def __gen_csv(self,
                  cmdopts: tp.Dict[str, str],
                  scenario: str,
                  controller: str,
                  src_stem: str,
                  dest_stem: str):
        """
        Help function for generating a set of .csv files for use in intra-scenario graph generation
        (1 per controller).
        """

        csv_ipath = os.path.join(cmdopts['sierra_root'],
                                 controller,
                                 scenario,
                                 'exp-outputs',
                                 self.main_config['sierra']['collate_csv_leaf'],
                                 src_stem + ".csv")
        stddev_ipath = os.path.join(cmdopts['sierra_root'],
                                    controller,
                                    scenario,
                                    'exp-outputs',
                                    self.main_config['sierra']['collate_csv_leaf'],
                                    src_stem + ".stddev")
        csv_opath_stem = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)

        # Some experiments might not generate the necessary performance measure .csvs for
        # graph generation, which is OK.
        if not os.path.exists(csv_ipath):
            return

        if os.path.exists(csv_opath_stem + '.csv'):
            cum_df = pd.read_csv(csv_opath_stem + '.csv', sep=';')
        else:
            cum_df = pd.DataFrame()

        cum_df = cum_df.append(pd.read_csv(csv_ipath, sep=';'))
        cum_df.to_csv(csv_opath_stem + '.csv', sep=';', index=False)

        if os.path.exists(csv_opath_stem + '.stddev'):
            cum_stddev_df = pd.read_csv(csv_opath_stem + '.stddev', sep=';')
        else:
            cum_stddev_df = pd.DataFrame()

        if os.path.exists(stddev_ipath):
            cum_stddev_df = cum_stddev_df.append(pd.read_csv(stddev_ipath, sep=';'))
            cum_stddev_df.to_csv(csv_opath_stem + '.stddev', sep=';', index=False)
