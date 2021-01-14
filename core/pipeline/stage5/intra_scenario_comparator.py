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

# Core packages
import os
import copy
import logging
import glob
import re
import typing as tp
import argparse

# 3rd party packages
import pandas as pd

# Project packages
from core.graphs.batch_ranged_graph import BatchRangedGraph
from core.graphs.stacked_surface_graph import StackedSurfaceGraph
from core.graphs.heatmap import Heatmap, DualHeatmap
from core.variables import batch_criteria as bc
import core.root_dirpath_generator as rdg
import core.utils
import core.config


class UnivarIntraScenarioComparator:
    """
    Compares a set of controllers on different performance measures in all scenarios using
    univariate batch criteria, one at a time. Graph generation is controlled via a config file
    parsed in :class:`~core.pipeline.stage5.pipeline_stage5.PipelineStage5`. Univariate batch
    criteria only.

    Attributes:
        controllers: List of controller names to compare.
        cc_csv_root: Absolute directory path to the location controller ``.csv`` files should be
                     output to.
        cc_graph_root: Absolute directory path to the location the generated graphs should be output
                       to.
        cmdopts: Dictionary of parsed cmdline parameters.
        cli_args: :class:`argparse` object containing the cmdline parameters. Needed for
                  :class:`~core.variables.batch_criteria.BatchCriteria` generation for each scenario
                  controllers are compared within, as batch criteria is dependent on
                  controller+scenario definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all cases.

    """

    def __init__(self,
                 controllers: tp.List[str],
                 cc_csv_root: str,
                 cc_graph_root: str,
                 cmdopts: dict,
                 cli_args,
                 main_config: dict) -> None:
        self.controllers = controllers
        self.cc_graph_root = cc_graph_root
        self.cc_csv_root = cc_csv_root

        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 graphs: dict,
                 legend: tp.List[str],
                 comp_type: str) -> None:
        # Obtain the list of scenarios to use. We can just take the scenario list of the first
        # controllers, because we have already checked that all controllers executed the same set
        # scenarios
        batch_leaves = os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                               self.cmdopts['project'],
                                               self.controllers[0]))

        # The FS gives us batch leaves which might not be in the same order as the list of specified
        # scenarios, so we:
        #
        # 1. Remove all batch leaves which do not have a counterpart in the scenario list we are
        #    comparing across.
        # 2. Do matching to get the indices of the batch leaves relative to the list, and then sort
        #    it.
        batch_leaves = [leaf for leaf in batch_leaves for s in self.scenarios if s in leaf]
        indices = [self.scenarios.index(s)
                   for leaf in batch_leaves for s in self.scenarios if s in leaf]
        batch_leaves = [leaf for s, leaf in sorted(zip(indices, batch_leaves),
                                                   key=lambda pair: pair[0])]

        # For each controller comparison graph we are interested in, generate it using data from all
        # scenarios
        cmdopts = copy.deepcopy(self.cmdopts)
        for graph in graphs:
            found = False
            for leaf in batch_leaves:
                if self.__leaf_select(leaf):
                    self.__compare_in_scenario(cmdopts=cmdopts,
                                               graph=graph,
                                               batch_leaf=leaf,
                                               legend=legend)
                    found = True
                    break
            if not found:
                self.logger.warning("Did not find scenario to compare in for criteria %s",
                                    self.cli_args.batch_criteria)

    def __leaf_select(self, candidate: str) -> bool:
        """
        Select which scenario to compare controllers within. You can only compare controllers within
        the scenario directly generated from the value of ``--batch-criteria``; other scenarios will
        (probably) cause file not found errors.

        """
        template_stem, scenario, _ = rdg.parse_batch_leaf(candidate)
        leaf = rdg.gen_batch_leaf(criteria=self.cli_args.batch_criteria,
                                  scenario=scenario,
                                  template_stem=template_stem)
        return leaf in candidate

    def __compare_in_scenario(self,
                              cmdopts: dict,
                              graph: dict,
                              batch_leaf: str,
                              legend: tp.List[str]) -> None:

        for controller in self.controllers:
            dirs = [d for d in os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                                       self.cmdopts['project'],
                                                       controller)) if batch_leaf in d]
            if len(dirs) == 0:
                self.logger.warning("Controller %s was not run on experiment %s",
                                    controller,
                                    batch_leaf)
                continue

            batch_leaf = dirs[0]
            _, scenario, _ = rdg.parse_batch_leaf(batch_leaf)

            # We need to generate the root directory paths for each batched experiment
            # (which # lives inside of the scenario dir), because they are all
            # different. We need generate these paths for EACH controller, because the
            # controller is part of the batch root path.
            paths = rdg.regen_from_exp(sierra_rpath=self.cli_args.sierra_root,
                                       project=self.cli_args.project,
                                       batch_leaf=batch_leaf,
                                       controller=controller)
            cmdopts.update(paths)

            # For each scenario, we have to create the batch criteria for it, because they
            # are all different.

            criteria = bc.factory(self.main_config, cmdopts, self.cli_args, scenario)

            self.__gen_csv(cmdopts=cmdopts,
                           batch_leaf=batch_leaf,
                           controller=controller,
                           src_stem=graph['src_stem'],
                           dest_stem=graph['dest_stem'])

        self.__gen_graph(batch_leaf=batch_leaf,
                         criteria=criteria,
                         cmdopts=cmdopts,
                         dest_stem=graph['dest_stem'],
                         title=graph['title'],
                         label=graph['label'],
                         legend=legend)

    def __gen_graph(self,
                    batch_leaf: str,
                    criteria: bc.IConcreteBatchCriteria,
                    cmdopts: dict,
                    dest_stem: str,
                    title: str,
                    label: str,
                    legend: tp.List[str]) -> None:
        """
        Generates a :class:`~core.graphs.batch_ranged_graph.BatchRangedGraph` comparing the
        specified controllers within the specified scenario after input files have been gathered
        from each controllers into ``cc-csvs/``.
        """
        csv_stem_opath = os.path.join(self.cc_csv_root, dest_stem + "-" + batch_leaf)
        xticks = criteria.graph_xticks(cmdopts)
        xtick_labels = criteria.graph_xticklabels(cmdopts)

        BatchRangedGraph(input_fpath=csv_stem_opath + '.csv',
                         output_fpath=os.path.join(self.cc_graph_root,
                                                   dest_stem) + '-' + batch_leaf + core.config.kImageExt,
                         title=title,
                         xlabel=criteria.graph_xlabel(cmdopts),
                         ylabel=label,
                         xtick_labels=xtick_labels[criteria.inter_exp_graphs_exclude_exp0():],
                         xticks=xticks[criteria.inter_exp_graphs_exclude_exp0():],
                         logyscale=cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text'],
                         legend=legend).generate()

    def __gen_csv(self,
                  cmdopts: dict,
                  batch_leaf: str,
                  controller: str,
                  src_stem: str,
                  dest_stem: str) -> None:
        """
        Help function for generating a set of .csv files for use in intra-scenario graph generatio
        (1 per controller).
        """

        csv_ipath = os.path.join(cmdopts['batch_output_root'],
                                 self.main_config['sierra']['collate_csv_leaf'],
                                 src_stem + ".csv")
        stddev_ipath = os.path.join(cmdopts['batch_output_root'],
                                    self.main_config['sierra']['collate_csv_leaf'],
                                    src_stem + ".stddev")
        csv_opath_stem = os.path.join(self.cc_csv_root,
                                      dest_stem + "-" + batch_leaf)

        # Some experiments might not generate the necessary performance measure .csvs for graph
        # generation, which is OK.
        if not core.utils.path_exists(csv_ipath):
            self.logger.warning("%s missing for controller %s", csv_ipath, controller)
            return

        if core.utils.path_exists(csv_opath_stem + '.csv'):
            cum_df = core.utils.pd_csv_read(csv_opath_stem + '.csv')
        else:
            cum_df = pd.DataFrame()

        t = core.utils.pd_csv_read(csv_ipath)
        cum_df = cum_df.append(t)

        core.utils.pd_csv_write(cum_df, csv_opath_stem + '.csv', index=False)

        if core.utils.path_exists(csv_opath_stem + '.stddev'):
            cum_stddev_df = core.utils.pd_csv_read(csv_opath_stem + '.stddev')
        else:
            cum_stddev_df = pd.DataFrame()

        if core.utils.path_exists(stddev_ipath):
            t = core.utils.pd_csv_read(stddev_ipath)
            cum_stddev_df = cum_stddev_df.append(t)
            core.utils.pd_csv_write(cum_stddev_df, csv_opath_stem + '.stddev', index=False)


