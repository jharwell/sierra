# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Reusable classes related to the homogeneous populations of agents.
"""
# Core packages
import typing as tp
import re
import math
import pathlib

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core.variables import batch_criteria as bc
from sierra.core.graphs import bcbridge


class PopulationSize(bc.UnivarBatchCriteria):
    """
    Base class for changing the # agents/robots to reduce code duplication.
    """

    def __init__(self, *args, **kwargs) -> None:
        bc.UnivarBatchCriteria.__init__(self, *args, *kwargs)

    def graph_xticks(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: pathlib.Path,
        exp_names: list[str],
    ) -> list[float]:

        ret = list(map(float, self.populations(cmdopts, exp_names)))

        if cmdopts["plot_log_xscale"]:
            return [int(math.log2(x)) for x in ret]

        if cmdopts["plot_enumerated_xscale"]:
            return list(range(0, len(ret)))

        return ret

    def graph_xticklabels(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: pathlib.Path,
        exp_names: list[str],
    ) -> list[str]:

        if exp_names is None:
            exp_names = self.gen_exp_names()

        ret = map(float, self.populations(cmdopts, exp_names))

        return [str(int(round(x, 4))) for x in ret]

    def graph_xlabel(self, cmdopts: types.Cmdopts) -> str:
        if cmdopts["plot_log_xscale"]:
            return r"$\log$(System Size)"

        return "System Size"

    def graph_info(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: tp.Optional[pathlib.Path] = None,
        exp_names: tp.Optional[list[str]] = None,
    ) -> bcbridge.GraphInfo:
        """Return graph info for base classes to use if they wish."""
        info = bcbridge.GraphInfo(
            cmdopts,
            batch_output_root,
            exp_names if exp_names else self.gen_exp_names(),
        )

        info.xlabel = self.graph_xlabel(info.cmdopts)
        info.xticklabels = self.graph_xticklabels(
            info.cmdopts, info.batch_output_root, info.exp_names
        )
        info.xticks = self.graph_xticks(
            info.cmdopts, info.batch_output_root, info.exp_names
        )
        return info


def parse(arg: str) -> list[int]:
    """Generate the system sizes for each experiment in a batch."""
    spec = {
        "max_size": 0,
        "model": "",
        "cardinality": None,
    }  # type: tp.Dict[str, tp.Union[str, tp.Optional[int]]]

    sections = arg.split(".")

    # remove batch criteria variable name, leaving only the spec
    sections = sections[1:]
    assert len(sections) >= 1 and len(sections) <= 2, (
        "Spec must have 1 or 2 sections separated by '.'; "
        f"have {len(sections)} from '{arg}'"
    )

    # Parse increment type
    res = re.search("Log|Linear", sections[0])
    assert (
        res is not None
    ), f"Bad size increment spec in criteria section '{sections[0]}'"
    spec["model"] = res.group(0)

    # Parse max size
    res = re.search("[0-9]+", sections[0])
    assert res is not None, "Bad population max in criteria section '{sections[0]}'"
    max_size = int(res.group(0))
    spec["max_size"] = max_size

    # Parse cardinality for linear models
    if spec["model"] == "Linear":
        if len(sections) == 2:
            res = re.search("C[0-9]+", sections[1])
            assert (
                res is not None
            ), "Bad cardinality in criteria section '{sections[1]}'"
            spec["cardinality"] = int(res.group(0)[1:])
        else:
            spec["cardinality"] = int(spec["max_size"] / 10.0)
    elif spec["model"] == "Log":
        spec["cardinality"] = len(range(0, int(math.log2(max_size)) + 1))

    if spec["model"] == "Linear":
        increment = int(spec["max_size"] / spec["cardinality"])
        return [increment * x for x in range(1, spec["cardinality"] + 1)]

    if spec["model"] == "Log":
        return [int(2**x) for x in range(0, spec["cardinality"])]

    raise ValueError("Bad value for model: {}".format(spec["model"]))


__all__ = [
    "PopulationSize",
    "parse",
]
