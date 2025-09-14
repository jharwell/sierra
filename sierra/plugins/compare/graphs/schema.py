#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#
"""
YAML schemas for comparison graphs for stage 5.

See :ref:`plugins/compare/graphs` for more details.
"""
# Core packages

# 3rd party packages
import strictyaml

# Project packages


cc = strictyaml.Map(
    {
        "src_stem": strictyaml.Str(),
        "dest_stem": strictyaml.Str(),
        strictyaml.Optional("title"): strictyaml.Str(),
        strictyaml.Optional("label"): strictyaml.Str(),
        strictyaml.Optional("primary_axis"): strictyaml.Int(),
        strictyaml.Optional("include_exp"): strictyaml.Str(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for controller comparison graphs.
"""

sc = cc
"""
Schema for scenario comparison graphs.
"""
