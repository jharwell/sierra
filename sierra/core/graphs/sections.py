#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Registry of the top-level sections of ``graphs.yaml``.

``graphs.yaml`` is a *shared* config file: several plugins each own one or more
top-level sections of it. Rather than any one plugin hardcoding the full set
(which would require it to import the others, and to be updated whenever a new
plugin appears), each plugin declares the sections it owns by calling
:func:`register` at import time.

:mod:`sierra.core.graphs.gconfig` then validates the whole file by consulting
this registry, so:

- No plugin needs to know about any other plugin's sections.

- A section whose owning plugin is not installed is skipped rather than
  rejected: running stage 4 must not require the stage 5 plugin.

- A section which no plugin owns is a config *error*, rather than being
  silently accepted and then never read.

Registration is idempotent so that repeated imports (which Python caches, but
which can happen across test runs in one process) do not raise.
"""

# Core packages
import typing as tp
import enum
import logging

# 3rd party packages

# Project packages

_logger = logging.getLogger(__name__)


class Shape(enum.Enum):
    """The structural shape of a section's contents.

    Sections differ in whether their graphs are grouped into named categories
    (which the controller YAML can then enable/disable individually) or are a
    single flat list.
    """

    #: ``{category: [graph, ...]}`` -- e.g. ``intra-exp``, ``inter-exp``.
    CATEGORIZED = "categorized"

    #: ``[graph, ...]`` -- e.g. ``inter-controller``, ``imagize``.
    FLAT = "flat"


class Section(tp.NamedTuple):
    """One top-level section of ``graphs.yaml``, and how to validate it.

    Attributes:
        name: The key in ``graphs.yaml``, e.g. ``intra-exp``.

        shape: Whether the section's graphs are categorized or a flat list.

        by_type: Maps the value of a graph's ``type`` key to the schema which
                 validates it. This is *per-section*, which serves two
                 purposes: a section can accept only a subset of the graph
                 types which exist (``imagize`` supports only heatmaps and
                 networks), and two sections can legitimately use the same
                 schema object for the same type (``imagize`` reuses the
                 ``heatmap``/``network`` schemas verbatim).

        owner: Dotted name of the owning plugin, used in diagnostics so a
               config error names the plugin responsible for the section.
    """

    name: str
    shape: Shape
    by_type: dict[str, tp.Any]
    owner: str


#: Every section name SIERRA ships a plugin for, and the plugin which owns it.
#:
#: This is deliberately separate from :data:`_REGISTRY`, which only contains
#: sections whose owning plugin has actually been *imported*. Which plugins get
#: imported depends on the pipeline stages being run: a stage 4 invocation does
#: not load the stage 5 comparison plugin. Without this declaration, a perfectly
#: valid ``graphs.yaml`` containing an ``inter-controller`` section would be
#: rejected as "unknown" whenever stage 5 was not part of the run.
#:
#: So: a name in here but not in the registry is *skipped* (its owner is not
#: loaded, so nothing will read it); a name in neither is a genuine error.
KNOWN = {
    "intra-exp": "prod.graphs",
    "inter-exp": "prod.graphs",
    "inter-controller": "compare.graphs",
    "inter-scenario": "compare.graphs",
    "imagize": "proc.imagize",
}

_REGISTRY = {}  # type: dict[str, Section]


def register(section: Section) -> None:
    """Declare that a plugin owns a top-level section of ``graphs.yaml``.

    Raises:
        RuntimeError: if a *different* plugin has already claimed this section
                      name. Two plugins silently sharing a section would mean
                      whichever imported last decided how it is validated.
    """
    existing = _REGISTRY.get(section.name)

    if existing is not None:
        if existing == section:
            # Idempotent: re-registering the identical section is a no-op.
            return

        raise RuntimeError(
            "Section '{}' is already registered by {}; {} cannot also claim it".format(
                section.name, existing.owner, section.owner
            )
        )

    _REGISTRY[section.name] = section
    _logger.debug("Registered graphs.yaml section '%s' (%s)", section.name, section.owner)


def registered() -> dict[str, Section]:
    """Return all currently-registered sections, keyed by name.

    Which sections are present depends on which plugins have been imported, so
    callers should treat an absent section as "that plugin is not loaded"
    rather than "that section is invalid".
    """
    return dict(_REGISTRY)


def get(name: str) -> tp.Optional[Section]:
    """Look up one section by name, or ``None`` if its owner is not loaded."""
    return _REGISTRY.get(name)


def is_known(name: str) -> bool:
    """Whether `name` is a section SIERRA ships a plugin for.

    True even if that plugin is not loaded in this invocation; use
    :func:`get` to find out whether it can actually be validated.
    """
    return name in KNOWN


def reset() -> None:
    """Drop all registrations. For tests only."""
    _REGISTRY.clear()


__all__ = [
    "KNOWN",
    "Section",
    "Shape",
    "get",
    "is_known",
    "register",
    "registered",
    "reset",
]
