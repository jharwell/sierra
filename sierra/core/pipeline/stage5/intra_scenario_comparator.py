# Copyright 2019 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT

"""Classes for comparing deliverables within the same scenario.

Univariate and bivariate batch criteria.

"""

# Core packages
import os
import copy
import glob
import re
import typing as tp
import argparse
import logging
import pathlib

# 3rd party packages

# Project packages
from sierra.core.graphs.summary_line_graph import SummaryLineGraph
from sierra.core.graphs.stacked_surface_graph import StackedSurfaceGraph
from sierra.core.graphs.heatmap import Heatmap, DualHeatmap
from sierra.core.variables import batch_criteria as bc
from sierra.core import types, utils, config, storage, batchroot
from sierra.core.pipeline.stage5 import namecalc, preprocess, outputroot


class UnivarIntraScenarioComparator:
    """Compares a set of controllers within each of a set of scenarios.

    Graph generation
    is controlled via a config file parsed in
    :class:`~sierra.core.pipeline.stage5.pipeline_stage5.PipelineStage5`.

    Univariate batch criteria only.

    Attributes:

        controllers: List of controller names to compare.

        stage5_roots: Set of directory paths for stage 5 file generation.

        cmdopts: Dictionary of parsed cmdline parameters.

        cli_args: :class:`argparse` object containing the cmdline
                  parameters. Needed for
                  :class:`~sierra.core.variables.batch_criteria.BatchCriteria`
                  generation for each scenario controllers are compared within,
                  as batch criteria is dependent on controller+scenario
                  definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all
                  cases.

    """

    def __init__(self,
                 controllers: tp.List[str],
                 batch_roots: batchroot.PathSet,
                 stage5_roots: outputroot.PathSet,
                 cmdopts: types.Cmdopts,
                 cli_args,
                 main_config: types.YAMLDict) -> None:
        self.controllers = controllers
        self.batch_roots = batch_roots
        self.stage5_roots = stage5_roots

        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config
        self.project_root = pathlib.Path(self.cmdopts['sierra_root'],
                                         self.cmdopts['project'])
        self.logger = logging.getLogger(__name__)

    def __call__(self,
                 graphs: tp.List[types.YAMLDict],
                 legend: tp.List[str],
                 comp_type: str) -> None:
        # Obtain the list of scenarios to use. We can just take the scenario
        # list of the first controllers, because we have already checked that
        # all controllers executed the same set scenarios.
        batch_leaves = os.listdir(self.project_root / self.controllers[0])

        # For each controller comparison graph we are interested in, generate it
        # using data from all scenarios
        cmdopts = copy.deepcopy(self.cmdopts)
        for graph in graphs:
            found = False
            for l in batch_leaves:
                if self._leaf_select(l):
                    self.logger.debug("Generating graph %s from scenario '%s'",
                                      graph,
                                      l)
                    leaf = batchroot.ExpRootLeaf.from_name(l)
                    self._compare_in_scenario(cmdopts=cmdopts,
                                              graph=graph,
                                              batch_leaf=leaf,
                                              legend=legend)
                    found = True
                    break
            if not found:
                self.logger.warning("Did not find scenario to compare in for criteria %s",
                                    self.cli_args.batch_criteria)

    def _leaf_select(self, candidate: str) -> bool:
        """Determine if a controller can be included in the comparison for a scenario.

        You can only compare controllers within the scenario directly generated
        from the value of ``--batch-criteria``; other scenarios will (probably)
        cause file not found errors.

        """
        leaf = batchroot.ExpRootLeaf.from_name(candidate).to_path()
        return leaf in candidate

    def _compare_in_scenario(self,
                             cmdopts: types.Cmdopts,
                             graph: types.YAMLDict,
                             batch_leaf: batchroot.ExpRootLeaf,
                             legend: tp.List[str]) -> None:

        for controller in self.controllers:
            dirs = [d for d in os.listdir(
                self.project_root / controller) if batch_leaf in d]
            if len(dirs) == 0:
                self.logger.warning("Controller %s was not run on experiment %s",
                                    controller,
                                    batch_leaf)
                continue

            batch_leaf = batchroot.ExpRootLeaf.from_name(dirs[0])

            # We need to generate the root directory paths for each batch
            # experiment (which # lives inside of the scenario dir), because
            # they are all different. We need generate these paths for EACH
            # controller, because the controller is part of the batch root path.
            pathset = batchroot.from_exp(sierra_root=self.cli_args.sierra_root,
                                         project=self.cli_args.project,
                                         batch_leaf=batch_leaf,
                                         controller=controller)

            # For each scenario, we have to create the batch criteria for it,
            # because they are all different.
            criteria = bc.factory(self.main_config,
                                  cmdopts,
                                  pathset.input_root,
                                  self.cli_args,
                                  batch_leaf.scenario)

            self._gen_csv(batch_leaf=batch_leaf,
                          criteria=criteria,
                          pathset=pathset,
                          controller=controller,
                          src_stem=graph['src_stem'],
                          dest_stem=graph['dest_stem'],
                          inc_exps=graph.get('include_exp', None))

            self._gen_graph(batch_leaf=batch_leaf,
                            criteria=criteria,
                            cmdopts=cmdopts,
                            batch_output_root=pathset.output_root,
                            dest_stem=graph['dest_stem'],
                            title=graph.get('title', ''),
                            label=graph.get('label', ''),
                            inc_exps=graph.get('include_exp', None),
                            legend=legend)

    def _gen_csv(self,
                 batch_leaf: batchroot.ExpRootLeaf,
                 criteria: bc.IConcreteBatchCriteria,
                 pathset: batchroot.PathSet,
                 controller: str,
                 src_stem: str,
                 dest_stem: str,
                 inc_exps: tp.Optional[str]) -> None:
        """Generate a set of CSV files for use in intra-scenario graph generation.

        1 CSV per controller.

        """
        self.logger.debug("Gathering data for '%s' from %s -> %s",
                          controller, src_stem, dest_stem)
        ipath = pathset.stat_collate_root / \
            (src_stem + config.kStats['mean'].exts['mean'])

        # Some experiments might not generate the necessary performance measure
        # .csvs for graph generation, which is OK.
        if not utils.path_exists(ipath):
            self.logger.warning("%s missing for controller %s",
                                ipath,
                                controller)
            return

        preparer = preprocess.IntraExpPreparer(ipath_stem=pathset.stat_collate_root,
                                               ipath_leaf=src_stem,
                                               opath_stem=self.stage5_roots.csv_root,
                                               n_exp=criteria.n_exp())
        opath_leaf = namecalc.for_output(batch_leaf.name, dest_stem, None)
        preparer.across_rows(opath_leaf=opath_leaf, index=0, inc_exps=inc_exps)

    def _gen_graph(self,
                   batch_leaf: batchroot.ExpRootLeaf,
                   criteria: bc.IConcreteBatchCriteria,
                   cmdopts: types.Cmdopts,
                   batch_output_root: pathlib.Path,
                   dest_stem: str,
                   title: str,
                   label: str,
                   inc_exps: tp.Optional[str],
                   legend: tp.List[str]) -> None:
        """Generate a graph comparing the specified controllers within a scenario.
        """
        opath_leaf = namecalc.for_output(batch_leaf,
                                         dest_stem,
                                         None)

        xticks = criteria.graph_xticks(cmdopts, batch_output_root)
        xtick_labels = criteria.graph_xticklabels(cmdopts, batch_output_root)

        if inc_exps is not None:
            xtick_labels = utils.exp_include_filter(
                inc_exps, xtick_labels, criteria.n_exp())
            xticks = utils.exp_include_filter(
                inc_exps, xticks, criteria.n_exp())

        opath = self.stage5_roots.graph_root / (opath_leaf + config.kImageExt)

        SummaryLineGraph(stats_root=self.stage5_roots.csv_root,
                         input_stem=opath_leaf,
                         output_fpath=opath,
                         stats=cmdopts['dist_stats'],
                         title=title,
                         xlabel=criteria.graph_xlabel(cmdopts),
                         ylabel=label,
                         xtick_labels=xtick_labels,
                         xticks=xticks,
                         logyscale=cmdopts['plot_log_yscale'],
                         large_text=self.cmdopts['plot_large_text'],
                         legend=legend).generate()


