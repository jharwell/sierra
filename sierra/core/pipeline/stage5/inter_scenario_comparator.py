# Copyright 2019 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT

"""Classes for comparing deliverables across a set of scenarios.

Univariate batch criteria only. The same controller must be used for all
scenarios.

"""

# Core packages
import os
import copy
import typing as tp
import argparse
import logging
import pathlib

# 3rd party packages
import pandas as pd

# Project packages
from sierra.core.variables import batch_criteria as bc
import sierra.core.plugin as pm
from sierra.core import types, utils, config, storage, batchroot, graphs
from sierra.core.pipeline.stage5 import outputroot


class UnivarInterScenarioComparator:
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
                  :class:`~sierra.core.variables.batch_criteria.BatchCriteria`
                  generation for each scenario controllers are compared within,
                  as batch criteria is dependent on controller+scenario
                  definition, and needs to be re-generated for each scenario in
                  order to get graph labels/axis ticks to come out right in all
                  cases.

    """

    def __init__(
        self,
        controller: str,
        scenarios: tp.List[str],
        batch_roots: batchroot.PathSet,
        stage5_roots: outputroot.PathSet,
        cmdopts: types.Cmdopts,
        cli_args: argparse.Namespace,
        main_config: types.YAMLDict,
    ) -> None:
        self.controller = controller
        self.scenarios = scenarios
        self.stage5_roots = stage5_roots
        self.batch_roots = batch_roots

        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config
        self.logger = logging.getLogger(__name__)

    def __call__(
        self, target_graphs: tp.List[types.YAMLDict], legend: tp.List[str]
    ) -> None:
        # Obtain the list of experimental run results directories to draw from.
        batch_leaves = os.listdir(
            pathlib.Path(
                self.cmdopts["sierra_root"], self.cmdopts["project"], self.controller
            )
        )

        # The FS gives us batch leaves which might not be in the same order as
        # the list of specified scenarios, so we:
        #
        # 1. Remove all batch leaves which do not have a counterpart in the
        #    scenario list we are comparing across.
        #
        # 2. Do matching to get the indices of the batch leaves relative to the
        #    list, and then sort it.
        batch_leaves = [
            leaf for leaf in batch_leaves for s in self.scenarios if s in leaf
        ]
        indices = [
            self.scenarios.index(s)
            for leaf in batch_leaves
            for s in self.scenarios
            if s in leaf
        ]
        batch_leaves = [
            leaf
            for s, leaf in sorted(zip(indices, batch_leaves), key=lambda pair: pair[0])
        ]

        # For each controller comparison graph we are interested in, generate it
        # using data from all scenarios
        cmdopts = copy.deepcopy(self.cmdopts)
        for graph in target_graphs:
            for leaf2 in batch_leaves:
                if self._leaf_select(leaf2):
                    leaf = batchroot.ExpRootLeaf.from_name(leaf2)
                    self._compare_across_scenarios(
                        cmdopts=cmdopts, graph=graph, batch_leaf=leaf, legend=legend
                    )
                else:
                    self.logger.debug(
                        "Skipping '%s': not in scenario list %s/does not match %s",
                        leaf,
                        self.scenarios,
                        self.cli_args.batch_criteria,
                    )

    def _leaf_select(self, candidate: str) -> bool:
        """Figure out if a batch experiment root should be included in the comparison.

        Inclusion determined by if a scenario that the selected controller has
        been run on in the past is part of the set passed that the controller
        should be compared across (i.e., the controller is not compared across
        all scenarios it has ever been run on).

        """
        leaf = batchroot.ExpRootLeaf.from_name(candidate)
        return leaf.to_str() in candidate and leaf.scenario in self.scenarios

    def _compare_across_scenarios(
        self,
        cmdopts: types.Cmdopts,
        graph: types.YAMLDict,
        batch_leaf: batchroot.ExpRootLeaf,
        legend: tp.List[str],
    ) -> None:

        # We need to generate the root directory paths for each batch experiment
        # (which lives inside of the scenario dir), because they are all
        # different. We need generate these paths for EACH controller, because
        # the controller is part of the batch root path.
        pathset = batchroot.from_exp(
            sierra_root=self.cli_args.sierra_root,
            project=self.cli_args.project,
            batch_leaf=batch_leaf,
            controller=self.controller,
        )

        # For each scenario, we have to create the batch criteria for it,
        # because they are all different.
        criteria = bc.factory(
            self.main_config,
            cmdopts,
            pathset.input_root,
            self.cli_args,
            self.scenarios[0],
        )

        self._gen_csvs(
            pathset=pathset,
            project=self.cli_args.project,
            batch_leaf=batch_leaf,
            src_stem=graph["src_stem"],
            dest_stem=graph["dest_stem"],
        )

        self._gen_graph(
            criteria=criteria,
            cmdopts=cmdopts,
            batch_output_root=pathset.output_root,
            dest_stem=graph["dest_stem"],
            inc_exps=graph.get("include_exp", None),
            title=graph.get("title", None),
            label=graph["label"],
            legend=legend,
        )

    def _gen_graph(
        self,
        criteria: bc.XVarBatchCriteria,
        cmdopts: types.Cmdopts,
        batch_output_root: pathlib.Path,
        dest_stem: str,
        inc_exps: tp.Optional[str],
        title: str,
        label: str,
        legend: tp.List[str],
    ) -> None:
        """Generate graph comparing the specified controller across scenarios."""
        istem = dest_stem + "-" + self.controller
        img_ostem = dest_stem + "-" + self.controller

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
            input_stem=istem,
            stats=cmdopts["dist_stats"],
            medium=cmdopts["storage"],
            output_stem=img_ostem,
            title=title,
            xlabel=info.xlabel(cmdopts),
            ylabel=label,
            xticks=xticks,
            xticklabels=xtick_labels,
            logyscale=cmdopts["plot_log_yscale"],
            large_text=cmdopts["plot_large_text"],
            legend=legend,
        )

    def _gen_csvs(
        self,
        pathset: batchroot.PathSet,
        project: str,
        batch_leaf: batchroot.ExpRootLeaf,
        src_stem: str,
        dest_stem: str,
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

        csv_ipath_stem = pathset.stat_collate_root / src_stem

        # Some experiments might not generate the necessary performance measure
        # CSVs for graph generation, which is OK.
        csv_ipath_mean = csv_ipath_stem.with_suffix(config.kStats["mean"].exts["mean"])
        if not utils.path_exists(csv_ipath_mean):
            self.logger.warning(
                "%s missing for controller %s", csv_ipath_mean, self.controller
            )
            return

        opath_stem = pathlib.Path(
            self.stage5_roots.csv_root, dest_stem + "-" + self.controller
        )

        # Collect performance measure results. Append to existing dataframe if
        # it exists, otherwise start a new one.
        exts = config.kStats["mean"].exts
        exts.update(config.kStats["conf95"].exts)
        exts.update(config.kStats["bw"].exts)

        for k in exts:
            # Can't use with_suffix() for opath, because that path contains the
            # controller, which already has a '.' in it.
            csv_opath = opath_stem.with_name(opath_stem.name + exts[k])
            csv_ipath = csv_ipath_stem.with_suffix(exts[k])
            df = self._accum_df(csv_ipath, csv_opath, src_stem)
            if df is not None:
                storage.df_write(df, csv_opath, "storage.csv", index=False)

        # Collect performance results models and legends. Append to existing
        # dataframes if they exist, otherwise start new ones.
        # Can't use with_suffix() for opath, because that path contains the
        # controller, which already has a '.' in it.
        model_istem = pathlib.Path(pathset.model_root, src_stem)
        model_ostem = self.stage5_roots.model_root / (dest_stem + "-" + self.controller)

        model_ipath = model_istem.with_suffix(config.kModelsExt["model"])
        model_opath = model_ostem.with_name(
            model_ostem.name + config.kModelsExt["model"]
        )
        model_df = self._accum_df(model_ipath, model_opath, src_stem)
        legend_opath = model_ostem.with_name(
            model_ostem.name + config.kModelsExt["legend"]
        )

        if model_df is not None:
            storage.df_write(model_df, model_opath, "storage.csv", index=False)

            with utils.utf8open(legend_opath, "a") as f:
                sgp = pm.module_load_tiered(project=project, path="generators.scenario")
                kw = sgp.to_dict(batch_leaf.scenario)
                f.write("{0} Prediction\n".format(kw["scenario_tag"]))

    def _accum_df(
        self, ipath: pathlib.Path, opath: pathlib.Path, src_stem: str
    ) -> pd.DataFrame:
        if utils.path_exists(opath):
            cum_df = storage.df_read(opath, "storage.csv")
        else:
            cum_df = None

        if utils.path_exists(ipath):
            t = storage.df_read(ipath, "storage.csv")
            if cum_df is None:
                cum_df = pd.DataFrame(columns=t.columns)

            if len(t.index) != 1:
                self.logger.warning(
                    (
                        "'%s.csv' is a collated inter-experiment "
                        "not a summary inter-experiment csv: "
                        "# rows %s != 1"
                    ),
                    src_stem,
                    len(t.index),
                )
                self.logger.warning("Truncating '%s.csv' to last row", src_stem)

            # Series are columns, so we have to transpose before concatenating
            cum_df = pd.concat([cum_df, t.loc[t.index[-1], :].to_frame().T])

            # cum_df = cum_df.append(t.loc[t.index[-1], t.columns.to_list()])
            return cum_df

        return None


__all__ = ["UnivarInterScenarioComparator"]
