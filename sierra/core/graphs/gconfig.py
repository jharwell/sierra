#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Loading and validation of the ``graphs.yaml`` :term:`Project` config.

Validation happens *once*, here, as the config is loaded -- rather than
per-graph inside each consumer. This means:

- A malformed graph definition is reported before *any* graph is written to
  disk, instead of after everything preceding it in the file has already been
  generated. All problems in the file are reported together.

- Every consumer gets the same validation. Consumers which previously
  hand-rolled key checks (or did none at all) no longer diverge.

- Defaults declared in the schemas are materialized exactly once, so consumers
  can index keys directly rather than re-supplying defaults at each call site.

Which sections exist, what shape they have, and which graph types are legal in
each is determined by :mod:`sierra.core.graphs.sections` -- plugins register
the sections they own. Nothing here knows about any specific plugin.
"""

# Core packages
import typing as tp
import logging

# 3rd party packages
import yaml
import strictyaml

# Project packages
from sierra.core import types, config
from sierra.core.graphs import sections
import sierra.core.plugin as pm

_logger = logging.getLogger(__name__)


class ConfigError(RuntimeError):
    """Raised when ``graphs.yaml`` does not conform to the graph schemas.

    Carries every problem found rather than just the first, so a project with
    several bad graph definitions can be fixed in one pass.
    """

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__(
            "{} problem(s) in graphs YAML config:\n  - {}".format(
                len(problems), "\n  - ".join(problems)
            )
        )


def load(cmdopts: types.Cmdopts) -> types.YAMLDict:
    """Load ``graphs.yaml`` and validate every graph it defines.

    Returns the config with schema defaults materialized, in the same shape as
    on disk: categorized sections stay ``{category: [graph, ...]}`` and flat
    sections stay ``[graph, ...]``.

    Raises:
        ConfigError: if any graph definition does not conform to the schema for
                     its ``type``. All problems are reported together.
    """
    loader = pm.module_load_tiered(project=cmdopts["project"], path="pipeline.yaml")
    raw = loader.load_config(cmdopts, config.PROJECT_YAML.graphs)

    return validate(raw)


def validate(raw: types.YAMLDict) -> types.YAMLDict:
    """Validate an already-loaded ``graphs.yaml`` mapping.

    Split out from :func:`load` so it can be exercised directly by tests
    without needing the plugin-loading machinery.
    """
    validated = {}  # type: types.YAMLDict
    problems = []  # type: list[str]
    count = 0

    known = sections.registered()

    for name in raw:
        section = known.get(name)

        if section is None:
            if sections.is_known(name):
                # Owner plugin is not loaded this invocation (e.g. a stage 4
                # run does not load the stage 5 comparison plugin). Nothing
                # will read the section, so leave it alone rather than
                # failing an otherwise-valid config.
                _logger.debug(
                    "Skipping section '%s': owning plugin %s not loaded",
                    name,
                    sections.KNOWN[name],
                )
                continue

            problems.append(
                "unknown top-level section '{}': expected one of {}".format(
                    name, sorted(sections.KNOWN)
                )
            )
            continue

        result: tp.Union[dict[str, list[types.YAMLDict]], list[types.YAMLDict]]
        if section.shape is sections.Shape.CATEGORIZED:
            result, n = _validate_categorized(raw[name], section, problems)
        else:
            result, n = _validate_flat(raw[name], section, problems)

        # The concrete section types (a category->list mapping or a bare list
        # of graph dicts) are both valid YAMLDict *values*, but dict invariance
        # prevents mypy from widening them into the recursive YAMLDict union.
        validated[name] = result  # type: ignore[assignment]
        count += n

    if problems:
        raise ConfigError(problems)

    _logger.debug(
        "Validated %d graph definition(s) across %d section(s) in graphs YAML config",
        count,
        len(validated),
    )

    return validated


def _validate_categorized(
    raw: tp.Any, section: sections.Section, problems: list[str]
) -> tuple[dict[str, list[types.YAMLDict]], int]:
    """Validate a ``{category: [graph, ...]}`` section."""
    validated = {}  # type: dict[str, list[types.YAMLDict]]
    count = 0

    if not isinstance(raw, dict):
        problems.append(
            "{}: expected a mapping of categories (section owned by {}), got {}".format(
                section.name, section.owner, type(raw).__name__
            )
        )
        return validated, count

    for category, graphs in raw.items():
        if not isinstance(graphs, list):
            problems.append(
                "{}/{}: expected a list of graphs, got {}".format(
                    section.name, category, type(graphs).__name__
                )
            )
            continue

        entries: list[types.YAMLDict] = []
        validated[category] = entries

        for i, graph in enumerate(graphs):
            where = "{}/{}[{}]".format(section.name, category, i)
            loaded = _validate_one(graph, where, section, problems)

            if loaded is not None:
                entries.append(loaded)
                count += 1

    return validated, count


def _validate_flat(
    raw: tp.Any, section: sections.Section, problems: list[str]
) -> tuple[list[types.YAMLDict], int]:
    """Validate a ``[graph, ...]`` section."""
    validated = []  # type: list[types.YAMLDict]
    count = 0

    if not isinstance(raw, list):
        problems.append(
            "{}: expected a list of graphs (section owned by {}), got {}".format(
                section.name, section.owner, type(raw).__name__
            )
        )
        return validated, count

    for i, graph in enumerate(raw):
        where = "{}[{}]".format(section.name, i)
        loaded = _validate_one(graph, where, section, problems)

        if loaded is not None:
            validated.append(loaded)
            count += 1

    return validated, count


def _validate_one(
    graph: tp.Any,
    where: str,
    section: sections.Section,
    problems: list[str],
) -> tp.Optional[types.YAMLDict]:
    """Validate a single graph definition against the schema for its type.

    The schema is selected from the *section's* type table rather than a global
    one, so a section can accept only a subset of the graph types which exist.

    Appends to `problems` and returns ``None`` on failure, so that validation
    continues and the caller can report everything at once.
    """
    if not isinstance(graph, dict):
        problems.append(
            "{}: expected a mapping, got {}".format(where, type(graph).__name__)
        )
        return None

    if "type" not in graph:
        problems.append(
            "{}: missing required key 'type' (expected one of {})".format(
                where, sorted(section.by_type)
            )
        )
        return None

    gtype = graph["type"]

    if gtype not in section.by_type:
        problems.append(
            "{}: graph type '{}' is not supported in this section "
            "(expected one of {})".format(where, gtype, sorted(section.by_type))
        )
        return None

    try:
        return strictyaml.load(yaml.dump(graph), section.by_type[gtype]).data
    except strictyaml.YAMLError as e:
        problems.append("{}: non-conformant {} config: {}".format(where, gtype, e))
        return None


def section(cfg: types.YAMLDict, name: str) -> tp.Optional[tp.Any]:
    """Fetch one section of validated config, warning if it is absent.

    Returns ``None`` if the section is missing, which every caller treats as
    "nothing to do" rather than an error -- a project may legitimately define
    only some of the sections.
    """
    if name not in cfg:
        _logger.warning(
            "Cannot generate graphs: '%s' key not found in graphs YAML config", name
        )
        return None

    return cfg[name]


__all__ = ["ConfigError", "load", "section", "validate"]