class BivarIntraScenarioComparator:
    """Compares a set of controllers within each of a set of scenarios.

    Graph generation is controlled via a config file
    parsed in
    :class:`~sierra.core.pipeline.stage5.pipeline_stage5.PipelineStage5`.

    Bivariate batch criteria only.

    Attributes:

        controllers: List of controller names to compare.

        cmdopts: Dictionary of parsed cmdline parameters.

        cli_args: :class:`argparse` object containing the cmdline
                  parameters. Needed for
                  :class:`~sierra.core.variables.batch_criteria.BatchCriteria`
                  generation for each scenario controllers are compared within,
                  as batch criteria is dependent on controller+scenario
                  definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all
                  cases.
    """

    def __init__(self,
                 controllers: tp.List[str],
                 stage5_roots: outputroot.PathSet,
                 cmdopts: types.Cmdopts,
                 cli_args: argparse.Namespace,
                 main_config: types.YAMLDict) -> None:
        self.controllers = controllers
        self.stage5_roots = stage5_roots
        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config
        self.logger = logging.getLogger(__name__)

        self.logger.debug("csv_root=%s", str(self.stage5_roots.csv_root))
        self.logger.debug("graph_root=%s", str(self.stage5_roots.graph_root))

        self.project_root = pathlib.Path(self.cmdopts['sierra_root'],
                                         self.cmdopts['project'])

    def __call__(self,
                 graphs: tp.List[types.YAMLDict],
                 legend: tp.List[str],
                 comp_type: str) -> None:

        # Obtain the list of scenarios to use. We can just take the scenario
        # list of the first controllers, because we have already checked that
        # all controllers executed the same set scenarios.
        batch_leaves = os.listdir(self.project_root / self.controllers[0])

        cmdopts = copy.deepcopy(self.cmdopts)
        for graph in graphs:
            found = False
            for l in batch_leaves:
                if self._leaf_select(l):
                    leaf = batchroot.ExpRootLeaf.from_name(l)
                    self.logger.debug("Generating graph %s from scenario '%s'",
                                      graph,
                                      leaf)
                    self._compare_in_scenario(cmdopts=cmdopts,
                                              graph=graph,
                                              batch_leaf=leaf,
                                              legend=legend,
                                              comp_type=comp_type)
                    found = True
                    break
            if not found:
                self.logger.warning("Did not find scenario to compare in for criteria '%s'",
                                    self.cli_args.batch_criteria)

    def _leaf_select(self, candidate: str) -> bool:
        """Determine if a controller can be included in the comparison for a scenario.

        You can only compare controllers within the scenario directly generated
        from the value of ``--batch-criteria``; other scenarios will (probably)
        cause file not found errors.

        """
        leaf = batchroot.ExpRootLeaf.from_name(candidate).to_path()
        return leaf in candidate

    def _compare_in_scenario(self,
                             cmdopts: types.Cmdopts,
                             graph: types.YAMLDict,
                             batch_leaf: batchroot.ExpRootLeaf,
                             legend: tp.List[str],
                             comp_type: str) -> None:
        """Compare all controllers within the specified scenario.

        Generates CSV files and graphs according to configuration.
        """
        for controller in self.controllers:
            dirs = [d for d in os.listdir(
                self.project_root / controller) if batch_leaf in d]

            if len(dirs) == 0:
                self.logger.warning("Controller '%s' was not run on scenario '%s'",
                                    controller,
                                    batch_leaf)
                continue

            batch_leaf = batchroot.ExpRootLeaf.from_name(dirs[0])

            # We need to generate the root directory paths for each batch
            # experiment (which # lives inside of the scenario dir), because
            # they are all different. We need generate these paths for EACH
            # controller, because the controller is part of the batch root path.
            pathset = batchroot.from_exp(sierra_root=self.cli_args.sierra_root,
                                         project=self.cli_args.project,
                                         batch_leaf=batch_leaf,
                                         controller=controller)

            # For each scenario, we have to create the batch criteria for it,
            # because they are all different.
            criteria = bc.factory(self.main_config,
                                  cmdopts,
                                  pathset.input_root,
                                  self.cli_args,
                                  batch_leaf.scenario)
            if comp_type == 'LNraw':
                self._gen_csvs_for_1D(cmdopts=cmdopts,
                                      criteria=criteria,
                                      pathset=pathset,
                                      controller=controller,
                                      batch_leaf=batch_leaf,
                                      src_stem=graph['src_stem'],
                                      dest_stem=graph['dest_stem'],
                                      primary_axis=graph.get('primary_axis', 0),
                                      inc_exps=graph.get('include_exp', None))

            elif 'HM' in comp_type or 'SU' in comp_type:
                self._gen_csvs_for_2D_or_3D(controller=controller,
                                            batch_leaf=batch_leaf,
                                            pathset=pathset,
                                            src_stem=graph['src_stem'],
                                            dest_stem=graph['dest_stem'])

        if comp_type == 'LNraw':
            self._gen_graphs1D(batch_leaf=batch_leaf,
                               criteria=criteria,
                               cmdopts=cmdopts,
                               pathset=pathset,
                               dest_stem=graph['dest_stem'],
                               title=graph.get('title', ''),
                               label=graph.get('label', ''),
                               primary_axis=graph.get('primary_axis', 0),
                               inc_exps=graph.get('include_exp', None),
                               legend=legend)
        elif 'HM' in comp_type:
            self._gen_graphs2D(batch_leaf=batch_leaf,
                               criteria=criteria,
                               cmdopts=cmdopts,
                               dest_stem=graph['dest_stem'],
                               title=graph.get('title', ''),
                               label=graph.get('label', ''),
                               legend=legend,
                               comp_type=comp_type)

        elif 'SU' in comp_type:
            self._gen_graph3D(batch_leaf=batch_leaf,
                              criteria=criteria,
                              cmdopts=cmdopts,
                              dest_stem=graph['dest_stem'],
                              title=graph.get('title', ''),
                              zlabel=graph.get('label', ''),
                              legend=legend,
                              comp_type=comp_type)

    def _gen_csvs_for_2D_or_3D(self,
                               pathset: batchroot.PathSet,
                               batch_leaf: batchroot.ExpRootLeaf,
                               controller: str,
                               src_stem: str,
                               dest_stem: str) -> None:
        """Generate a set of CSV files for use in intra-scenario graph generation.

        1 CSV per controller, for 2D/3D comparison types only. Because each CSV
        file corresponding to performance measures are 2D arrays, we actually
        just copy and rename the performance measure CSV files for each
        controllers into :attr:`stage5_roots.csv_root`.

        :class:`~sierra.core.graphs.stacked_surface_graph.StackedSurfaceGraph`
        expects an ``_[0-9]+.csv`` pattern for each 2D surfaces to graph in
        order to disambiguate which files belong to which controller without
        having the controller name in the filepath (contains dots), so we do
        that here. :class:`~sierra.core.graphs.heatmap.Heatmap` does not require
        that, but for the heatmap set we generate it IS helpful to have an easy
        way to differentiate primary vs. other controllers, so we do it
        unconditionally here to handle both cases.

        """
        self.logger.debug("Gathering data for '%s' from %s -> %s",
                          controller, src_stem, dest_stem)

        csv_ipath = pathset.stat_collate_root / \
            (src_stem + config.kStats['mean'].exts['mean'])

        # Some experiments might not generate the necessary performance measure
        # .csvs for graph generation, which is OK.
        if not utils.path_exists(csv_ipath):
            self.logger.warning("%s missing for controller '%s'",
                                csv_ipath,
                                controller)
            return

        df = storage.DataFrameReader('storage.csv')(csv_ipath)

        opath_leaf = namecalc.for_output(batch_leaf,
                                         dest_stem,
                                         [self.controllers.index(controller)])

        opath_stem = self.stage5_roots.csv_root / opath_leaf
        opath = opath_stem.with_name(
            opath_stem.name + config.kStats['mean'].exts['mean'])
        writer = storage.DataFrameWriter('storage.csv')
        writer(df, opath, index=False)

    def _gen_csvs_for_1D(self,
                         cmdopts: types.Cmdopts,
                         pathset: batchroot.PathSet,
                         criteria: bc.BivarBatchCriteria,
                         batch_leaf: batchroot.ExpRootLeaf,
                         controller: str,
                         src_stem: str,
                         dest_stem: str,
                         primary_axis: int,
                         inc_exps: tp.Optional[str]) -> None:
        """Generate a set of CSV files for use in intra-scenario graph generation.

        Because we are targeting linegraphs, we draw the the i-th row/col (as
        configured) from the performance results of each controller .csv, and
        concatenate them into a new .csv file which can be given to
        :class:`~sierra.core.graphs.summary_line_graph.SummaryLineGraph`.

        """
        self.logger.debug("Gathering data for '%s' from %s -> %s",
                          controller, src_stem, dest_stem)

        csv_ipath = pathset.stat_collate_root / \
            src_stem + config.kStats['mean'].exts['mean']

        # Some experiments might not generate the necessary performance measure
        # .csvs for graph generation, which is OK.
        if not utils.path_exists(csv_ipath):
            self.logger.warning("%s missing for controller '%s'",
                                csv_ipath,
                                controller)
            return

        if cmdopts['dist_stats'] != 'none':
            self.logger.warning(("--dist-stats is not supported with "
                                 "1D CSVs sliced from 2D CSV for linegraph "
                                 "generation: no stats will be included"))

        if primary_axis == 0:
            preparer = preprocess.IntraExpPreparer(ipath_stem=pathset.stat_collate_root,
                                                   ipath_leaf=src_stem,
                                                   opath_stem=self.stage5_roots.csv_root,
                                                   n_exp=criteria.criteria2.n_exp())

            reader = storage.DataFrameReader('storage.csv')
            ipath = pathset.stat_collate_root / \
                (src_stem + config.kStats['mean'].exts['mean'])
            n_rows = len(reader(ipath).index)

            for i in range(0, n_rows):
                opath_leaf = namecalc.for_output(batch_leaf,
                                                 dest_stem,
                                                 [i])
                preparer.across_rows(opath_leaf=opath_leaf,
                                     index=i,
                                     inc_exps=inc_exps)
        else:
            preparer = preprocess.IntraExpPreparer(ipath_stem=pathset.stat_collate_root,
                                                   ipath_leaf=src_stem,
                                                   opath_stem=self.stage5_roots.csv_root,
                                                   n_exp=criteria.criteria1.n_exp())

            exp_dirs = criteria.gen_exp_names()
            xlabels, ylabels = utils.bivar_exp_labels_calc(exp_dirs)
            xlabels = utils.exp_include_filter(
                inc_exps, xlabels, criteria.criteria1.n_exp())

            for col in ylabels:
                col_index = ylabels.index(col)
                opath_leaf = namecalc.for_output(batch_leaf,
                                                 dest_stem,
                                                 [col_index])
                preparer.across_cols(opath_leaf=opath_leaf,
                                     col_index=col_index,
                                     all_cols=xlabels,
                                     inc_exps=inc_exps)

    def _gen_graphs1D(self,
                      batch_leaf: batchroot.ExpRootLeaf,
                      criteria: bc.BivarBatchCriteria,
                      pathset: batchroot.PathSet,
                      cmdopts: types.Cmdopts,
                      dest_stem: str,
                      title: str,
                      label: str,
                      primary_axis: int,
                      inc_exps: tp.Optional[str],
                      legend: tp.List[str]) -> None:
        oleaf = namecalc.for_output(batch_leaf,
                                    dest_stem,
                                    None)
        csv_stem_root = self.stage5_roots.csv_root / oleaf
        pattern = str(csv_stem_root) + '*' + config.kStats['mean'].exts['mean']
        paths = [f for f in glob.glob(pattern) if re.search('_[0-9]+', f)]

        for i in range(0, len(paths)):
            opath_leaf = namecalc.for_output(batch_leaf,
                                             dest_stem,
                                             [i])
            img_opath = self.stage5_roots.graph_root / \
                (opath_leaf + config.kImageExt)

            if primary_axis == 0:
                n_exp = criteria.criteria1.n_exp()
                xticks = utils.exp_include_filter(inc_exps,
                                                  criteria.graph_yticks(
                                                      cmdopts),
                                                  n_exp)
                xtick_labels = utils.exp_include_filter(inc_exps,
                                                        criteria.graph_yticklabels(
                                                            cmdopts),
                                                        n_exp)
                xlabel = criteria.graph_ylabel(cmdopts)
            else:
                n_exp = criteria.criteria2.n_exp()
                xticks = utils.exp_include_filter(inc_exps,
                                                  criteria.graph_xticks(
                                                      cmdopts),
                                                  n_exp)
                xtick_labels = utils.exp_include_filter(inc_exps,
                                                        criteria.graph_xticklabels(
                                                            cmdopts),
                                                        n_exp)
                xlabel = criteria.graph_xlabel(cmdopts)

            # TODO: Fix no statistics support for these graphs
            SummaryLineGraph(stats_root=self.stage5_roots.csv_root,
                             input_stem=opath_leaf,
                             stats='none',
                             output_fpath=img_opath,
                             model_root=pathset.model_root,
                             title=title,
                             xlabel=xlabel,
                             ylabel=label,
                             xticks=xticks,
                             xtick_labels=xtick_labels,
                             legend=legend,
                             logyscale=cmdopts['plot_log_yscale'],
                             large_text=cmdopts['plot_large_text']).generate()

    def _gen_graphs2D(self,
                      batch_leaf: batchroot.ExpRootLeaf,
                      criteria: bc.BivarBatchCriteria,
                      cmdopts: types.Cmdopts,
                      dest_stem: str,
                      title: str,
                      label: str,
                      legend: tp.List[str],
                      comp_type: str) -> None:
        if comp_type in ['HMscale', 'HMdiff']:
            self._gen_paired_heatmaps(batch_leaf,
                                      criteria,
                                      cmdopts,
                                      dest_stem,
                                      title,
                                      label,
                                      comp_type)
        elif comp_type == 'HMraw':
            self._gen_dual_heatmaps(batch_leaf,
                                    criteria,
                                    cmdopts,
                                    dest_stem,
                                    title,
                                    label,
                                    legend,
                                    comp_type)

    def _gen_paired_heatmaps(self,
                             batch_leaf: batchroot.ExpRootLeaf,
                             criteria: bc.BivarBatchCriteria,
                             cmdopts: types.Cmdopts,
                             dest_stem: str,
                             title: str,
                             label: str,
                             comp_type: str) -> None:
        """Generate a set of :class:`~sierra.core.graphs.heatmap.Heatmap` graphs.

        Uses a configured controller of primary interest against all other
        controllers (one graph per pairing), after input files have been
        gathered from each controller into :attr:`stage5_roots.csv_root`. 

        """
        opath_leaf = namecalc.for_output(batch_leaf,
                                         dest_stem,
                                         None)
        opath = self.stage5_roots.graph_root / (opath_leaf + config.kImageExt)
        pattern = self.stage5_roots.csv_root / (opath_leaf + '*' +
                                                config.kStats['mean'].exts['mean'])

        paths = [pathlib.Path(f) for f in glob.glob(str(pattern))
                 if re.search(r'_[0-9]+\.', f)]

        self.logger.debug("Generating paired heatmaps in %s -> %s",
                          pattern,
                          [str(f.relative_to(self.stage5_roots.csv_root)) for f in paths])

        if len(paths) < 2:
            self.logger.warning(("Not enough matches from pattern='%s'--"
                                 "skipping paired heatmap generation"),
                                pattern)
            return

        reader = storage.DataFrameReader('storage.csv')
        ref_df = reader(paths[0])

        for i in range(1, len(paths)):
            df = reader(paths[i])
            if comp_type == 'HMscale':
                plot_df = df / ref_df
            elif comp_type == 'HMdiff':
                plot_df = df - ref_df

            # Have to add something before the .mean to ensure that the diff CSV
            # does not get picked up by the regex above as each controller is
            # treated in turn as the primary.
            leaf = namecalc.for_output(batch_leaf,
                                       dest_stem,
                                       [0, i]) + '_paired'
            ipath = self.stage5_roots.csv_root / \
                (leaf + config.kStats['mean'].exts['mean'])
            opath = self.stage5_roots.graph_root / (leaf + config.kImageExt)

            writer = storage.DataFrameWriter('storage.csv')
            writer(plot_df, ipath, index=False)

            Heatmap(input_fpath=ipath,
                    output_fpath=opath,
                    title=title,
                    transpose=self.cmdopts['plot_transpose_graphs'],
                    zlabel=self._gen_zaxis_label(label, comp_type),
                    xlabel=criteria.graph_xlabel(cmdopts),
                    ylabel=criteria.graph_ylabel(cmdopts),
                    xtick_labels=criteria.graph_xticklabels(cmdopts),
                    ytick_labels=criteria.graph_yticklabels(cmdopts)).generate()

    def _gen_dual_heatmaps(self,
                           batch_leaf: batchroot.ExpRootLeaf,
                           criteria: bc.BivarBatchCriteria,
                           cmdopts: types.Cmdopts,
                           dest_stem: str,
                           title: str,
                           label: str,
                           legend: tp.List[str],
                           comp_type: str) -> None:
        """Generate a set of :class:`~sierra.core.graphs.heatmap.DualHeatmap` graphs.

        Graphs contain all pairings of (primary controller, other), one per
        graph, within the specified scenario after input files have been
        gathered from each controller into :attr:`stage5_roots.csv_root`. Only valid if
        the comparison type is ``HMraw``.

        """
        opath_leaf = namecalc.for_output(batch_leaf,
                                         dest_stem,
                                         None)
        opath = self.stage5_roots.graph_root / (opath_leaf + config.kImageExt)
        pattern = self.stage5_roots.csv_root / (opath_leaf + '*' +
                                                config.kStats['mean'].exts['mean'])

        paths = [pathlib.Path(f) for f in glob.glob(str(pattern))
                 if re.search('_[0-9]+', f)]

        self.logger.debug("Generating dual heatmaps in %s -> %s",
                          pattern,
                          [str(f.relative_to(self.stage5_roots.csv_root)) for f in paths])

        DualHeatmap(ipaths=paths,
                    output_fpath=opath,
                    title=title,
                    large_text=cmdopts['plot_large_text'],
                    zlabel=self._gen_zaxis_label(label, comp_type),
                    xlabel=criteria.graph_xlabel(cmdopts),
                    ylabel=criteria.graph_ylabel(cmdopts),
                    legend=legend,
                    xtick_labels=criteria.graph_xticklabels(cmdopts),
                    ytick_labels=criteria.graph_yticklabels(cmdopts)).generate()

    def _gen_graph3D(self,
                     batch_leaf: batchroot.ExpRootLeaf,
                     criteria: bc.BivarBatchCriteria,
                     cmdopts: types.Cmdopts,
                     dest_stem: str,
                     title: str,
                     zlabel: str,
                     legend: tp.List[str],
                     comp_type: str) -> None:
        """Generate a graph comparing the specified controllers within a scenario.

        Graph contains the specified controllers within thes pecified scenario
        after input files have been gathered from each controllers into
        :attr:`stage5_roots.csv_root`.

        """
        opath_leaf = namecalc.for_output(batch_leaf,
                                         dest_stem,
                                         None)
        opath = self.stage5_roots.graph_root / (opath_leaf + config.kImageExt)
        pattern = self.stage5_roots.csv_root / (opath_leaf + '*' +
                                                config.kStats['mean'].exts['mean'])

        paths = [pathlib.Path(f) for f in glob.glob(
            str(pattern)) if re.search('_[0-9]+', f)]

        self.logger.debug("Generating stacked surface graphs in %s -> %s",
                          pattern,
                          [str(f.relative_to(self.stage5_roots.csv_root)) for f in paths])

        StackedSurfaceGraph(ipaths=paths,
                            output_fpath=opath,
                            title=title,
                            ylabel=criteria.graph_xlabel(cmdopts),
                            xlabel=criteria.graph_ylabel(cmdopts),
                            zlabel=self._gen_zaxis_label(zlabel, comp_type),
                            xtick_labels=criteria.graph_yticklabels(cmdopts),
                            ytick_labels=criteria.graph_xticklabels(cmdopts),
                            legend=legend,
                            comp_type=comp_type).generate()

    def _gen_zaxis_label(self, label: str, comp_type: str) -> str:
        """Generate the Z axis label for the graph (if applicable).

        I.e., if the comparison type is not "raw", it needs a title to look like
        the prettiest girl at the ball.
        """
        if 'scale' in comp_type:
            return label + ' (Scaled)'
        elif 'diff' in comp_type:
            return label + ' (Difference Comparison)'
        return label


__api__ = ['UnivarIntraScenarioComparator', 'BivarIntraScenarioComparator']
