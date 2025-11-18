# Copyright 2018 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#
"""
Functionality for mapping arena size -> swarm size to maintain a constant ratio.
"""
# Core packages
import re
import typing as tp
import pathlib

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.core.utils import ArenaExtent
from sierra.plugins.engine.argos.variables.arena_shape import ArenaShape
from sierra.core import types


class ConstantDensity(bc.UnivarBatchCriteria):
    """Defines common functionality for all constant-density classes.

    Constant density = SOMETHING/arena size is held constant as arena size is
    increased. This class is a base class which should NEVER be used on its own.

    Attributes:
        target_density: The target density.

        dimensions: List of (X,Y) dimensions to use (creates rectangular
                    arenas).

        scenario_tag: A scenario tag (presumably part of `--scenario`) to use to
                      generate scenario names.

        changes: List of sets of changes to apply to generate the specified
                 arena sizes.

    """

    def __init__(
        self,
        cli_arg: str,
        main_config: types.YAMLDict,
        batch_input_root: pathlib.Path,
        target_density: float,
        dimensions: list[ArenaExtent],
        scenario_tag: str,
    ) -> None:
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_input_root)
        self.target_density = target_density
        self.dimensions = dimensions
        self.scenario_tag = scenario_tag
        self.attr_changes = ArenaShape(dimensions).gen_attr_changelist()

    def computable_exp_scenario_name(self) -> bool:
        return True

    def exp_scenario_name(self, exp_num: int) -> str:
        """Given the exp number in the batch, compute a parsable scenario name.

        It is necessary to query this criteria after generating the changelist
        in order to create generator classes for each experiment in the batch
        with the correct name and definition in some cases.

        Normally controller+scenario are used to look up all necessary changes
        for the specified arena size, but for this criteria the specified
        scenario is the base scenario (i.e., the starting arena dimensions), and
        the correct arena dimensions for a given exp must be found via lookup
        with THIS function).

        """
        dims = self.dimensions[exp_num]
        return (
            self.scenario_tag
            + "."
            + "x".join([str(dims.xsize()), str(dims.ysize()), str(dims.zsize())])
        )


def parse(arg: str) -> types.CLIArgSpec:
    """Enforces specification of a :class:`ConstantDensity` derived batch criteria.

    Returns:
       Dict:
             target_density: Floating point value of parsed target density
             arena_size_inc: Integer increment for arena size
    """
    ret = {}

    sections = arg.split(".")
    # remove variable name, leaving only the spec
    spec = ".".join(sections[1:])

    regex = r"(\d+)p(\d+)\.I(\d+)\.C(\d+)"
    res = re.match(regex, spec)

    assert len(res.groups()) == 4, f"Spec must match {regex}, have {spec}"

    # groups(0) is always the full matched string; subsequent groups are the
    # captured groups from the () expressions.
    characteristic = float(res.group(1))
    mantissa = float("0." + res.group(2))
    ret["target_density"] = characteristic + mantissa
    ret["arena_size_inc"] = int(res.group(3))
    ret["cardinality"] = int(res.group(4))

    return ret


__all__ = ["ConstantDensity", "parse"]
