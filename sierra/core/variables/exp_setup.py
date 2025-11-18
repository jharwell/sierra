# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Reusable classes for configuring general aspects of experiments.

Aspects include experiment length, controller frequency, etc.

"""
# Core packages
import re

# 3rd party packages

# Project packages
from sierra.core import types


def parse(arg: str, dflts: types.SimpleDict) -> types.CLIArgSpec:
    """Enforces the cmdline definition of ``--exp-setup``.

    See :ref:`usage/vars/expsetup` for documentation.

    """
    ret = dflts

    regex = r"T(\d+)(?:\.K(\d+))?"

    sections = arg.split(".")
    # remove variable name, leaving only the spec
    sections = sections[1:]

    # Get pretty name for logging
    ret["pretty_name"] = ".".join(sections)
    res = re.match(regex, ret["pretty_name"])

    assert (
        res is not None and len(res.groups()) >= 1 and len(res.groups()) <= 3
    ), f"Spec must match {regex}, have {arg}"

    ret["n_secs_per_run"] = int(res.group(1))

    # Parse # ticks per second for controllers, which can be absent
    if res.group(2) is not None:
        ret["n_ticks_per_sec"] = int(res.group(2))

    return ret


__all__ = ["parse"]
