# Copyright 2019 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT

"""Classes for comparing deliverables across controllers.

Batch criteria and scenario are the same across all compared controllers.
"""

# Core packages
import os
import glob
import re
import typing as tp
import argparse
import logging
import pathlib

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core import types, utils, config, batchroot, graphs
from sierra.plugins.compare.graphs import namecalc, preprocess, outputroot, comparator


class BaseInterControllerComparator(comparator.BaseComparator):
    def __init__(
        self,
        controllers: tp.List[str],
        stage5_roots: outputroot.PathSet,
        cmdopts: types.Cmdopts,
        cli_args: argparse.Namespace,
        main_config: types.YAMLDict,
    ) -> None:
        super().__init__(controllers, stage5_roots, cmdopts, cli_args, main_config)
        self.logger = logging.getLogger(__name__)

    def exp_select(self) -> tp.List[batchroot.ExpRoot]:
        """Determine if a controller can be included in the comparison for a scenario.

        You can only compare controllers within the scenario directly generated
        from the value of ``--batch-criteria``; other scenarios will (probably)
        cause file not found errors.

        """
        # Obtain the raw list of batch experiments to use. We can just take the
        # scenario list of the first THING, because we have already checked that
        # all things were executed in the same context, and if there were any
        # warnings which will cause crashes at this stage, the user will have
        # been warned.
        batch_leaves = [
            batchroot.ExpRootLeaf.from_name(d)
            for d in os.listdir(self.project_root / self.things[0])
        ]
        selected = []
        for leaf in batch_leaves:
            for controller in self.things:
                root = batchroot.ExpRoot(
                    sierra_root=self.cmdopts["sierra_root"],
                    project=self.cmdopts["project"],
                    controller=controller,
                    leaf=leaf,
                )
                if root.to_path().exists():
                    selected.append(root)
        return selected


