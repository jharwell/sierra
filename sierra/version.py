# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Provide access to the SIERRA version from the pyproject.toml in source code."""

# Core packages
import importlib.metadata

# 3rd party packages

# Project packages

try:
    __version__ = importlib.metadata.version("sierra-research")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0+unknown"