class BivarIntraScenarioComparator:
    """
    Compares a set of controllers on different performance measures in all scenarios, one at a
    time. Graph generation is controlled via a config file parsed in
    :class:`~core.pipeline.stage5.pipeline_stage5.PipelineStage5`. Bivariate batch criteria only.

    Attributes:
        controllers: List of controller names to compare.
        cc_csv_root: Absolute directory path to the location controller ``.csv`` files should be
                     output to.
        cc_graph_root: Absolute directory path to the location the generated graphs should be output
                       to.
        cmdopts: Dictionary of parsed cmdline parameters.
        cli_args: :class:`argparse` object containing the cmdline parameters. Needed for
                  :class:`~core.variables.batch_criteria.BatchCriteria` generation for each scenario
                  controllers are compared within, as batch criteria is dependent on
                  controller+scenario definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all cases.
    """

    def __init__(self,
                 controllers: tp.List[str],
                 cc_csv_root: str,
                 cc_graph_root: str,
                 cmdopts: dict,
                 cli_args: argparse.Namespace,
                 main_config: dict) -> None:
        self.controllers = controllers
        self.cc_csv_root = cc_csv_root
        self.cc_graph_root = cc_graph_root
        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 graphs: dict,
                 legend: tp.List[str],
                 comp_type: str) -> None:

        # Obtain the list of scenarios to use. We can just take the scenario list of the first
        # controllers, because we have already checked that all controllers executed the same set
        # scenarios.
        batch_leaves = os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                               self.cmdopts['project'],
                                               self.controllers[0]))

        cmdopts = copy.deepcopy(self.cmdopts)

        # For each controller comparison graph we are interested in, generate it using data from all
        # scenarios
        cmdopts = copy.deepcopy(self.cmdopts)
        for graph in graphs:
            found = False
            for leaf in batch_leaves:
                if self.__leaf_select(leaf):
                    self.__compare_in_scenario(cmdopts=cmdopts,
                                               graph=graph,
                                               batch_leaf=leaf,
                                               legend=legend,
                                               comp_type=comp_type)
                    found = True
                    break
            if not found:
                self.logger.warning("Did not find scenario to compare in for criteria %s",
                                    self.cli_args.batch_criteria)

    def __leaf_select(self, candidate: str) -> bool:
        """
        Select which scenario to compare controllers within. You can only compare controllers within
        the scenario directly generated from the value of ``--batch-criteria``; other scenarios will
        (probably) cause file not found errors.

        """
        template_stem, scenario, _ = rdg.parse_batch_leaf(candidate)
        leaf = rdg.gen_batch_leaf(criteria=self.cli_args.batch_criteria,
                                  scenario=scenario,
                                  template_stem=template_stem)
        return leaf in candidate

    def __compare_in_scenario(self,
                              cmdopts: dict,
                              graph: dict,
                              batch_leaf: str,
                              legend: tp.List[str],
                              comp_type: str) -> None:
        """
        Compares all controllers within the specified scenario, generating ``.csv`` files and graphs
        according to configuration.
        """
        for controller in self.controllers:
            dirs = [d for d in os.listdir(os.path.join(self.cmdopts['sierra_root'],
                                                       self.cmdopts['project'],
                                                       controller)) if batch_leaf in d]
            if len(dirs) == 0:
                self.logger.warning("Controller %s was not run on scenario %s",
                                    controller,
                                    batch_leaf)
                continue

            batch_leaf = dirs[0]
            _, scenario, _ = rdg.parse_batch_leaf(batch_leaf)

            # We need to generate the root directory paths for each batched experiment
            # (which # lives inside of the scenario dir), because they are all
            # different. We need generate these paths for EACH controller, because the
            # controller is part of the batch root path.
            paths = rdg.regen_from_exp(sierra_rpath=self.cli_args.sierra_root,
                                       project=self.cli_args.project,
                                       batch_leaf=batch_leaf,
                                       controller=controller)

            cmdopts.update(paths)

            # For each scenario, we have to create the batch criteria for it, because they
            # are all different.
            criteria = bc.factory(self.main_config, cmdopts, self.cli_args, scenario)

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
                                legend=legend,
                                comp_type=comp_type)

        elif '3D' in comp_type:
            self.__gen_graph3D(scenario=scenario,
                               batch_criteria=criteria,
                               cmdopts=cmdopts,
                               dest_stem=graph['dest_stem'],
                               title=graph['title'],
                               zlabel=graph['label'],
                               legend=legend,
                               comp_type=comp_type)
        else:
            raise ValueError('Bad comparison type requested: {0}'.format(comp_type))

    def __gen_heatmaps(self,
                       scenario: str,
                       batch_criteria: bc.BivarBatchCriteria,
                       cmdopts: dict,
                       dest_stem: str,
                       title: str,
                       label: str,
                       legend: tp.List[str],
                       comp_type: str) -> None:
        if comp_type in ['scale2D', 'diff2D']:
            self.__gen_paired_heatmaps(scenario,
                                       batch_criteria,
                                       cmdopts,
                                       dest_stem,
                                       title,
                                       label,
                                       comp_type)
        elif comp_type in ['raw2D']:
            self.__gen_dual_heatmaps(scenario,
                                     batch_criteria,
                                     cmdopts,
                                     dest_stem,
                                     title,
                                     label,
                                     legend,
                                     comp_type)

    def __gen_paired_heatmaps(self,
                              scenario: str,
                              batch_criteria: bc.BivarBatchCriteria,
                              cmdopts: dict,
                              dest_stem: str,
                              title: str,
                              label: str,
                              comp_type: str) -> None:
        """
        Generates a set of :class:`~core.graphs.heatmap.Heatmap` graphs a controller of primary
        interest against all other controllers (one graph per pairing), after input files have been
        gathered from each controller into :attribute:`self.cc_csv_root`. Only valid if the
        comparison type is ``scale2D`` or ``diff2D``.
        """

        csv_stem_root = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)
        paths = [f for f in glob.glob(
            csv_stem_root + '*.csv') if re.search('_[0-9]+', f)]

        ref_df = core.utils.pd_csv_read(paths[0])

        for i in range(1, len(paths)):
            df = core.utils.pd_csv_read(paths[i])

            if comp_type == 'scale2D':
                plot_df = df / ref_df
            elif comp_type == 'diff2D':
                plot_df = df - ref_df
            opath_stem = csv_stem_root + "_{0}{1}".format(0, i)
            core.utils.pd_csv_write(plot_df, opath_stem + ".csv", index=False)

            opath = os.path.join(self.cc_graph_root,
                                 dest_stem) + '-' + scenario + "_{0}{1}".format(0, i) + core.config.kImageExt
            Heatmap(input_fpath=opath_stem + ".csv",
                    output_fpath=opath,
                    title=title,
                    transpose=self.cmdopts['transpose_graphs'],
                    zlabel=self.__gen_zaxis_label(label, comp_type),
                    xlabel=batch_criteria.graph_xlabel(cmdopts),
                    ylabel=batch_criteria.graph_ylabel(cmdopts),
                    xtick_labels=batch_criteria.graph_xticklabels(cmdopts),
                    ytick_labels=batch_criteria.graph_yticklabels(cmdopts)).generate()

    def __gen_dual_heatmaps(self,
                            scenario: str,
                            batch_criteria: bc.BivarBatchCriteria,
                            cmdopts: dict,
                            dest_stem: str,
                            title: str,
                            label: str,
                            legend: tp.List[str],
                            comp_type: str) -> None:
        """
        Generates a set of :class:`~core.graphs.heatmap.DualHeatmap` graphs containing all pairs of
        (primary controller, other), one per graph, within the specified scenario after input files
        have been gathered from each controller into :attribute:`self.cc_csv_root`. Only valid if
        the comparison type is ``raw``.
        """

        csv_stem_root = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)

        paths = [f for f in glob.glob(
            csv_stem_root + '*.csv') if re.search('_[0-9]+', f)]

        for _ in range(0, len(paths)):
            opath = os.path.join(self.cc_graph_root,
                                 dest_stem) + '-' + scenario + core.config.kImageExt
            DualHeatmap(input_stem_pattern=csv_stem_root,
                        output_fpath=opath,
                        title=title,
                        zlabel=self.__gen_zaxis_label(label, comp_type),
                        xlabel=batch_criteria.graph_xlabel(cmdopts),
                        ylabel=batch_criteria.graph_ylabel(cmdopts),
                        legend=legend,
                        xtick_labels=batch_criteria.graph_xticklabels(cmdopts),
                        ytick_labels=batch_criteria.graph_yticklabels(cmdopts)).generate()

    def __gen_graph3D(self,
                      scenario: str,
                      batch_criteria: bc.BivarBatchCriteria,
                      cmdopts: dict,
                      dest_stem: str,
                      title: str,
                      zlabel: str,
                      legend: tp.List[str],
                      comp_type: str) -> None:
        """
        Generates a :class:`~core.graphs.stacked_surface_graph.StackedSurfaceGraph` comparing the
        specified controllers within thespecified scenario after input files have been gathered from
        each controllers into :attribute:`self.cc_csv_root`.
        """
        csv_stem_root = os.path.join(self.cc_csv_root, dest_stem + "-" + scenario)
        opath = os.path.join(self.cc_graph_root,
                             dest_stem) + '-' + scenario + core.config.kImageExt
        StackedSurfaceGraph(input_stem_pattern=csv_stem_root,
                            output_fpath=opath,
                            title=title,
                            ylabel=batch_criteria.graph_xlabel(cmdopts),
                            xlabel=batch_criteria.graph_ylabel(cmdopts),
                            zlabel=self.__gen_zaxis_label(zlabel, comp_type),
                            xtick_labels=batch_criteria.graph_yticklabels(cmdopts),
                            ytick_labels=batch_criteria.graph_xticklabels(cmdopts),
                            legend=legend,
                            comp_type=comp_type).generate()

    def __gen_zaxis_label(self, label: str, comp_type: str) -> str:
        """
        If we are doing something other than raw controller comparisons, put that on the graph
        Z axis title.
        """
        if 'scale' in comp_type:
            return label + ' (Scaled)'
        elif 'diff' in comp_type == comp_type:
            return label + ' (Difference Comparison)'
        return label

    def __gen_csv(self,
                  cmdopts: dict,
                  batch_root: str,
                  controller: str,
                  src_stem: str,
                  dest_stem: str) -> None:
        """
        Helper function for generating a set of .csv files for use in intra-scenario graph
        generation (1 per controller). Because each ``.csv`` file corresponding to performance
        measures are 2D arrays, we actually just copy and rename the performance measure ``.csv``
        files for each controllers into :attribute:`self.cc_csv_root`.

        :class:`~core.graphs.stacked_surface_graph.StackedSurfaceGraph` expects an ``_[0-9]+.csv``
        pattern for each 2D surfaces to graph in order to disambiguate which files belong to which
        controller without having the controller name in the filepath (contains dots), so we do that
        here. :class:`~core.graphs.heatmap.Heatmap` does not require that, but for the heatmap set
        we generate it IS helpful to have an easy way to differentiate primary vs. other
        controllers, so we do it unconditionally here to handle both cases.

        """
        csv_ipath = os.path.join(cmdopts['batch_output_root'],
                                 self.main_config['sierra']['collate_csv_leaf'],
                                 src_stem + ".csv")

        # Some experiments might not generate the necessary performance measure .csvs for
        # graph generation, which is OK.
        if not core.utils.path_exists(csv_ipath):
            self.logger.warning("%s missing for controller %s", csv_ipath, controller)
            return

        df = core.utils.pd_csv_read(csv_ipath)

        _, batch_leaf, _ = rdg.parse_batch_leaf(batch_root)
        leaf = dest_stem + "-" + batch_leaf + '_' + str(self.controllers.index(controller))

        csv_opath_stem = os.path.join(self.cc_csv_root, leaf)
        core.utils.pd_csv_write(df, csv_opath_stem + '.csv', index=False)


__api__ = ['UnivarIntraScenarioComparator', 'BivarIntraScenarioComparator']
