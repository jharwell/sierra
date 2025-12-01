# Copyright 2019 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT

"""Classes for comparing deliverables across controllers.

Batch criteria and scenario are the same across all compared controllers.
"""

# Core packages
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
        controllers: list[str],
        stage5_roots: outputroot.PathSet,
        cmdopts: types.Cmdopts,
        cli_args: argparse.Namespace,
        main_config: types.YAMLDict,
    ) -> None:
        super().__init__(controllers, stage5_roots, cmdopts, cli_args, main_config)
        self.logger = logging.getLogger(__name__)

    def exp_select(self) -> list[batchroot.ExpRoot]:
        """Determine if a controller can be included in the comparison for a scenario."""
        # Obtain the raw list of batch experiments to use. We can just take the
        # scenario list of the first THING, because we have already checked that
        # all things were executed in the same context, and if there were any
        # warnings which will cause crashes at this stage, the user will have
        # been warned.
        selected = []
        for controller in self.things:
            for scenario in (self.project_root / self.things[0]).iterdir():
                for candidate in scenario.iterdir():
                    root = batchroot.ExpRoot(
                        sierra_root=self.cmdopts["sierra_root"],
                        project=self.cmdopts["project"],
                        controller=controller,
                        leaf=batchroot.ExpRootLeaf.from_name(candidate.name),
                        scenario=str(scenario),
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
        controllers: list[str],
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
        roots: list[batchroot.ExpRoot],
        legend: list[str],
    ) -> None:

        graph_spec = {
            "src_stem": graph["src_stem"],
            "index": graph.get("index", -1),
            "dest_stem": graph["dest_stem"],
            "title": graph.get("title", ""),
            "label": graph.get("label", ""),
            "inc_exps": graph.get("include_exp", None),
            "legend": legend,
            "backend": graph.get("backend", cmdopts["graphs_backend"]),
        }

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
                scenario=root.scenario,
            )

            # For each scenario, we have to create the batch criteria for it,
            # because they are all different.
            criteria = bc.factory(
                self.main_config,
                cmdopts,
                pathset.input_root,
                self.cli_args,
                root.scenario,
            )

            # We incrementally generate the CSV, adding a new column for each
            # controller as we iterate.
            self._accum_csv(
                batch_leaf=root.leaf,
                criteria=criteria,
                pathset=pathset,
                controller=controller,
                spec=graph_spec,
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
            spec=graph_spec,
        )

    def _accum_csv(
        self,
        batch_leaf: batchroot.ExpRootLeaf,
        criteria: bc.XVarBatchCriteria,
        pathset: batchroot.PathSet,
        controller: str,
        spec: types.SimpleDict,
    ) -> None:
        """Accumulate info in a CSV file for inter-controller comparison."""
        self.logger.debug(
            "Gathering data for %s from %s -> %s",
            controller,
            spec["src_stem"],
            spec["dest_stem"],
        )
        ipath = pathset.stat_interexp_root / (
            spec["src_stem"] + config.STATS["mean"].exts["mean"]
        )

        # Some experiments might not generate the necessary performance measure
        # .csvs for graph generation, which is OK.
        if not utils.path_exists(ipath):
            self.logger.warning("%s missing for controller %s", ipath, controller)
            return

        preparer = preprocess.IntraExpPreparer(
            ipath_stem=pathset.stat_interexp_root,
            ipath_leaf=spec["src_stem"],
            opath_stem=self.stage5_roots.csv_root,
            criteria=criteria,
        )
        opath_leaf = namecalc.for_cc(batch_leaf, spec["dest_stem"], None)
        preparer.for_cc(
            controller=controller,
            opath_leaf=opath_leaf,
            index=spec["index"],
            inc_exps=spec["inc_exps"],
        )

    def _gen_graph(
        self,
        batch_leaf: batchroot.ExpRootLeaf,
        criteria: bc.XVarBatchCriteria,
        cmdopts: types.Cmdopts,
        batch_output_root: pathlib.Path,
        spec: dict,
    ) -> None:
        """Generate a graph comparing the specified controllers within a scenario."""
        opath_leaf = namecalc.for_cc(batch_leaf, spec["dest_stem"], None)

        info = criteria.graph_info(cmdopts, batch_output_root=batch_output_root)

        xtick_labels = utils.exp_include_filter(
            spec["inc_exps"], info.xticklabels, criteria.n_exp()
        )
        xticks = utils.exp_include_filter(
            spec["inc_exps"], info.xticks, criteria.n_exp()
        )

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
            stats=cmdopts.get("dist_stats", "none"),
            medium="storage.csv",
            title=spec["title"],
            xlabel=info.xlabel,
            ylabel=spec["label"],
            backend=spec["backend"],
            xticklabels=xtick_labels,
            xticks=xticks,
            logyscale=cmdopts["plot_log_yscale"],
            large_text=self.cmdopts["plot_large_text"],
            legend=spec["legend"],
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
        controllers: list[str],
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
        roots: list[batchroot.ExpRoot],
        legend: list[str],
    ) -> None:

        graph_spec = {
            "index": graph.get("index", -1),
            "src_stem": graph["src_stem"],
            "dest_stem": graph["dest_stem"],
            "title": graph.get("title", ""),
            "label": graph.get("label", ""),
            "inc_exps": graph.get("include_exp", None),
            "legend": legend,
            "primary_axis": graph.get("primary_axis", 0),
        }
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
                scenario=root.scenario,
            )

            # For each scenario, we have to create the batch criteria for it,
            # because they are all different.
            criteria = bc.factory(
                self.main_config,
                cmdopts,
                pathset.input_root,
                self.cli_args,
                root.scenario,
            )

            if self.cli_args.comparison_type == "LNraw":
                self._gen_csvs_1d(
                    cmdopts=cmdopts,
                    criteria=criteria,
                    pathset=pathset,
                    controller=controller,
                    batch_leaf=root.leaf,
                    spec=graph_spec,
                )

        if self.cli_args.comparison_type == "LNraw":

            self._gen_graphs_1d(
                batch_leaf=root.leaf,
                criteria=criteria,
                cmdopts=cmdopts,
                pathset=pathset,
                spec=graph_spec,
            )

    def _gen_csvs_1d(
        self,
        cmdopts: types.Cmdopts,
        pathset: batchroot.PathSet,
        criteria: bc.XVarBatchCriteria,
        batch_leaf: batchroot.ExpRootLeaf,
        controller: str,
        spec: types.SimpleDict,
    ) -> None:
        """Generate a set of CSV files for use in intra-scenario graph generation.

        Because we are targeting linegraphs, we draw the the i-th row/col (as
        configured) from the performance results of each controller .csv, and
        concatenate them into a new .csv file which can be given to
        :func:`~sierra.core.graphs.summary_line`.

        """
        self.logger.debug(
            "Gathering data for '%s' from %s -> %s",
            controller,
            spec["src_stem"],
            spec["dest_stem"],
        )

        csv_ipath = pathset.stat_interexp_root / (
            spec["src_stem"] + config.STATS["mean"].exts["mean"]
        )

        # Some experiments might not generate the necessary performance measure
        # .csvs for graph generation, which is OK.
        if not utils.path_exists(csv_ipath):
            self.logger.warning("%s missing for controller '%s'", csv_ipath, controller)
            return

        if cmdopts["dist_stats"] != "none":
            self.logger.warning(
                "--dist-stats is not supported with "
                "1D CSVs sliced from 2D CSV for linegraph "
                "generation: no stats will be included"
            )

        if spec["primary_axis"] == 0:
            preparer = preprocess.IntraExpPreparer(
                ipath_stem=pathset.stat_interexp_root,
                ipath_leaf=spec["src_stem"],
                opath_stem=self.stage5_roots.csv_root,
                criteria=criteria,
            )

            opath_leaf = namecalc.for_cc(batch_leaf, spec["dest_stem"], [spec["index"]])
            preparer.for_cc(
                controller,
                opath_leaf=opath_leaf,
                index=spec["index"],
                inc_exps=spec["inc_exps"],
            )
        else:
            preparer = preprocess.IntraExpPreparer(
                ipath_stem=pathset.stat_interexp_root,
                ipath_leaf=spec["src_stem"],
                opath_stem=self.stage5_roots.csv_root,
                criteria=criteria,
            )

            exp_dirs = criteria.gen_exp_names()
            xlabels, ylabels = utils.bivar_exp_labels_calc(exp_dirs)
            xlabels = utils.exp_include_filter(
                spec["inc_exps"], xlabels, criteria.criteria1.n_exp()
            )

            for col in ylabels:
                col_index = ylabels.index(col)
                opath_leaf = namecalc.for_cc(batch_leaf, spec["dest_stem"], [col_index])
                preparer.for_cc(
                    controller,
                    opath_leaf=opath_leaf,
                    index=col_index,
                    inc_exps=spec["inc_exps"],
                )

    def _gen_graphs_1d(
        self,
        batch_leaf: batchroot.ExpRootLeaf,
        criteria: bc.XVarBatchCriteria,
        pathset: batchroot.PathSet,
        cmdopts: types.Cmdopts,
        spec: dict,
    ) -> None:
        oleaf = namecalc.for_cc(batch_leaf, spec["dest_stem"], None)
        csv_stem_root = self.stage5_roots.csv_root / oleaf
        pattern = "*" + config.STATS["mean"].exts["mean"]
        paths = [f for f in csv_stem_root.glob(pattern) if re.search("_[0-9]+", str(f))]

        opath_leaf = namecalc.for_cc(batch_leaf, spec["dest_stem"], [spec["index"]])

        info = criteria.graph_info(cmdopts, batch_output_root=pathset.output_root)
        if spec["primary_axis"] == 0:
            n_exp = criteria.criterias[0].n_exp()
            yticks = info.yticks
            xticks = utils.exp_include_filter(spec["inc_exps"], yticks, n_exp)

            ytick_labels = info.yticklabels
            xtick_labels = utils.exp_include_filter(
                spec["inc_exps"], ytick_labels, n_exp
            )
            xlabel = info.ylabel
        else:
            n_exp = criteria.criterias[1].n_exp()
            yticks = info.xticks
            xticks = utils.exp_include_filter(spec["inc_exps"], yticks, n_exp)

            ytick_labels = info.xticklabels
            xtick_labels = utils.exp_include_filter(
                spec["inc_exps"], ytick_labels, n_exp
            )
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
            title=spec["title"],
            xlabel=xlabel,
            ylabel=spec["label"],
            backend=cmdopts["graphs_backend"],
            xticks=xticks,
            xticklabels=xtick_labels,
            legend=spec["legend"],
            logyscale=cmdopts["plot_log_yscale"],
            large_text=cmdopts["plot_large_text"],
        )


__all__ = ["BivarInterControllerComparator", "UnivarInterControllerComparator"]
