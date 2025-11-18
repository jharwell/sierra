# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

"""Classes for the ``--exp-setup`` cmdline option.

See :ref:`usage/vars/expsetup` for usage documentation.

"""

# Core packages
import typing as tp

# 3rd party packages
import implements

# Project packages
from sierra.core.variables.base_variable import IBaseVariable
from sierra.core.experiment import definition
from sierra.core import config
from sierra.core.variables import exp_setup


@implements.implements(IBaseVariable)
class ExpSetup:
    """
    Defines the simulation duration.

    """

    def __init__(self, n_secs_per_run: int, n_ticks_per_sec: int) -> None:
        self.n_secs_per_run = n_secs_per_run
        self.n_ticks_per_sec = n_ticks_per_sec
        self.attr_changes = []  # type: tp.List[definition.AttrChangeSet]

    def gen_attr_changelist(self) -> list[definition.AttrChangeSet]:
        if not self.attr_changes:
            chgs = definition.AttrChangeSet(
                definition.AttrChange(
                    ".//experiment", "length", "{}".format(self.n_secs_per_run)
                ),
                definition.AttrChange(
                    ".//experiment",
                    "ticks_per_second",
                    "{}".format(self.n_ticks_per_sec),
                ),
            )
            self.attr_changes = [chgs]
        return self.attr_changes

    def gen_tag_rmlist(self) -> list[definition.ElementRmList]:
        return []

    def gen_element_addlist(self) -> list[definition.ElementAddList]:
        return []

    def gen_files(self) -> None:
        pass


def factory(arg: str) -> ExpSetup:
    """Create an :class:`ExpSetup` derived class from the command line definition.

    Arguments:

       arg: The value of ``--exp-setup``.

    """
    attr = exp_setup.parse(
        arg,
        {
            "n_secs_per_run": config.ARGOS["n_secs_per_run"],
            "n_ticks_per_sec": config.ARGOS["n_ticks_per_sec"],
        },
    )

    return ExpSetup(attr["n_secs_per_run"], attr["n_ticks_per_sec"])


__all__ = [
    "ExpSetup",
]