class UnivarInterControllerComparator(BaseInterControllerComparator):
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
                  :class:`~sierra.core.variables.batch_criteria.XVarBatchCriteria`
                  generation for each scenario controllers are compared within,
                  as batch criteria is dependent on controller+scenario
                  definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all
                  cases.

    """

    def __init__(
        self,
        controllers: tp.List[str],
        stage5_roots: outputroot.PathSet,
        cmdopts: types.Cmdopts,
        cli_args: argparse.Namespace,
        main_config: types.YAMLDict,
    ) -> None:
        super().__init__(controllers, stage5_roots, cmdopts, cli_args, main_config)

    def compare(
        self,
        cmdopts: types.Cmdopts,
        graph: types.YAMLDict,
        roots: tp.List[batchroot.ExpRoot],
        legend: tp.List[str],
    ) -> None:

        for controller in self.things:
            valid_configurations = sum(r.controller == controller for r in roots)
            if valid_configurations > 1:
                self.logger.warning(
                    "Skipping ambiguous comparison for controller %s: was run on multiple selected batch roots %s",
                    controller,
                    [r.to_str() for r in roots],
                )
                continue

            if valid_configurations == 0:
                self.logger.warning(
                    "Skipping comparison for controller %s: not run on any selected batch roots %s",
                    controller,
                    [r.to_str() for r in roots],
                )
                continue

            # Each controller should have been run on exactly ONE batch
            # experiment that we selected for controller comparison, by
            # definition.
            root = next(r for r in roots if r.controller == controller)

            # We need to generate the root directory paths for each batch
            # experiment (which # lives inside of the scenario dir), because
            # they are all different. We need generate these paths for EACH
            # controller, because the controller is part of the batch root path.
            pathset = batchroot.from_exp(
                sierra_root=self.cli_args.sierra_root,
                project=self.cli_args.project,
                batch_leaf=root.leaf,
                controller=controller,
            )

            # For each scenario, we have to create the batch criteria for it,
            # because they are all different.
            criteria = bc.factory(
                self.main_config,
                cmdopts,
                pathset.input_root,
                self.cli_args,
                root.leaf.scenario,
            )

            # We incrementally generate the CSV, adding a new column for each
            # controller as we iterate.
            self._accum_csv(
                batch_leaf=root.leaf,
                criteria=criteria,
                pathset=pathset,
                controller=controller,
                src_stem=graph["src_stem"],
                dest_stem=graph["dest_stem"],
                index=graph.get("index", -1),
                inc_exps=graph.get("include_exp", None),
            )

        # After the CSV has been generated, we can generate the graph. We can
        # use any controller when computing the batch leaf, since they are all
        # the same in this comparison, by definition.
        root = next(r for r in roots if r.controller == self.things[0])
        self._gen_graph(
            batch_leaf=root.leaf,
            criteria=criteria,
            cmdopts=cmdopts,
            batch_output_root=pathset.output_root,
            dest_stem=graph["dest_stem"],
            title=graph.get("title", ""),
            label=graph.get("label", ""),
            inc_exps=graph.get("include_exp", None),
            legend=legend,
            backend=graph.get("backend", cmdopts["graphs_backend"]),
        )

    def _accum_csv(
        self,
        batch_leaf: batchroot.ExpRootLeaf,
        criteria: bc.XVarBatchCriteria,
        pathset: batchroot.PathSet,
        controller: str,
        src_stem: str,
        dest_stem: str,
        index: int,
        inc_exps: tp.Optional[str],
    ) -> None:
        """Accumulate info in a CSV file for inter-controller comparison."""
        self.logger.debug(
            "Gathering data for %s from %s -> %s", controller, src_stem, dest_stem
        )
        ipath = pathset.stat_interexp_root / (
            src_stem + config.kStats["mean"].exts["mean"]
        )

        # Some experiments might not generate the necessary performance measure
        # .csvs for graph generation, which is OK.
        if not utils.path_exists(ipath):
            self.logger.warning("%s missing for controller %s", ipath, controller)
            return

        preparer = preprocess.IntraExpPreparer(
            ipath_stem=pathset.stat_interexp_root,
            ipath_leaf=src_stem,
            opath_stem=self.stage5_roots.csv_root,
            criteria=criteria,
        )
        opath_leaf = namecalc.for_cc(batch_leaf, dest_stem, None)
        preparer.for_cc(
            controller=controller, opath_leaf=opath_leaf, index=index, inc_exps=inc_exps
        )

    def _gen_graph(
        self,
        batch_leaf: batchroot.ExpRootLeaf,
        criteria: bc.XVarBatchCriteria,
        cmdopts: types.Cmdopts,
        batch_output_root: pathlib.Path,
        dest_stem: str,
        title: str,
        label: str,
        inc_exps: tp.Optional[str],
        legend: tp.List[str],
        backend: str,
    ) -> None:
        """Generate a graph comparing the specified controllers within a scenario."""
        opath_leaf = namecalc.for_cc(batch_leaf, dest_stem, None)

        info = criteria.graph_info(cmdopts, batch_output_root=batch_output_root)

        if inc_exps is not None:
            xtick_labels = utils.exp_include_filter(
                inc_exps, info.xticklabels, criteria.n_exp()
            )
            xticks = utils.exp_include_filter(inc_exps, info.xticks, criteria.n_exp())

        paths = graphs.PathSet(
            input_root=self.stage5_roots.csv_root,
            output_root=self.stage5_roots.graph_root,
            batchroot=pathlib.Path(
                self.cmdopts["sierra_root"], self.cmdopts["project"]
            ),
            model_root=None,
        )

        graphs.summary_line(
            paths=paths,
            input_stem=opath_leaf,
            output_stem=opath_leaf,
            stats=cmdopts["dist_stats"],
            medium="storage.csv",
            title=title,
            xlabel=info.xlabel,
            ylabel=label,
            backend=backend,
            xticklabels=xtick_labels,
            xticks=xticks,
            logyscale=cmdopts["plot_log_yscale"],
            large_text=self.cmdopts["plot_large_text"],
            legend=legend,
        )


class BivarInterControllerComparator(BaseInterControllerComparator):
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
                  :class:`~sierra.core.variables.batch_criteria.XVarBatchCriteria`
                  generation for each scenario controllers are compared within,
                  as batch criteria is dependent on controller+scenario
                  definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all
                  cases.
    """

    def __init__(
        self,
        controllers: tp.List[str],
        stage5_roots: outputroot.PathSet,
        cmdopts: types.Cmdopts,
        cli_args: argparse.Namespace,
        main_config: types.YAMLDict,
    ) -> None:
        super().__init__(controllers, stage5_roots, cmdopts, cli_args, main_config)

    def compare(
        self,
        cmdopts: types.Cmdopts,
        graph: types.YAMLDict,
        roots: tp.List[batchroot.ExpRoot],
        legend: tp.List[str],
    ) -> None:

        for controller in self.things:
            valid_configurations = sum(r.controller == controller for r in roots)
            if valid_configurations > 1:
                self.logger.warning(
                    "Skipping ambiguous comparison for controller %s: was run on multiple selected batch roots %s",
                    controller,
                    [r.to_str() for r in roots],
                )
                continue

            if valid_configurations == 0:
                self.logger.warning(
                    "Skipping comparison for controller %s: not run on any selected batch roots %s",
                    controller,
                    [r.to_str() for r in roots],
                )
                continue

            # Each controller should have been run on exactly ONE batch
            # experiment that we selected for controller comparison, by
            # definition.
            root = next(r for r in roots if r.controller == controller)

            # We need to generate the root directory paths for each batch
            # experiment (which # lives inside of the scenario dir), because
            # they are all different. We need generate these paths for EACH
            # controller, because the controller is part of the batch root path.
            pathset = batchroot.from_exp(
                sierra_root=self.cli_args.sierra_root,
                project=self.cli_args.project,
                batch_leaf=root.leaf,
                controller=controller,
            )

            # For each scenario, we have to create the batch criteria for it,
            # because they are all different.
            criteria = bc.factory(
                self.main_config,
                cmdopts,
                pathset.input_root,
                self.cli_args,
                root.leaf.scenario,
            )

            if self.cli_args.comparison_type == "LNraw":
                self._gen_csvs_for_1D(
                    cmdopts=cmdopts,
                    criteria=criteria,
                    pathset=pathset,
                    controller=controller,
                    batch_leaf=root.leaf,
                    src_stem=graph["src_stem"],
                    dest_stem=graph["dest_stem"],
                    primary_axis=graph.get("primary_axis", 0),
                    inc_exps=graph.get("include_exp", None),
                    index=graph.get("index", -1),
                )

        if self.cli_args.comparison_type == "LNraw":
            self._gen_graphs1D(
                batch_leaf=root.leaf,
                criteria=criteria,
                cmdopts=cmdopts,
                pathset=pathset,
                dest_stem=graph["dest_stem"],
                title=graph.get("title", ""),
                label=graph.get("label", ""),
                primary_axis=graph.get("primary_axis", 0),
                inc_exps=graph.get("include_exp", None),
                index=graph.get("index", -1),
                legend=legend,
            )

    def _gen_csvs_for_1D(
        self,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
        criteria: bc.XVarBatchCriteria,
        batch_leaf: batchroot.ExpRootLeaf,
        controller: str,
        src_stem: str,
        dest_stem: str,
        primary_axis: int,
        index: int,
        inc_exps: tp.Optional[str],
    ) -> None:
        """Generate a set of CSV files for use in intra-scenario graph generation.

        Because we are targeting linegraphs, we draw the the i-th row/col (as
        configured) from the performance results of each controller .csv, and
        concatenate them into a new .csv file which can be given to
        :func:`~sierra.core.graphs.summary_line`.

        """
        self.logger.debug(
            "Gathering data for '%s' from %s -> %s", controller, src_stem, dest_stem
        )

        csv_ipath = pathset.stat_interexp_root / (
            src_stem + config.kStats["mean"].exts["mean"]
        )

        # Some experiments might not generate the necessary performance measure
        # .csvs for graph generation, which is OK.
        if not utils.path_exists(csv_ipath):
            self.logger.warning("%s missing for controller '%s'", csv_ipath, controller)
            return

        if cmdopts["dist_stats"] != "none":
            self.logger.warning(
                (
                    "--dist-stats is not supported with "
                    "1D CSVs sliced from 2D CSV for linegraph "
                    "generation: no stats will be included"
                )
            )

        if primary_axis == 0:
            preparer = preprocess.IntraExpPreparer(
                ipath_stem=pathset.stat_interexp_root,
                ipath_leaf=src_stem,
                opath_stem=self.stage5_roots.csv_root,
                criteria=criteria,
            )

            opath_leaf = namecalc.for_cc(batch_leaf, dest_stem, [index])
            preparer.for_cc(
                controller, opath_leaf=opath_leaf, index=index, inc_exps=inc_exps
            )
        else:
            preparer = preprocess.IntraExpPreparer(
                ipath_stem=pathset.stat_interexp_root,
                ipath_leaf=src_stem,
                opath_stem=self.stage5_roots.csv_root,
                criteria=criteria,
            )

            exp_dirs = criteria.gen_exp_names()
            xlabels, ylabels = utils.bivar_exp_labels_calc(exp_dirs)
            xlabels = utils.exp_include_filter(
                inc_exps, xlabels, criteria.criteria1.n_exp()
            )

            for col in ylabels:
                col_index = ylabels.index(col)
                opath_leaf = namecalc.for_cc(batch_leaf, dest_stem, [col_index])
                preparer.across_cols(
                    opath_leaf=opath_leaf,
                    col_index=col_index,
                    all_cols=xlabels,
                    inc_exps=inc_exps,
                )

    def _gen_graphs1D(
        self,
        batch_leaf: batchroot.ExpRootLeaf,
        criteria: bc.XVarBatchCriteria,
        pathset: batchroot.PathSet,
        cmdopts: types.Cmdopts,
        dest_stem: str,
        title: str,
        label: str,
        primary_axis: int,
        index: int,
        inc_exps: tp.Optional[str],
        legend: tp.List[str],
    ) -> None:
        oleaf = namecalc.for_cc(batch_leaf, dest_stem, None)
        csv_stem_root = self.stage5_roots.csv_root / oleaf
        pattern = str(csv_stem_root) + "*" + config.kStats["mean"].exts["mean"]
        paths = [f for f in glob.glob(pattern) if re.search("_[0-9]+", f)]

        opath_leaf = namecalc.for_cc(batch_leaf, dest_stem, [index])

        info = criteria.graph_info(cmdopts, batch_output_root=pathset.output_root)
        if primary_axis == 0:
            n_exp = criteria.criterias[0].n_exp()
            yticks = info.yticks
            xticks = utils.exp_include_filter(inc_exps, yticks, n_exp)

            ytick_labels = info.yticklabels
            xtick_labels = utils.exp_include_filter(inc_exps, ytick_labels, n_exp)
            xlabel = info.ylabel
        else:
            n_exp = criteria.criterias[1].n_exp()
            yticks = info.xticks
            xticks = utils.exp_include_filter(inc_exps, yticks, n_exp)

            ytick_labels = info.xticklabels
            xtick_labels = utils.exp_include_filter(inc_exps, ytick_labels, n_exp)
            xlabel = info.xlabel

        # TODO: Fix no statistics support for these graphs
        paths = graphs.PathSet(
            input_root=self.stage5_roots.csv_root,
            output_root=self.stage5_roots.graph_root,
            batchroot=pathlib.Path(
                self.cmdopts["sierra_root"], self.cmdopts["project"]
            ),
            model_root=None,
        )

        graphs.summary_line(
            paths=paths,
            input_stem=opath_leaf,
            output_stem=opath_leaf,
            medium="storage.csv",
            stats="none",
            title=title,
            xlabel=xlabel,
            ylabel=label,
            backend=cmdopts["graphs_backend"],
            xticks=xticks,
            xticklabels=xtick_labels,
            legend=legend,
            logyscale=cmdopts["plot_log_yscale"],
            large_text=cmdopts["plot_large_text"],
        )


__all__ = ["UnivarInterControllerComparator", "BivarInterControllerComparator"]
