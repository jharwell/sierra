# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""
Builtin batch criteria which can be used with any :term:`Engine`/:term:`Project`.

"""
# Core packages
import typing as tp
import re
import pathlib

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


def _parse(arg: str) -> types.CLIArgSpec:
    ret = {
        "cardinality": None,
    }  # type: tp.Dict[str, tp.Optional[int]]

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
    ret["cardinality"] = int(res.group(0)[1:])

    return ret


def factory(
    cli_arg: str,
    main_config: types.YAMLDict,
    cmdopts: types.Cmdopts,
    batch_input_root: pathlib.Path,
    **kwargs,
) -> MonteCarlo:
    """Create a :class:`MonteCarlo` derived class from the cmdline definition."""
    config = _parse(cli_arg)

    def __init__(self) -> None:
        MonteCarlo.__init__(
            self, cli_arg, main_config, batch_input_root, config["cardinality"]
        )

    return type(cli_arg, (MonteCarlo,), {"__init__": __init__})  # type: ignore


__all__ = [
    "MonteCarlo",
]
