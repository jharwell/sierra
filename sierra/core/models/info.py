# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Abstract info about models."""

# Core packages
import dataclasses
import typing as tp

# 3rd party packages
import holoviews as hv

# Project packages


@dataclasses.dataclass
class ModelInfo:
    dataset: hv.Dataset = None
    legend: list[str] = dataclasses.field(default_factory=lambda: [])
