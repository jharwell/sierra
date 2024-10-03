#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import typing as tp

# 3rd party packages

# Project packages


def from_batch_leaf(batch_leaf: str,
                    graph_stem: str,
                    indices: tp.Union[tp.List[int], None]):
    leaf = graph_stem + "-" + batch_leaf

    if indices is not None:
        leaf += '_' + ''.join([str(i) for i in indices])

    return leaf
