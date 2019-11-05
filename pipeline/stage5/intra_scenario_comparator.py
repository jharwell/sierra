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
"""
Classes for handling univariate and bivariate controller comparisons within a set of scenarios for
stage5 of the experimental pipeline.
"""

import os
import copy
import logging
import glob
import re
import typing as tp
import pandas as pd

from graphs.batch_ranged_graph import BatchRangedGraph
from graphs.stacked_surface_graph import StackedSurfaceGraph
from graphs.heatmap import Heatmap
import variables.batch_criteria as bc
import pipeline.root_dirpath_generator as rdg


class BivarIntraScenarioComparator:
    """
    Compares a set of controllers on different performance measures in all scenarios, one at a
    time. Graph generation is controlled via a config file parsed in
    :class:`~pipeline.stage5.PipelineStage5`. Bivariate batch criteria only.

    Attributes:
        controllers: List of controller names to compare.
        cc_csv_root: Absolute directory path to the location controller ``.csv`` files should be
                     output to.
        cc_graph_root: Absolute directory path to the location the generated graphs should be output
                       to.
        cmdopts: Dictionary of parsed cmdline parameters.
        cli_args: :class:`argparse` object containing the cmdline parameters. Needed for
                  :class:`~variables.batch_criteria.BatchCriteria` generation for each scenario
                  controllers are compared within, as batch criteria is dependent on
                  controller+scenario definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all cases.
    """

    def __init__(self,
                 controllers: tp.List[str],
                 cc_csv_root: str,
                 cc_graph_root: str,
                 cmdopts: tp.Dict[str, str],
                 cli_args: dict,
                 main_config: dict):
        self.controllers = controllers
        self.cc_csv_root = cc_csv_root
        self.cc_graph_root = cc_graph_root
        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config

    def __call__(self,
                 graphs: dict,
                 legend: tp.List[str],
                 comp_type: str):
        # Obtain the list of scenarios to use. We can just take the scenario list of the first
        # controllers, because we have already checked that all controllers executed the same set
        # scenarios.
        dirs = os.listdir(os.path.join(self.cmdopts['sierra_root'], self.controllers[0]))
        scenario_dirs = [rdg.parse_batch_root(d)[1] for d in dirs]

        cmdopts = copy.deepcopy(self.cmdopts)
        # For each controller comparison graph we are interested in, generate it using data from all
        # scenarios
        for graph in graphs:
            for s in scenario_dirs:
                self.__compare_in_scenario(cmdopts, graph, s, legend, comp_type)

    def __compare_in_scenario(self,
                              cmdopts: tp.Dict[str, str],
                              graph: dict,
                              scenario_dir: str,
                              legend: str,
                              comp_type: str):
        """
        Compares all controllers within the specified scenario, generating ``.csv`` files and graphs
        according to configuration.
        """
        for controller in self.controllers:
            dirs = [d for d in os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                                       controller)) if scenario_dir in d]

            if 0 == len(dirs):
                logging.warning("Controller %s was not run on scenario %s",
                                controller,
                                scenario_dir)
                continue
            scenario = rdg.parse_batch_root(dirs[0])[1]

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
                                  scenario)

            self.__gen_csv(cmdopts=cmdopts,
                           controller=controller,
                           batch_root=dirs[0],
                           src_stem=graph['src_stem'],
                           dest_stem=graph['dest_stem'])

            if '2D' in comp_type:
                self.__gen_heatmaps(scenario=scenario,
                                    batch_criteria=criteria,
                                    cmdopts=cmdopts,
                                    dest_stem=graph['dest_stem'],
                                    title=graph['title'],
                                    label=graph['label'],
                                    comp_type=comp_type)
            else:
                self.__gen_graph3D(scenario=scenario,
                                   batch_criteria=criteria,
                                   cmdopts=cmdopts,
                                   dest_stem=graph['dest_stem'],
                                   title=graph['title'],
                                   zlabel=graph['label'],
                                   legend=legend,
                                   comp_type=comp_type)

    def __gen_heatmaps(self,
                       scenario: str,
                       batch_criteria: bc.UnivarBatchCriteria,
                       cmdopts: tp.Dict[str, str],
                       dest_stem: str,
                       title: str,
                       label: str,
                       comp_type: str):
        """
        Generates a :class:`~graphs.heatmap.Heatmap` comparing the specified controllers within the
        specified scenario after input files have been gathered from each controller into
        :attribute:`self.cc_csv_root`.
        """

        csv_stem_root = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)
        paths = [f for f in glob.glob(
            csv_stem_root + '*.csv') if re.search('_[0-9]+', f)]

        ref_df = pd.read_csv(paths[0], sep=';')

        for i in range(1, len(paths)):
            df = pd.read_csv(paths[i], sep=';')
            if 'scale2D' == comp_type:
                plot_df = df / ref_df
            elif 'diff2D' == comp_type:
                plot_df = df - ref_df
            opath_stem = csv_stem_root + "_{0}{1}".format(0, i)
            plot_df.to_csv(opath_stem + ".csv", sep=';', index=False)

            Heatmap(input_fpath=opath_stem + ".csv",
                    output_fpath=os.path.join(self.cc_graph_root,
                                              dest_stem) + '-' + scenario + "_{0}{1}".format(0, i) + ".png",
                    title=title,
                    zlabel=self.__gen_zaxis_label(label, comp_type),
                    ylabel=batch_criteria.graph_xlabel(cmdopts),
                    xlabel=batch_criteria.graph_ylabel(cmdopts),
                    xtick_labels=batch_criteria.graph_yticklabels(cmdopts),
                    ytick_labels=batch_criteria.graph_xticklabels(cmdopts)).generate()

    def __gen_zaxis_label(self, label: str, comp_type: str):
        """
        If we are doing something other than raw controller comparisons, put that on the graph
        Z axis title.
        """
        if 'scale' in comp_type:
            return label + ' (Scaled)'
        elif 'diff'in comp_type == comp_type:
            return label + ' (Difference Comparison)'
        return label

    def __gen_graph3D(self,
                      scenario: str,
                      batch_criteria: bc.UnivarBatchCriteria,
                      cmdopts: tp.Dict[str, str],
                      dest_stem: str,
                      title: str,
                      zlabel: str,
                      legend: tp.List[str],
                      comp_type: str):
        """
        Generates a :class:`~graphs.stacked_surface_graph.StackedSurfaceGraph` comparing the
        specified controllers within thespecified scenario after input files have been gathered from
        each controllers into :attribute:`self.cc_csv_root`.
        """
        csv_stem_root = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)
        StackedSurfaceGraph(input_stem_pattern=csv_stem_root,
                            output_fpath=os.path.join(self.cc_graph_root,
                                                      dest_stem) + '-' + scenario + ".png",
                            title=title,
                            ylabel=batch_criteria.graph_xlabel(cmdopts),
                            xlabel=batch_criteria.graph_ylabel(cmdopts),
                            zlabel=self.__gen_zaxis_label(zlabel, comp_type),
                            xtick_labels=batch_criteria.graph_yticklabels(cmdopts),
                            ytick_labels=batch_criteria.graph_xticklabels(cmdopts),
                            legend=legend,
                            comp_type=comp_type).generate()

    def __gen_csv(self,
                  cmdopts: tp.Dict[str, str],
                  batch_root: str,
                  controller: str,
                  src_stem: str,
                  dest_stem: str):
        """
        Helper function for generating a set of .csv files for use in intra-scenario graph
        generation (1 per controller). Because each ``.csv`` file corresponding to performance
        measures are 2D arrays, we actually just copy and rename the performance measure ``.csv``
        files for each controllers into :attribute:`self.cc_csv_root`.

        :class:`~graphs.stacked_surface_graph.StackedSurfaceGraph` expects an ``_[0-9]+.csv``
        pattern for each 2D surfaces to graph in order to disambiguate which files belong to which
        controller without having the controller name in the filepath (contains dots), so we do that
        here. :class:`~graphs.heatmap.Heatmap` does not require that, but for the heatmap set we
        generate it IS helpful to have an easy way to differentiate primary vs. other controllers,
        so we do it unconditionally here to handle both cases.

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


class UnivarIntraScenarioComparator:
    """
    Compares a set of controllers on different performance measures in all scenarios using
    univariate batch criteria, one at a time. Graph generation is controlled via a config file
    parsed in :class:`~pipeline.stage5.PipelineStage5`. Univariate batch criteria only.

    Attributes:
        controllers: List of controller names to compare.
        cc_csv_root: Absolute directory path to the location controller ``.csv`` files should be
                     output to.
        cc_graph_root: Absolute directory path to the location the generated graphs should be output
                       to.
        cmdopts: Dictionary of parsed cmdline parameters.
        cli_args: :class:`argparse` object containing the cmdline parameters. Needed for
                  :class:`~variables.batch_criteria.BatchCriteria` generation for each scenario
                  controllers are compared within, as batch criteria is dependent on
                  controller+scenario definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all cases.

    """

    def __init__(self,
                 controllers: tp.List[str],
                 cc_csv_root: str,
                 cc_graph_root: str,
                 cmdopts: tp.Dict[str, str],
                 cli_args,
                 main_config):
        self.controllers = controllers
        self.cc_graph_root = cc_graph_root
        self.cc_csv_root = cc_csv_root

        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config

    def __call__(self,
                 graphs: dict,
                 legend: tp.List[str],
                 norm_comp: bool):
        # Obtain the list of scenarios to use. We can just take the scenario list of the first
        # controllers, because we have already checked that all controllers executed the same set
        # scenarios
        scenarios = os.listdir(os.path.join(self.cmdopts['sierra_root'], self.controllers[0]))

        # For each controller comparison graph we are interested in, generate it using data from all
        # scenarios
        cmdopts = copy.deepcopy(self.cmdopts)
        for graph in graphs:
            for s in scenarios:
                self.__compare_in_scenario(cmdopts, graph, s, legend)

    def __compare_in_scenario(self,
                              cmdopts: tp.Dict[str, str],
                              graph: dict,
                              scenario: str,
                              legend: str):
        for controller in self.controllers:
            # We need to generate the root directory paths for each batched experiment
            # (which # lives inside of the scenario dir), because they are all
            # different. We need generate these paths for EACH controller, because the
            # controller is part of the batch root.
            paths = rdg.regen_from_exp(self.cli_args.sierra_root,
                                       self.cli_args.batch_criteria,
                                       scenario,
                                       controller)
            cmdopts.update(paths)
            # For each scenario, we have to create the batch criteria for it, because they
            # are all different.
            criteria = bc.Factory(self.cli_args,
                                  cmdopts,
                                  rdg.parse_batch_root(scenario)[1])

            self.__gen_csv(cmdopts=cmdopts,
                           scenario=scenario,
                           controller=controller,
                           src_stem=graph['src_stem'],
                           dest_stem=graph['dest_stem'])

        self.__gen_graph(scenario=scenario,
                         batch_criteria=criteria,
                         cmdopts=cmdopts,
                         dest_stem=graph['dest_stem'],
                         title=graph['title'],
                         label=graph['label'],
                         legend=legend)

    def __gen_graph(self,
                    scenario: str,
                    batch_criteria: bc.UnivarBatchCriteria,
                    cmdopts: tp.Dict[str, str],
                    dest_stem: str,
                    title: str,
                    label: str,
                    legend: tp.List[str]):
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
                         legend=legend).generate()

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
