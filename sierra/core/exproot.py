#
# Copyright 2024 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""
Container module for functionality for managing paths used by SIERRA.
"""

# Core packages
import typing as tp

# 3rd party packages

# Project packages
from sierra.core import batchroot


class PathSet:
    """
    The set of filesystem paths under the per-experiment root that SIERRA uses.

    Collected here in the interest of DRY.
    """

    def __init__(self,
                 batch: batchroot.PathSet,
                 exp_name: str,
                 exp0_name: tp.Optional[str] = None) -> None:
        self.input_root = batch.input_root / exp_name
        self.output_root = batch.output_root / exp_name
        self.graph_root = batch.graph_root / exp_name
        self.model_root = batch.model_root / exp_name
        self.stat_root = batch.stat_root / exp_name
        self.parent = batch.root

        if exp0_name:
            self.exp0_output_root = batch.output_root / exp0_name
            self.exp0_stat_root = batch.stat_root / exp0_name


__all__ = [
    "PathSet"
]
