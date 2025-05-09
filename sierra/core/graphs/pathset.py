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
    input_root: pathlib.Path
    output_root: pathlib.Path
    parent: pathlib.Path
    model_root: tp.Optional[pathlib.Path]
