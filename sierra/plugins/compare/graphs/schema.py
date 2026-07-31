#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""
YAML schemas for comparison graphs for stage 5.

See :ref:`plugins/compare/graphs` for more details.
"""
# Core packages

# 3rd party packages
import strictyaml

# Project packages
from sierra.core import types


comparison_line = strictyaml.Map(
    {
        "src": strictyaml.Str(),
        "dest": strictyaml.Str(),
        "type": strictyaml.Enum(["comparison_line"]),
        strictyaml.Optional("title", default=""): strictyaml.Str(),
        strictyaml.Optional("label", default=""): strictyaml.Str(),
        strictyaml.Optional("primary_axis", default=0): strictyaml.Int(),
        strictyaml.Optional("index", default=-1): strictyaml.Int(),
        # 2026-07-24 [JRH]: ':' (the whole range) rather than None. These are
        # equivalent -- sierra.core.utils.exp_include_filter() treats an empty
        # start/end as an open bound -- but a real value keeps this key
        # indexable like every other defaulted key, rather than forcing
        # consumers back to .get().
        strictyaml.Optional("include_exp", default=":"): strictyaml.Str(),
        strictyaml.Optional("backend"): strictyaml.Str(),
    }
)
"""
Schema for comparison graphs.

Used for both inter-controller and inter-scenario comparison; the two differ in
*what* is being compared, not in how a comparison graph is configured.

.. NOTE:: This is deliberately a distinct type from
          :data:`sierra.core.graphs.schema.summary_line`, which it was
          previously (and confusingly) named after. The two accept nearly
          disjoint key sets: a summary_line is one point per *experiment*
          within a batch, while a comparison_line is one line per
          *controller/scenario* across batches.
"""

#: Maps the value of the ``type`` key to the schema which validates that graph
#: type, for the sections owned by this plugin.
BY_TYPE = {
    "comparison_line": comparison_line,
}

#: Keys whose fallback is a *runtime* cmdline value rather than a constant, and
#: so cannot be expressed as a strictyaml default. Maps the YAML key to the
#: ``cmdopts`` key supplying its value when omitted.
#:
#: Keeping this here rather than inline at each call site means the schema
#: module remains the single place which knows how every key is defaulted --
#: whether that default is a constant or comes from the cmdline.
CMDLINE_DEFAULTS = {
    "backend": "graphs_backend",
}


def resolve(graph, cmdopts: types.Cmdopts):
    """Fill in any cmdline-derived keys omitted from a validated graph.

    Constant defaults are already materialized by strictyaml during validation;
    this handles the remainder, so that consumers can index every key directly
    rather than mixing ``graph["title"]`` with
    ``graph.get("backend", cmdopts[...])``.

    Arguments:
        graph: A validated graph definition.

        cmdopts: Dictionary of parsed cmdline attributes.

    Returns:
        A new dict; the input is not modified.
    """
    resolved = dict(graph)

    for key, cmdopt in CMDLINE_DEFAULTS.items():
        if key not in resolved:
            resolved[key] = cmdopts[cmdopt]

    return resolved


__all__ = ["BY_TYPE", "CMDLINE_DEFAULTS", "comparison_line", "resolve"]
