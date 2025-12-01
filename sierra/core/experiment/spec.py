# Copyright 2020 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Contains experiment specification bits in the interest of DRY.
"""

# Core packages
import typing as tp
import logging
import pathlib

# 3rd party packages

# Project packages
import sierra.core.variables.batch_criteria as bc
from sierra.core.utils import ArenaExtent
from sierra.core.vector import Vector3D
import sierra.core.plugin as pm
from sierra.core import types, config
from sierra.core.experiment import definition


class SimpleBatchScaffoldSpec:
    def __init__(self, criteria: bc.XVarBatchCriteria, log: bool = False) -> None:
        self.criteria = criteria
        self.chgs = criteria.gen_attr_changelist()
        self.adds = criteria.gen_element_addlist()
        self.rms = criteria.gen_tag_rmlist()
        self.logger = logging.getLogger(__name__)
        self.n_exps = 0

        self.mods = []
        self.is_compound = False

        if (
            (self.chgs and self.adds)
            or (self.chgs and self.rms)
            or (self.adds and self.rms)
        ):
            raise RuntimeError("This spec can't be used with compound scaffolding")

        if self.chgs:
            self.mods = self.chgs
            self.n_exps = len(self.chgs)
            if log:
                self.logger.info(
                    (
                        "Executing scaffold: cli=%s: modify %s "
                        "expdef elements per experiment"
                    ),
                    self.criteria.name,
                    len(self.chgs[0]),
                )
        elif self.adds:
            self.mods = self.adds
            self.n_exps = len(self.adds)
            if log:
                self.logger.info(
                    (
                        "Executing scaffold: cli=%s: Add %s expdef "
                        "elements per experiment"
                    ),
                    self.criteria.name,
                    len(self.adds[0]),
                )
        elif self.rms:
            self.mods = self.rms
            self.n_exps = len(self.rms)
            if log:
                self.logger.info(
                    (
                        "Executing scaffold: cli=%s: Remove %s expdef "
                        "elements per experiment"
                    ),
                    self.criteria.name,
                    len(self.rms[0]),
                )

    def __iter__(
        self,
    ) -> tp.Iterator[
        tp.Union[
            definition.AttrChangeSet,
            definition.ElementAddList,
            definition.ElementRmList,
        ]
    ]:
        return iter(self.mods)

    def __len__(self) -> int:
        return self.n_exps


class CompoundBatchScaffoldSpec:
    def __init__(self, criteria: bc.XVarBatchCriteria, log: bool = False) -> None:
        self.criteria = criteria
        self.chgs = criteria.gen_attr_changelist()
        self.adds = criteria.gen_element_addlist()
        self.rms = criteria.gen_tag_rmlist()
        self.logger = logging.getLogger(__name__)

        self.n_exps = 0

        self.is_compound = True
        self.mods = (
            []
        )  # type: tp.List[tp.Union[tuple[definition.ElementAddList,definition.AttrChangeSet],tuple[definition.ElementRmList,definition.AttrChangeSet],tuple[definition.ElementRmList,definition.ElementAddList]]]

        if self.chgs and self.adds:
            self._handle_case1(log)
        elif self.chgs and self.rms:
            self._handle_case2(log)
        elif self.adds and self.rms:
            self._handle_case3(log)
        else:
            raise RuntimeError("This spec can only be used with compound scaffolding")

    def __len__(self) -> int:
        return self.n_exps

    def _handle_case1(self, log: bool) -> None:
        for addlist in self.adds:
            for chgset in self.chgs:
                t = addlist, chgset
                self.mods.append(t)
                self.n_exps += 1

        if log:
            self.logger.info(
                (
                    "Executing scaffold: cli=%s: Add  "
                    "%s expdef elements AND modify %s expdef  "
                    "elements per experiment"
                ),
                self.criteria.name,
                len(self.adds[0]),
                len(self.chgs[0]),
            )

    def _handle_case2(self, log: bool) -> None:
        for rmlist in self.rms:
            for chgset in self.chgs:
                t = rmlist, chgset
                self.mods.append(t)
                self.n_exps += 1

        if log:
            self.logger.info(
                (
                    "Executing scaffold: cli=%s: Remove  "
                    "%s expdef elements AND modify %s expdef  "
                    "elements per experiment"
                ),
                self.criteria.name,
                len(self.rms[0]),
                len(self.chgs[0]),
            )

    def _handle_case3(self, log: bool) -> None:
        for rmlist in self.rms:
            for addlist in self.adds:
                t = rmlist, addlist
                self.mods.append(t)
                self.n_exps += 1

        if log:
            self.logger.info(
                (
                    "Executing scaffold: cli=%s: Remove  "
                    "%s expdef elements AND add %s expdef  "
                    "elements per experiment"
                ),
                self.criteria.name,
                len(self.rms[0]),
                len(self.adds[0]),
            )


class ExperimentSpec:
    """
    The specification for a single experiment with a batch.

    In the interest of DRY, this class collects the following common components:

    - Experiment # within the batch.

    - Root input directory for all :term:`Experimental Run` input files
      comprising the :term:`Experiment`.

    - Pickle file path for the experiment.

    - Arena dimensions for the experiment (if any).

    - Full scenario name.
    """

    def __init__(
        self,
        criteria: bc.XVarBatchCriteria,
        batch_input_root: pathlib.Path,
        exp_num: int,
        cmdopts: types.Cmdopts,
    ) -> None:
        self.exp_num = exp_num
        exp_name = criteria.gen_exp_names()[exp_num]

        self.exp_input_root = batch_input_root / exp_name
        self.exp_def_fpath = self.exp_input_root / config.PICKLE_LEAF

        self.logger = logging.getLogger(__name__)
        self.criteria = criteria

        # Need to get per-experiment arena dimensions from batch criteria, as
        # they might be different for each experiment
        if self.criteria.computable_exp_scenario_name():
            self.arena_dim = self.criteria.arena_dims(cmdopts)[exp_num]
            self.scenario_name = self.criteria.exp_scenario_name(exp_num)
            self.logger.debug(
                "Read scenario dimensions '%s' from batch criteria",
                self.arena_dim,
            )
        else:  # Maybe read scenario dimensions read from cmdline
            module = pm.module_load_tiered(
                project=cmdopts["project"], path="generators.scenario"
            )
            kw = module.to_dict(cmdopts["scenario"])
            if all(k in kw for k in ["arena_x", "arena_y", "arena_z"]):
                self.arena_dim = ArenaExtent(
                    Vector3D(kw["arena_x"], kw["arena_y"], kw["arena_z"])
                )
                self.logger.debug(
                    "Read scenario dimensions %s from cmdline spec", self.arena_dim
                )
            else:
                self.arena_dim = None

            self.scenario_name = cmdopts["scenario"]


def scaffold_spec_factory(
    criteria: bc.XVarBatchCriteria, **kwargs
) -> tp.Union[SimpleBatchScaffoldSpec, CompoundBatchScaffoldSpec]:
    chgs = criteria.gen_attr_changelist()
    adds = criteria.gen_element_addlist()

    if chgs and adds:
        logging.debug(
            "Create compound batch experiment scaffolding spec for '%s'",
            criteria.name,
        )
        return CompoundBatchScaffoldSpec(criteria, **kwargs)

    logging.debug(
        "Create simple batch experiment scaffolding spec for '%s'", criteria.name
    )
    return SimpleBatchScaffoldSpec(criteria, **kwargs)


__all__ = ["ExperimentSpec"]
