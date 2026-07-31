#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Loading and validation of ``collate.yaml``.

Like :mod:`sierra.core.graphs.gconfig` for ``graphs.yaml``, validation happens
*once*, here, as the config is loaded -- not per-target inside the gatherer. A
malformed target is reported before any collation runs, and *every* problem in
the file is reported together rather than failing on the first.

Validation and normalization are a single pass: :func:`validate` returns the
list of :class:`CollateTarget` objects the gatherer consumes, with schema
defaults materialized and semantic invariants checked. The gatherer never sees
the raw dict form, so there is no validated-but-un-normalized intermediate to
keep in sync.

The per-target shape is checked against the strictyaml schemas in
:mod:`sierra.plugins.proc.collate.schema`; the cross-key and whole-target
invariants that strictyaml cannot express (the file-vs-sources discriminator,
duplicate columns within a source, cross-source column collisions) are checked
here.
"""

# Core packages
import typing as tp
import dataclasses
import pathlib

# 3rd party packages

# Project packages
from sierra.core.yaml import validate as yamlvalidate
from sierra.core.yaml import sources as srcspec
from sierra.plugins.proc.collate import schema


@dataclasses.dataclass(frozen=True)
class CollateSource:
    """One source file contributing columns to a collation target.

    Attributes:

        file: The configured output filename, matched exactly against run
              outputs (with or without the storage extension) by
              :func:`sierra.core.pipeline.stage3.gather.file_matches`. Not a
              substring match.

        col_map: Ordered ``(source_col, output_col)`` pairs selecting the
                 columns to lift and the names to expose them under. A bare
                 column string in config becomes ``(col, col)`` (no rename); the
                 ``{name, as}`` form becomes ``(name, as)`` and is how same-named
                 columns from different files are disambiguated.
    """

    file: str
    col_map: tuple[tuple[str, str], ...]

    @property
    def output_cols(self) -> list[str]:
        return [out for _, out in self.col_map]


@dataclasses.dataclass(frozen=True)
class CollateTarget:
    """A single collation output, assembled from one or more source files.

    Attributes:

        name: Output identity. For the single-source spelling it defaults to the
              file stem, preserving historical output filenames. For the
              multi-source spelling it is required (there is no single stem to
              derive from, and output identity must not depend on source order).

        sources: The source files contributing columns to this target. Length 1
                 is the common case and the single-source spelling.

        name_explicit: Whether ``name`` was set in config (vs defaulted to the
                       file stem). A single-source target with an explicit name
                       may not fan out over multiple matching files, since one
                       name cannot disambiguate several outputs.
    """

    name: str
    sources: tuple[CollateSource, ...]
    name_explicit: bool = False

    @property
    def is_single_source(self) -> bool:
        return len(self.sources) == 1


def validate(raw: tp.Any) -> list[CollateTarget]:
    """Validate a loaded ``collate.yaml`` and return its collation targets.

    ``raw`` is the object produced by the ordinary YAML loader: a flat list of
    target mappings (collation is intra-experiment only, so there is no section
    wrapper). ``None`` or an empty list -- a project with no collation config --
    yields no targets.

    Returns:
        The validated, normalized :class:`CollateTarget` list.

    Raises:
        ConfigError: if the file is malformed or any target is non-conformant.
                     All problems are reported together.
    """
    if raw is None:
        return []

    problems = []  # type: tp.List[str]

    if not isinstance(raw, list):
        raise yamlvalidate.ConfigError(
            [
                "expected a list of collation targets, got {}".format(
                    type(raw).__name__
                )
            ],
            what="collate.yaml",
        )

    targets = []  # type: tp.List[CollateTarget]
    for i, entry in enumerate(raw):
        where = "collate[{}]".format(i)
        target = _validate_target(entry, where, problems)
        if target is not None:
            targets.append(target)

    if problems:
        raise yamlvalidate.ConfigError(problems, what="collate.yaml")

    return targets


def _validate_target(
    entry: tp.Any, where: str, problems: list[str]
) -> tp.Optional[CollateTarget]:
    """Validate one target: discriminate spelling, check shape, then semantics.

    Appends to ``problems`` and returns ``None`` on any failure so that
    validation of the rest of the file continues.
    """
    if not isinstance(entry, dict):
        problems.append(
            "{}: expected a mapping, got {}".format(where, type(entry).__name__)
        )
        return None

    has_file = "file" in entry
    has_sources = "sources" in entry

    # The file-vs-sources discriminator: exactly one spelling. strictyaml cannot
    # express "exactly one of these keys", so it is checked here, before shape
    # validation (there is no single schema that fits an entry with both/neither).
    if has_file and has_sources:
        problems.append(
            "{}: has both 'file' (single-source) and 'sources' (multi-source); "
            "use exactly one".format(where)
        )
        return None
    if not has_file and not has_sources:
        problems.append(
            "{}: needs either 'file' (single-source) or 'sources' "
            "(multi-source)".format(where)
        )
        return None

    if has_file:
        return _validate_single(entry, where, problems)
    return _validate_multi(entry, where, problems)


def _validate_single(
    entry: dict, where: str, problems: list[str]
) -> tp.Optional[CollateTarget]:
    validated = yamlvalidate.validate_entry(
        entry, schema.single_source, where, problems
    )
    if validated is None:
        return None

    source = _build_source(validated, where, problems)
    if source is None:
        return None

    name_explicit = "name" in validated
    name = str(validated.get("name", pathlib.Path(source.file).stem))
    target = CollateTarget(
        name=name, sources=(source,), name_explicit=name_explicit
    )

    return _check_target_semantics(target, where, problems)


def _validate_multi(
    entry: dict, where: str, problems: list[str]
) -> tp.Optional[CollateTarget]:
    validated = yamlvalidate.validate_entry(
        entry, schema.multi_source, where, problems
    )
    if validated is None:
        return None

    raw_sources = validated["sources"]
    if not raw_sources:
        problems.append("{}: multi-source target has no sources".format(where))
        return None

    sources = []  # type: tp.List[CollateSource]
    ok = True
    for j, s in enumerate(raw_sources):
        built = _build_source(s, "{}/sources[{}]".format(where, j), problems)
        if built is None:
            ok = False
        else:
            sources.append(built)
    if not ok:
        return None

    target = CollateTarget(
        name=str(validated["name"]),
        sources=tuple(sources),
        name_explicit=True,
    )

    return _check_target_semantics(target, where, problems)


def _build_source(
    validated: dict, where: str, problems: list[str]
) -> tp.Optional[CollateSource]:
    """Turn a shape-validated source mapping into a :class:`CollateSource`.

    Delegates shape-independent normalization (the ``{name, as}`` handling and
    the duplicate-column-within-one-file check) to the shared source spec, then
    wraps the result in the collate-specific dataclass.
    """
    result = srcspec.normalize_source(validated, where, problems)
    if result is None:
        return None

    file, col_map = result
    return CollateSource(file=file, col_map=col_map)


def _check_target_semantics(
    target: CollateTarget, where: str, problems: list[str]
) -> tp.Optional[CollateTarget]:
    """Check the whole-target invariant: no unresolved cross-source collision.

    A post-rename output column contributed by more than one source that the
    researcher has not disambiguated via ``as`` is rejected. Returns the target
    unchanged on success, or ``None`` (having appended) on collision.
    """
    pairs = [(s.file, s.col_map) for s in target.sources]
    ok = srcspec.check_collisions(
        pairs, where, "target '{}'".format(target.name), problems
    )
    return target if ok else None


__all__ = ["CollateSource", "CollateTarget", "validate"]
