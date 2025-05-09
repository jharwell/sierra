# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Container module for things related to models."""

# Core packages
import dataclasses
import typing as tp

# 3rd party packages
import holoviews as hv

# Project packages
from . import interface as interface


@dataclasses.dataclass
class ModelInfo:
    dataset: hv.Dataset = None
    legend: tp.List[str] = dataclasses.field(default_factory=lambda: [])
