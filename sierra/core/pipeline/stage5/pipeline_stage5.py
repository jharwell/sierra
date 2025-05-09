# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Stage 5 of the experimental pipeline: comparing deliverables."""

# Core packages
import logging
import pathlib
import typing as tp
import argparse

# 3rd party packages
import yaml

# Project packages
from sierra.core.pipeline.stage5 import intra_scenario_comparator as intrasc
from sierra.core.pipeline.stage5 import inter_scenario_comparator as intersc
from sierra.core.pipeline.stage5 import outputroot
from sierra.core import types, utils, config, batchroot


class PipelineStage5:
    """Compare controllers within or across scenarios.

    This can be either:

    #. Compare a set of controllers within the same scenario using performance
       measures specified in YAML configuration.

    #. Compare a single controller across a set ofscenarios using performance
       measures specified in YAML configuration.

    This stage is idempotent.

    Attributes:
        cmdopts: Dictionary of parsed cmdline parameters.

        controllers: List of controllers to compare.

        main_config: Dictionary of parsed main YAML configuration.

        stage5_config: Dictionary of parsed stage5 YAML configuration.

        output_roots: Dictionary containing output directories for intra- and
                      inter-scenario graph generation.

    """

    def __init__(
        self,
        main_config: types.YAMLDict,
        cmdopts: types.Cmdopts,
        batch_roots: batchroot.PathSet,
    ) -> None:
        self.cmdopts = cmdopts
        self.main_config = main_config
        self.batch_roots = batch_roots

        path = pathlib.Path(self.cmdopts["project_config_root"], config.kYAML.stage5)

        with utils.utf8open(path) as f:
            self.stage5_config = yaml.load(f, yaml.FullLoader)

        self.logger = logging.getLogger(__name__)

        if self.cmdopts["controllers_list"] is not None:
            self.controllers = self.cmdopts["controllers_list"].split(",")
        else:
            self.controllers = []

        if self.cmdopts["scenarios_list"] is not None:
            self.scenarios = self.cmdopts["scenarios_list"].split(",")
        else:
            self.scenarios = []

        self.stage5_roots = outputroot.PathSet(
            cmdopts, self.controllers, self.scenarios
        )

        self.project_root = pathlib.Path(
            self.cmdopts["sierra_root"], self.cmdopts["project"]
        )

    def run(self, cli_args: argparse.Namespace) -> None:
        """Run stage 5 of the experimental pipeline.

        If ``--controller-comparison`` was passed:

        #. :class:`~sierra.core.pipeline.stage5.intra_scenario_comparator.UnivarIntraScenarioComparator`
            or
            :class:`~sierra.core.pipeline.stage5.intra_scenario_comparator.BivarIntraScenarioComparator`
            as appropriate, depending on which type of
            :class:`~sierra.core.variables.batch_criteria.BatchCriteria` was
            selected on the cmdline.

        If ``--scenario-comparison`` was passed:

        #. :class:`~sierra.core.pipeline.stage5.inter_scenario_comparator.UnivarInterScenarioComparator`
            (only valid for univariate batch criteria currently).

        """
        # Create directories for .csv files and graphs
        utils.dir_create_checked(self.stage5_roots.graph_root, True)
        utils.dir_create_checked(self.stage5_roots.csv_root, True)

        if self.stage5_roots.model_root is not None:
            utils.dir_create_checked(self.stage5_roots.model_root, True)

        if self.cmdopts["controller_comparison"]:
            self._run_cc(cli_args)
        elif self.cmdopts["scenario_comparison"]:
            self._run_sc(cli_args)

    def _run_cc(self, cli_args: argparse.Namespace) -> None:
        # Use nice controller names on graph legends if configured
        if self.cmdopts["controllers_legend"] is not None:
            legend = self.cmdopts["controllers_legend"].split(",")
        else:
            legend = self.controllers

        self._verify_comparability(self.controllers, cli_args)

        self.logger.info("Inter-batch controller comparison of %s...", self.controllers)

        if cli_args.bc_univar:
            univar = intrasc.UnivarIntraScenarioComparator(
                self.controllers,
                self.batch_roots,
                self.stage5_roots,
                self.cmdopts,
                cli_args,
                self.main_config,
            )
            univar(
                target_graphs=self.stage5_config["intra_scenario"]["graphs"],
                legend=legend,
                comp_type=self.cmdopts["comparison_type"],
            )
        else:
            bivar = intrasc.BivarIntraScenarioComparator(
                self.controllers,
                self.stage5_roots,
                self.cmdopts,
                cli_args,
                self.main_config,
            )
            bivar(
                target_graphs=self.stage5_config["intra_scenario"]["graphs"],
                legend=legend,
                comp_type=self.cmdopts["comparison_type"],
            )

        self.logger.info("Inter-batch controller comparison complete")

    def _run_sc(self, cli_args: argparse.Namespace) -> None:
        # Use nice scenario names on graph legends if configured
        if self.cmdopts["scenarios_legend"] is not None:
            legend = self.cmdopts["scenarios_legend"].split(",")
        else:
            legend = self.scenarios

        controller = cli_args.controller

        self.logger.info(
            "Inter-batch  comparison of %s across %s...", controller, self.scenarios
        )

        assert (
            cli_args.bc_univar
        ), "inter-scenario controller comparison only valid for univariate batch criteria"

        comparator = intersc.UnivarInterScenarioComparator(
            controller,
            self.scenarios,
            self.batch_roots,
            self.stage5_roots,
            self.cmdopts,
            cli_args,
            self.main_config,
        )

        comparator(
            target_graphs=self.stage5_config["inter_scenario"]["graphs"], legend=legend
        )

        self.logger.info(
            "Inter-batch  comparison of %s across %s complete",
            controller,
            self.scenarios,
        )

    def _verify_comparability(
        self, controllers: tp.List[str], cli_args: argparse.Namespace
    ) -> None:
        """Check if the specified controllers can be compared.

        Comparable controllers have all been run on the same set of batch
        experiments. If they have not, it is not `necessarily` an error, but
        probably should be looked at, so it is only a warning, not fatal.

        """
        for c1 in controllers:
            for item in (self.project_root / c1).iterdir():
                leaf = batchroot.ExpRootLeaf.from_name(item.name)

                for c2 in controllers:
                    opts1 = batchroot.from_exp(
                        sierra_root=self.cmdopts["sierra_root"],
                        project=self.cmdopts["project"],
                        batch_leaf=leaf,
                        controller=c1,
                    )
                    opts2 = batchroot.from_exp(
                        sierra_root=self.cmdopts["sierra_root"],
                        project=self.cmdopts["project"],
                        batch_leaf=leaf,
                        controller=c2,
                    )
                    collate_root1 = opts1.stat_collate_root
                    collate_root2 = opts2.stat_collate_root

                    if leaf.scenario in str(collate_root1) and leaf.scenario not in str(
                        collate_root2
                    ):
                        self.logger.warning(
                            "%s does not exist in %s", leaf.scenario, collate_root2
                        )
                    if leaf.scenario in str(collate_root2) and leaf.scenario not in str(
                        collate_root1
                    ):
                        self.logger.warning(
                            "%s does not exist in %s", leaf.scenario, collate_root1
                        )


__all__ = ["PipelineStage5"]
