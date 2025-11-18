# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
#

# Core packages
import re
import typing as tp
import pathlib

# 3rd party packages
import numpy as np

# Project packages
from sierra.core.variables.batch_criteria import UnivarBatchCriteria
from sierra.core.utils import ArenaExtent
from sierra.core import types
from sierra.core.experiment import definition


class VariableDensity(UnivarBatchCriteria):
    """A univariate range for variable density (# THINGS/m^2).

    # THINGS is varied as arena size is held constant. This class is a base
    class which should NEVER be used on its own.

    """

    def __init__(
        self,
        cli_arg: str,
        main_config: types.YAMLDict,
        batch_input_root: pathlib.Path,
        densities: list[float],
        extent: ArenaExtent,
    ) -> None:
        UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_input_root)
        self.densities = densities
        self.extent = extent
        self.attr_changes = []  # type: tp.List[definition.AttrChangeSet]


def parse(arg: str) -> list[float]:
    """Enforces specification of a :class:`VariableDensity` derived batch criteria."""
    spec = {}  # type: tp.Dict[str, tp.Union[float, int]]
    sections = arg.split(".")

    # remove batch criteria variable name, leaving only the spec
    sections = sections[1:]
    assert len(sections) == 3, (
        "Spec must have 3 sections separated by '.'; "
        f"have {len(sections)} from '{arg}'"
    )

    # Parse density min
    spec["min"] = _parse_density(sections[0], "minimum")

    # Parse density pmax
    spec["max"] = _parse_density(sections[1], "maximum")

    # Parse cardinality
    res = re.search("C[0-9]+", sections[2])
    assert res is not None, "Bad cardinality specification in '{sections[2]}'"

    spec["cardinality"] = int(res.group(0)[1:])

    return list(np.linspace(spec["min"], spec["max"], num=spec["cardinality"]))


def _parse_density(chunk: str, which: str) -> float:
    res = re.search("[0-9]+", chunk)
    assert (
        res is not None
    ), f"Bad {which} density characteristic specification in '{chunk}'"

    characteristic = float(res.group(0))

    res = re.search("p[0-9]+", chunk)
    assert res is not None, f"Bad {which} density mantissa specification in '{chunk}'"

    mantissa = float("0." + res.group(0)[1:])

    return characteristic + mantissa


__all__ = ["VariableDensity", "parse"]
