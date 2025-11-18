#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""
Base class functionality for comparing products/deliverables in stage 5.
"""
# Core packages
import typing as tp
import logging
import pathlib
import argparse

# 3rd party packages
import strictyaml
import yaml

# Project packages
from sierra.core import types, batchroot
from sierra.plugins.compare.graphs import outputroot, schema


class BaseComparator:
    """Compares a set of SOMETHING within SOME context.

    Graph generation
    is controlled via a config file parsed in
    :class:`~sierra.core.pipeline.stage5.pipeline_stage5.PipelineStage5`.

    Attributes:
        things: List of names of things to compare.

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
        things: list[str],
        stage5_roots: outputroot.PathSet,
        cmdopts: types.Cmdopts,
        cli_args: argparse.Namespace,
        main_config: types.YAMLDict,
    ) -> None:
        self.things = things
        self.stage5_roots = stage5_roots

        self.cmdopts = cmdopts
        self.cli_args = cli_args
        self.main_config = main_config
        self.project_root = pathlib.Path(
            self.cmdopts["sierra_root"], self.cmdopts["project"]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.debug("csv_root=%s", str(self.stage5_roots.csv_root))
        self.logger.debug("graph_root=%s", str(self.stage5_roots.graph_root))

    def exp_select(self) -> list[batchroot.ExpRoot]:
        raise NotImplementedError

    def compare(
        self,
        cmdopts: types.Cmdopts,
        graph: types.YAMLDict,
        roots: list[batchroot.ExpRoot],
        legend: list[str],
    ) -> None:
        raise NotImplementedError

    def __call__(
        self,
        target_graphs: list[types.YAMLDict],
        legend: list[str],
    ) -> None:
        self._check_comparability()

        selected = self.exp_select()
        if not selected:
            self.logger.warning(
                "No matching batch experiments to compare %s in for criteria %s",
                self.things,
                self.cli_args.batch_criteria,
            )
            return

        self.logger.debug(
            "Comparing %s: selected=%s",
            self.things,
            [r.to_str() for r in selected],
        )

        # For each comparison graph we are interested in, generate it using data
        # from all matching batch roots
        for graph in target_graphs:
            try:
                if self.cmdopts["across"] == "controllers":
                    loaded = strictyaml.load(yaml.dump(graph), schema.cc).data
                elif self.cmdopts["across"] == "scenarios":
                    loaded = strictyaml.load(yaml.dump(graph), schema.sc).data
                elif self.cmdopts["across"] == "criterias":
                    raise NotImplementedError
            except strictyaml.YAMLError as e:
                self.logger.critical("Non-conformant comparison YAML: %s", e)
                raise

            self.compare(
                cmdopts=self.cmdopts, graph=loaded, roots=selected, legend=legend
            )

    def _check_comparability(self) -> None:
        """Check if the specified THINGS can be compared.

        Comparable THINGS have all been run on the same set of batch
        experiments, scenarios or controllers (depending on the specified
        comparison type).  If they have not, it is not *necessarily* an error,
        but probably should be looked at, so it is only a warning, not fatal.
        """
        if self.cmdopts["across"] == "controllers":
            self._check_comparability_cc()
        elif self.cmdopts["across"] == "scenarios":
            self._check_comparability_sc()

    def _check_comparability_cc(self) -> None:
        """
        Check that a set of controllers can be compared.

        To be comparable, controllers must have been run in the same scenario
        with the same batch criteria.
        """
        for c1 in self.things:
            # Check all scenario+batch criteria experiments which have used
            # this controller.
            for scenario in (self.project_root / c1).iterdir():
                for candidate in scenario.iterdir():
                    # Get the dirname of the batch experiment path
                    leaf1 = batchroot.ExpRootLeaf.from_name(candidate.name)
                    opts1 = batchroot.from_exp(
                        sierra_root=self.cmdopts["sierra_root"],
                        project=self.cmdopts["project"],
                        batch_leaf=leaf1,
                        controller=c1,
                        scenario=str(scenario),
                    )
                    interexp_root1 = opts1.stat_interexp_root

                    # Stage 5 only operates on stage4 collated data, so if that
                    # doesn't exist, we can't do anything.
                    if not interexp_root1.exists():
                        self.logger.debug(
                            "%s cannot be compared in/across for %s: %s does not exist",
                            scenario,
                            c1,
                            interexp_root1,
                        )
                        continue

                    for c2 in self.things:
                        self._check_comparability_cc_pairwise(c1, leaf1, c2)

    def _check_comparability_cc_pairwise(
        self, c1: str, leaf1: batchroot.ExpRootLeaf, c2: str
    ) -> None:
        """
        Check if two controllers can be compared.

        Given a candidate batch experiment for one of them, check that the other
        one executed the same batch experiment in the same scenario.
        """
        if c1 == c2:
            return

        for scenario2 in (self.project_root / c2).iterdir():
            for candidate2 in scenario2.iterdir():
                # Get the dirname of the batch experiment path
                leaf2 = batchroot.ExpRootLeaf.from_name(candidate2.name)

                opts2 = batchroot.from_exp(
                    sierra_root=self.cmdopts["sierra_root"],
                    project=self.cmdopts["project"],
                    batch_leaf=leaf2,
                    controller=c2,
                    scenario=str(scenario2),
                )
                interexp_root2 = opts2.stat_interexp_root

                if not interexp_root2.exists():
                    self.logger.debug(
                        "%s cannot be compared in/across for %s: %s does not exist",
                        scenario2,
                        c2,
                        interexp_root2,
                    )
                    return

                # Check that both controllers were run on the same set
                # of batch criteria
                if leaf1.bc != leaf2.bc:
                    self.logger.warning(
                        "Cannot compare %s with %s: bc mismatch (%s != %s)",
                        c1,
                        c2,
                        leaf1.bc,
                        leaf2.bc,
                    )

    def _check_comparability_sc(self) -> None:
        """
        Check that a set of scenarios can be compared.

        To be comparable, scenarios must have been run using the same controller
        with the same batch criteria.
        """
        controller = self.cmdopts["controller"]

        # Check all scenarios
        for s1 in self.things:
            # Check all batch criteria experiments which have used the specified
            # controller.
            for candidate in (self.project_root / controller / s1).iterdir():
                # Get the dirname of the batch experiment path
                leaf1 = batchroot.ExpRootLeaf.from_name(candidate.name)
                opts1 = batchroot.from_exp(
                    sierra_root=self.cmdopts["sierra_root"],
                    project=self.cmdopts["project"],
                    batch_leaf=leaf1,
                    controller=controller,
                    scenario=s1,
                )
                interexp_root1 = opts1.stat_interexp_root

                # Stage 5 only operates on stage4 collated data, so if that
                # doesn't exist, we can't do anything.
                if not interexp_root1.exists():
                    self.logger.debug(
                        "%s cannot be compared in/across for %s: %s does not exist",
                        controller,
                        s1,
                        interexp_root1,
                    )
                    continue

                for s2 in self.things:
                    self._check_comparability_sc_pairwise(s1, controller, leaf1, s2)

    def _check_comparability_sc_pairwise(
        self, s1: str, controller: str, leaf1: batchroot.ExpRootLeaf, s2: str
    ) -> None:
        """
        Check if two scenarios can be compared.

        Given a candidate batch experiment for one of them, check that the other
        one executed the same batch experiment using the same controller.
        """
        if s1 == s2:
            return

        for candidate2 in (self.project_root / controller / s2).iterdir():
            # Get the dirname of the batch experiment path
            leaf2 = batchroot.ExpRootLeaf.from_name(candidate2.name)

            opts2 = batchroot.from_exp(
                sierra_root=self.cmdopts["sierra_root"],
                project=self.cmdopts["project"],
                batch_leaf=leaf2,
                controller=controller,
                scenario=s2,
            )
            interexp_root2 = opts2.stat_interexp_root

            if not interexp_root2.exists():
                self.logger.debug(
                    "%s cannot be compared in/across for %s: %s does not exist",
                    candidate2,
                    s2,
                    interexp_root2,
                )
                return

            # Check that both controllers were run on the same set
            # of batch criteria
            if leaf1.bc != leaf2.bc:
                self.logger.warning(
                    "Cannot compare %s with %s: bc mismatch (%s != %s)",
                    s1,
                    s2,
                    leaf1.bc,
                    leaf2.bc,
                )


__all__ = ["BaseComparator"]
