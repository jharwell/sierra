# Copyright 2019 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT

"""Classes for comparing deliverables across a set of scenarios.

Univariate batch criteria only. The same controller must be used for all
scenarios.

"""

# Core packages
import typing as tp
import argparse
import logging
import pathlib

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
import sierra.core.plugin as pm
from sierra.core import types, utils, config, storage, batchroot, graphs
from sierra.plugins.compare.graphs import outputroot, preprocess, namecalc, comparator


class UnivarInterScenarioComparator(comparator.BaseComparator):
    """Compares a single controller across a set of scenarios.

    Graph generation is controlled via a config file parsed in
    :class:`~sierra.core.pipeline.stage5.pipeline_stage5.PipelineStage5`.

    Univariate batch criteria only.

    Attributes:
        controller: Controller to use.

        scenarios: List of scenario names to compare ``controller`` across.

        sc_csv_root: Absolute directory path to the location scenario CSV
                     files should be output to.

        sc_graph_root: Absolute directory path to the location the generated
                       graphs should be output to.

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
        controller: str,
        scenarios: list[str],
        stage5_roots: outputroot.PathSet,
        cmdopts: types.Cmdopts,
        cli_args: argparse.Namespace,
        main_config: types.YAMLDict,
    ) -> None:
        super().__init__(scenarios, stage5_roots, cmdopts, cli_args, main_config)
        self.logger = logging.getLogger(__name__)
        self.controller = controller

    def exp_select(self) -> list[batchroot.ExpRoot]:
        """
        Determine if a scenario can be include in the comparison for a controller.

        """
        selected = []
        for scenario in self.things:
            for candidate in (self.project_root / self.controller / scenario).iterdir():
                root = batchroot.ExpRoot(
                    sierra_root=self.cmdopts["sierra_root"],
                    project=self.cmdopts["project"],
                    controller=self.controller,
                    leaf=batchroot.ExpRootLeaf.from_name(candidate.name),
                    scenario=scenario,
                )
                if root.to_path().exists():
                    selected.append(root)
        return selected

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
            "backend": graph.get("backend", cmdopts["graphs_backend"]),
        }

        for scenario in self.things:
            valid_configurations = sum(r.scenario == scenario for r in roots)
            if valid_configurations > 1:
                self.logger.warning(
                    "Skipping ambiguous comparison for scenario %s: was run on multiple selected batch roots %s",
                    scenario,
                    [r.to_str() for r in roots],
                )
                continue

            if valid_configurations == 0:
                self.logger.warning(
                    "Skipping comparison for scenario %s: not run on any selected batch roots %s",
                    scenario,
                    [r.to_str() for r in roots],
                )
                continue

            # Each controller should have been run on exactly ONE batch
            # experiment that we selected for controller comparison, by
            # definition.
            root = next(r for r in roots if r.scenario == scenario)

            # We need to generate the root directory paths for each batch
            # experiment (which lives inside of the scenario dir), because they
            # are all different. We need generate these paths for EACH
            # controller, because the controller is part of the batch root path.
            pathset = batchroot.from_exp(
                sierra_root=self.cli_args.sierra_root,
                project=self.cli_args.project,
                batch_leaf=root.leaf,
                controller=self.controller,
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

            self._gen_csvs(
                criteria=criteria,
                pathset=pathset,
                project=self.cli_args.project,
                root=root,
                spec=graph_spec,
            )

            self._gen_graph(
                batch_leaf=root.leaf,
                criteria=criteria,
                cmdopts=cmdopts,
                batch_output_root=pathset.output_root,
                spec=graph_spec,
            )

    def _gen_graph(
        self,
        batch_leaf: batchroot.ExpRootLeaf,
        criteria: bc.XVarBatchCriteria,
        cmdopts: types.Cmdopts,
        batch_output_root: pathlib.Path,
        spec: dict,
    ) -> None:
        """Generate graph comparing the specified controller across scenarios."""
        opath_leaf = namecalc.for_sc(batch_leaf, self.things, spec["dest_stem"], None)
        info = criteria.graph_info(cmdopts, batch_output_root=batch_output_root)

        xticklabels = info.xticklabels
        xticks = info.xticks
        if spec["inc_exps"] is not None:
            xticklabels = utils.exp_include_filter(
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
            stats=cmdopts.get("dist_stats", "none"),
            medium=cmdopts["storage"],
            output_stem=opath_leaf,
            title=spec["title"],
            xlabel=info.xlabel,
            ylabel=spec["label"],
            backend=spec["backend"],
            xticks=xticks,
            xticklabels=xticklabels,
            logyscale=cmdopts["plot_log_yscale"],
            large_text=cmdopts["plot_large_text"],
            legend=spec["legend"],
        )

    def _gen_csvs(
        self,
        criteria: bc.XVarBatchCriteria,
        pathset: batchroot.PathSet,
        project: str,
        root: batchroot.ExpRoot,
        spec: dict,
    ) -> None:
        """Generate a set of CSV files for use in inter-scenario graph generation.

        Generates:

        - ``.mean`` CSV file containing results for each scenario the controller
           is being compared across, 1 per line.

        - Stastics CSV files containing various statistics for the ``.mean`` CSV
          file, 1 per line.

        - ``.model`` file containing model predictions for controller behavior
          during each scenario, 1 per line (not generated if models were not run
          the performance measures we are generating graphs for).

        - ``.legend`` file containing legend values for models to plot (not
          generated if models were not run for the performance measures we are
          generating graphs for).

        """

        csv_ipath_stem = pathset.stat_interexp_root / spec["src_stem"]

        # Some experiments might not generate the necessary performance measure
        # CSVs for graph generation, which is OK.
        csv_ipath_mean = csv_ipath_stem.with_suffix(config.STATS["mean"].exts["mean"])
        if not utils.path_exists(csv_ipath_mean):
            self.logger.warning(
                "%s missing for controller %s", csv_ipath_mean, self.controller
            )
            return

        preparer = preprocess.IntraExpPreparer(
            ipath_stem=pathset.stat_interexp_root,
            ipath_leaf=spec["src_stem"],
            opath_stem=self.stage5_roots.csv_root,
            criteria=criteria,
        )
        opath_leaf = namecalc.for_sc(root.leaf, self.things, spec["dest_stem"], None)

        preparer.for_sc(
            scenario=root.scenario,
            opath_leaf=opath_leaf,
            index=spec["index"],
            inc_exps=None,
        )

        # Collect performance results models and legends. Append to existing
        # dataframes if they exist, otherwise start new ones.
        # Can't use with_suffix() for opath, because that path contains the
        # controller, which already has a '.' in it.
        model_ostem = self.stage5_roots.model_root / (
            spec["dest_stem"] + "-" + self.controller
        )

        model_opath = model_ostem.with_name(
            model_ostem.name + config.MODELS_EXT["model"]
        )
        model_df = None
        legend_opath = model_ostem.with_name(
            model_ostem.name + config.MODELS_EXT["legend"]
        )

        if model_df is not None:
            storage.df_write(model_df, model_opath, "storage.csv", index=False)

            with utils.utf8open(legend_opath, "a") as f:
                sgp = pm.module_load_tiered(project=project, path="generators.scenario")
                kw = sgp.to_dict(root.scenario)
                f.write("{} Model Prediction\n".format(kw["scenario_tag"]))


__all__ = ["UnivarInterScenarioComparator"]
