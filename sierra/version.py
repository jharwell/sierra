# Copyright 2021 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT
"""Provide access to the SIERRA version from the pyproject.toml in source code."""

# Core packages
import importlib.metadata

# 3rd party packages

# Project packages

__version__ = importlib.metadata.version("sierra_research")
