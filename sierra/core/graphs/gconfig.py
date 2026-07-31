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

# Project packages
from sierra.core import types, config
from sierra.core.graphs import sections
from sierra.core.yaml import validate as yamlvalidate
from sierra.core.yaml import sources as srcspec
import sierra.core.plugin as pm

_logger = logging.getLogger(__name__)


class ConfigError(yamlvalidate.ConfigError):
    """Raised when ``graphs.yaml`` does not conform to the graph schemas.

    A thin specialization of the shared :class:`sierra.core.yaml.validate.
    ConfigError` that fixes the ``what`` to name the graphs config, so existing
    ``except gconfig.ConfigError`` sites keep working and messages stay specific.
    Carries every problem found rather than just the first.
    """

    def __init__(self, problems: list[str]) -> None:
        super().__init__(problems, what="graphs YAML config")


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

    # Graph-type dispatch is graphs-specific; the per-entry strictyaml check
    # itself is the shared harness.
    loaded = yamlvalidate.validate_entry(graph, section.by_type[gtype], where, problems)
    if loaded is None:
        return None

    # Cross-key invariants the schema cannot express: the src-vs-sources
    # discriminator (multi-file input). Checked here so a bad graph is reported
    # up front with everything else.
    if not _check_input_spelling(loaded, where, section, problems):
        return None

    return loaded


#: For graph types that reference input columns by a *named role* (rather than a
#: ``cols`` list), maps each role key to its schema default. Used to verify, for
#: a multi-source graph, that every role resolves to a column the sources
#: actually produce. Types keyed off ``cols`` (stacked_line, histogram) are
#: absent here -- their columns are named inside the sources themselves.
#:
#: Defaults MUST match the corresponding schema defaults in
#: :mod:`sierra.core.graphs.schema`.
_ROLE_COLUMNS = {
    "heatmap": {"x": "x", "y": "y", "z": "z"},
    "confusion_matrix": {"truth_col": "truth", "predicted_col": "predicted"},
}

#: Graph types whose schema historically *required* ``cols``. That requiredness
#: moved from the schema into the validator when ``cols`` was relaxed to Optional
#: to accommodate the ``sources`` spelling; it is re-enforced for the ``src``
#: spelling here. (stacked_line is absent: its ``cols`` is genuinely optional for
#: intra-exp, and its inter-exp requirement is enforced in the collate path.)
_COLS_REQUIRED_WITH_STEM = {"histogram"}


def _check_input_spelling(
    graph: dict, where: str, section: "sections.Section", problems: list[str]
) -> bool:
    """Validate the ``src`` vs ``sources`` input discriminator.

    A graph names its input either with a single ``src`` (the common case)
    or with a ``sources`` list drawing columns from several files, joined per
    experiment -- exactly one, never both, never neither. ``sources`` is
    intra-experiment only: inter-experiment collation consumes single,
    already-joined stage-3 files (see the collate plugin), so multi-file input is
    rejected there.

    Graph types which do not support ``sources`` at all (their schema has no such
    key) always require ``src``; this still enforces its presence for them.
    Appends to ``problems`` and returns ``False`` on any violation.
    """
    has_stem = "src" in graph
    has_sources = "sources" in graph

    if has_stem and has_sources:
        problems.append(
            "{}: has both 'src' and 'sources'; use exactly one".format(where)
        )
        return False

    if not has_stem and not has_sources:
        problems.append("{}: needs either 'src' or 'sources'".format(where))
        return False

    if has_stem:
        # 'cols' was required by these types' schemas before it was relaxed to
        # Optional to accommodate the 'sources' spelling (where columns come from
        # inside each source instead). Re-enforce it here for the src
        # spelling so a single-source graph of these types still requires 'cols'.
        # (stacked_line's inter-exp 'cols' requirement is enforced separately in
        # the collate path, so it is intentionally not duplicated here.)
        if graph["type"] in _COLS_REQUIRED_WITH_STEM and "cols" not in graph:
            problems.append(
                "{}: '{}' graphs require 'cols' when using 'src'".format(
                    where, graph["type"]
                )
            )
            return False

        return True

    if has_sources:
        return _check_input_spelling_multi_source(graph, where, section, problems)

    return True


def _check_input_spelling_multi_source(
    graph: dict, where: str, section: "sections.Section", problems: list[str]
) -> bool:
    """Validate the ``sources`` input discriminator."""
    # sources is intra-experiment only.
    if section.name != "intra-exp":
        problems.append(
            "{}: 'sources' (multi-file input) is only supported for "
            "intra-experiment graphs; inter-experiment graphs consume "
            "single already-joined files, so use 'src'".format(where)
        )
        return False

    # No src to derive the output name from, so dest is required.
    if "dest" not in graph:
        problems.append(
            "{}: a multi-source graph needs an explicit 'dest' "
            "(there is no 'src' to derive the output name from)".format(where)
        )
        return False

    # 'cols' comes from inside each source; a top-level 'cols' alongside
    # 'sources' is contradictory.
    if "cols" in graph:
        problems.append(
            "{}: 'cols' cannot be combined with 'sources' (each source "
            "names its own cols)".format(where)
        )
        return False

    # Per-source dup-column and cross-source collision checks, shared with
    # collate.
    normalized = []  # type: list[tuple[str, srcspec.ColMap]]
    for j, s in enumerate(graph["sources"]):
        result = srcspec.normalize_source(
            s, "{}/sources[{}]".format(where, j), problems
        )
        if result is None:
            return False
        normalized.append(result)

    if not srcspec.check_collisions(normalized, where, "graph input", problems):
        return False

    # For types that reference columns by named role (heatmap's x/y/z,
    # confusion_matrix's truth_col/predicted_col), those roles must resolve
    # to output columns the joined sources actually produce -- otherwise the
    # plot would fail at read time. Checked here so it fails up front.
    produced = {out for _, col_map in normalized for _, out in col_map}
    for key, default in _ROLE_COLUMNS.get(graph["type"], {}).items():
        wanted = graph.get(key, default)
        if wanted not in produced:
            problems.append(
                "{}: '{}' column '{}' is not produced by any source "
                "(sources produce {})".format(where, key, wanted, sorted(produced))
            )
            return False

    return True


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
