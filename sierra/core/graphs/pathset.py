#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
from dataclasses import dataclass
import pathlib
import typing as tp

# 3rd party packages

# Project packages


@dataclass
class PathSet:
    """The set of paths relevant/needed when creating graphs."""

    input_root: pathlib.Path
    output_root: pathlib.Path
    batchroot: pathlib.Path
    model_root: tp.Optional[pathlib.Path]


__all__ = ["PathSet"]
