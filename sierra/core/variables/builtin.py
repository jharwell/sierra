# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Builtin batch criteria which can be used with any :term:`Engine`/:term:`Project`.

Batch criteria in this file are the ONLY ones which come with SIERRA which can
be used as-is. Other stuff in ``sierra.core.variables`` are base classes which
require specialization to use as batch criteria, or are just experimental
variables.
"""
# Core packages
import typing as tp
import re
import pathlib
import numpy as np

# 3rd party packages

# Project packages
from sierra.core import types
from sierra.core.experiment import definition
from sierra.core.variables import batch_criteria as bc


class MonteCarlo(bc.UnivarBatchCriteria):
    """
    Criteria which does nothing put provide a set of experiments via cardinality.

    Useful in debugging/when all you care about varying is the random seed. Used
    as::

       builtin.MonteCarlo.C<X>

    where <X> is the # of experiments you want in the :term:`Batch Experiment`.

    """

    def __init__(
        self,
        cli_arg: str,
        main_config: types.YAMLDict,
        batch_input_root: pathlib.Path,
        cardinality: int,
    ) -> None:
        bc.UnivarBatchCriteria.__init__(self, cli_arg, main_config, batch_input_root)
        self.attr_changes = []  # type: tp.List[definition.AttrChangeSet]
        self.cardinality = cardinality

    def gen_attr_changelist(self) -> tp.List[definition.AttrChangeSet]:
        if not self.attr_changes:
            self.attr_changes = [
                definition.AttrChangeSet(definition.NullMod())
                for i in range(0, self.cardinality)
            ]

        return self.attr_changes

    def gen_exp_names(self) -> tp.List[str]:
        changes = self.gen_attr_changelist()
        return ["exp" + str(x) for x in range(0, len(changes))]

    def n_agents(self, exp_num: int) -> int:
        return self.size_list[exp_num]

    def graph_xticks(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: pathlib.Path,
        exp_names: tp.Optional[tp.List[str]] = None,
    ) -> tp.List[float]:

        if exp_names is None:
            exp_names = self.gen_exp_names()

        return list(range(0, len(exp_names)))

    def graph_xticklabels(
        self,
        cmdopts: types.Cmdopts,
        batch_output_root: pathlib.Path,
        exp_names: tp.Optional[tp.List[str]] = None,
    ) -> tp.List[str]:

        if exp_names is None:
            exp_names = self.gen_exp_names()

        return exp_names

    def graph_xlabel(self, cmdopts: types.Cmdopts) -> str:
        return "Experiment"


def _mc_parse(arg: str) -> int:
    sections = arg.split(".")

    # This is the one builtin batch criteria which exists for now
    assert (
        sections[1] == "MonteCarlo"
    ), f" Only 'MonteCarlo' builtin defined; have {sections[1]}"

    # remove batch criteria variable name, leaving only the spec
    sections = sections[1:]
    assert (
        len(sections) == 2
    ), f"Spec must have 2 sections separated by '.'; have {len(sections)} from '{arg}'"

    res = re.search("C[0-9]+", sections[1])
    assert res is not None, "Bad cardinality in criteria section '{sections[1]}'"
    return int(res.group(0)[1:])


def linspace_parse(arg: str, scale_factor: tp.Optional[float] = 1.0) -> tp.List[float]:
    """
    Generate an array from a linspace spec of the form ``<min>.<max>.C<cardinality>``.

    Args:
        arg: The CLI string.

        scale_factor: A linear factor applied to the min/max to shift the
                      range. This can be used to, e.g., generate ranges like
                      0.4-0.8 from specs like ``4.8.C8`` instead of having to do
                      contortions around parsing decimal values out of CLI
                      strings directly.
    """
    regex = r"(\d+)\.(\d+)\s*\.C\s*(\d+)\s*"
    res = re.match(regex, arg)
    assert len(res.groups()) == 3, f"Spec must match {regex}, have {arg}"

    # groups(0) is always the full matched string; subsequent groups are the
    # captured groups from the () expressions.
    _min = float(res.group(1)) * scale_factor
    _max = float(res.group(2)) * scale_factor
    cardinality = int(res.group(3))
    return [x for x in np.linspace(_min, _max, cardinality)]


def factory(
    cli_arg: str,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    **kwargs,
) -> MonteCarlo:
    """Create a :class:`MonteCarlo` derived class from the cmdline definition."""
    cardinality = _mc_parse(cli_arg)

    def __init__(self) -> None:
        MonteCarlo.__init__(self, cli_arg, main_config, batch_input_root, cardinality)

    return type(cli_arg, (MonteCarlo,), {"__init__": __init__})  # type: ignore


__all__ = ["MonteCarlo", "linspace_parse"]
