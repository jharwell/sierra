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
import sierra.core.root_dirpath_generator as rdg


def from_controller(batch_root: pathlib.Path,
                    graph_stem: str,
                    controllers: tp.List[str],
                    controller: str) -> str:
    _, batch_leaf, _ = rdg.parse_batch_leaf(str(batch_root))
    leaf = graph_stem + "-" + batch_leaf + \
        '_' + str(controllers.index(controller))
    return leaf


def from_batch_root(batch_root: pathlib.Path,
                    graph_stem: str,
                    index: tp.Union[int, None]):
    _, scenario, _ = rdg.parse_batch_leaf(str(batch_root))
    leaf = graph_stem + "-" + scenario

    if index is not None:
        leaf += '_' + str(index)

    return leaf


def from_batch_leaf(batch_leaf: str,
                    graph_stem: str,
                    indices: tp.Union[tp.List[int], None]):
    leaf = graph_stem + "-" + batch_leaf

    if indices is not None:
        leaf += '_' + ''.join([str(i) for i in indices])

    return leaf
