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


def for_output(leaf: batchroot.ExpRootLeaf,
               new_stem: str,
               indices: tp.Union[tp.List[int], None]) -> str:
    """
    Create a new name given an existing leaf and a new component.

    "Name" here is in pathlib terminology.
    """
    name = new_stem + "-" + leaf.to_path().name

    if indices is not None:
        name += '_' + ''.join([str(i) for i in indices])

    return name
