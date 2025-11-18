#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""Utility module for calculating path names."""

# Core packages
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import batchroot


def for_cc(
    leaf: batchroot.ExpRootLeaf, new_stem: str, indices: tp.Union[list[int], None]
) -> str:
    """
    Calculate a name suitable for CSVs/graphs in stage 5 to ensure uniqueness.

    "Name" here is in pathlib terminology. Targets controller comparisons. Since
    controller name is part of the default batchroot path, AND each batchroot
    path is unique, this case is easy.
    """
    name = "{}-{}".format(new_stem, leaf.to_path().name)

    if indices is not None:
        name += "_" + "".join([str(i) for i in indices])

    return name


def for_sc(
    leaf: batchroot.ExpRootLeaf,
    scenarios: list[str],
    new_stem: str,
    indices: tp.Union[list[int], None],
) -> str:
    """
    Calculate a name suitable for CSVs/graphs in stage 5 to ensure uniqueness.

    "Name" here is in pathlib terminology. Targets scenario comparisons, so we
    need a list of all scenarios in the path to eliminate path collisions in all
    cases.
    """
    name = "{}-{}+{}".format(new_stem, "+".join(scenarios), leaf.to_path())

    if indices is not None:
        name += "_" + "".join([str(i) for i in indices])

    return name
