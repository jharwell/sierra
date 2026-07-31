#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Shared spec for pulling columns from one or more source files.

Several YAML config surfaces need the same idea: name some files, name the
columns to lift from each (optionally renaming them), and join those columns
together on a shared row axis. ``collate.yaml`` uses it to build collated
outputs; intra-experiment graph configs use it to plot columns drawn from more
than one file.

Rather than each of those re-implementing the shape, the ``{name, as}`` column
form, and the semantic checks (a column selected twice within one file; two
sources exposing the same output column name), this module owns them once. It
provides:

- the strictyaml *shapes* (:data:`col_entry`, :data:`source`), which validate
  which keys are present and their types, and

- the *normalization* (:func:`normalize_source`) and *collision* checks
  (:func:`check_collisions`) that strictyaml cannot express, operating on plain
  ``(file, col_map)`` tuples so each consumer can wrap them in whatever target
  type it likes.

Everything here appends to a shared ``problems`` list rather than raising, so a
consumer can validate a whole file and report every fault together.
"""
# Core packages
import typing as tp

# 3rd party packages
import strictyaml

# Project packages


#: A ``(source_col, output_col)`` pair: the column to read, and the name to
#: expose it under after any renaming.
ColMap = tuple[tuple[str, str], ...]


#: One column entry within a source's ``cols`` list.
#:
#: A bare string selects a column and keeps its name. The ``{name, as}`` mapping
#: selects ``name`` and exposes it as ``as`` (defaulting to ``name`` when ``as``
#: is omitted) -- the mechanism for disambiguating same-named columns pulled
#: from different files.
col_entry = strictyaml.Str() | strictyaml.Map(
    {
        "name": strictyaml.Str(),
        strictyaml.Optional("as"): strictyaml.Str(),
    }
)

#: One source file: a ``file`` and the ``cols`` to lift from it.
source = strictyaml.Map(
    {
        "file": strictyaml.Str(),
        "cols": strictyaml.Seq(col_entry),
    }
)


def normalize_col(entry: tp.Union[str, dict]) -> tuple[str, str]:
    """Normalize one shape-validated column entry to ``(source_col, output_col)``.

    The entry has already passed the :data:`col_entry` schema, so it is either a
    string or a mapping with a required ``name`` and optional ``as``.
    """
    if isinstance(entry, str):
        return (entry, entry)

    src = str(entry["name"])
    out = str(entry.get("as", src))
    return (src, out)


def normalize_source(
    validated: dict, where: str, problems: list[str]
) -> tp.Optional[tuple[str, ColMap]]:
    """Turn a shape-validated source mapping into a ``(file, col_map)`` pair.

    Checks the one per-source semantic invariant strictyaml cannot: a column
    selected more than once within a single source (distinct from a cross-source
    collision, which is resolved via ``as``). Appends to ``problems`` and returns
    ``None`` on failure so validation can continue.
    """
    col_map = tuple(normalize_col(c) for c in validated["cols"])

    src_cols = [s for s, _ in col_map]
    if len(set(src_cols)) != len(src_cols):
        dupes = sorted({c for c in src_cols if src_cols.count(c) > 1})
        problems.append(
            "{}: duplicate source column(s) within one file: {}".format(
                where, dupes
            )
        )
        return None

    return (str(validated["file"]), col_map)


def check_collisions(
    sources: tp.Sequence[tuple[str, ColMap]],
    where: str,
    what: str,
    problems: list[str],
) -> bool:
    """Check that no output column name is produced by more than one source.

    ``sources`` is a sequence of ``(file, col_map)`` pairs (as returned by
    :func:`normalize_source`). A post-rename output column contributed by more
    than one source that the user has not disambiguated via ``as`` is a
    collision. ``what`` names the thing being checked (e.g. the target or graph
    name) for the diagnostic. Appends to ``problems`` and returns ``False`` on
    any collision, ``True`` if clean.
    """
    seen = {}  # type: tp.Dict[str, str]
    ok = True
    for file, col_map in sources:
        for _, out in col_map:
            if out in seen:
                problems.append(
                    "{}: unresolved column collision in {}: output column "
                    "'{}' is produced by both '{}' and '{}'; disambiguate "
                    "with 'as'".format(where, what, out, seen[out], file)
                )
                ok = False
            else:
                seen[out] = file

    return ok


__all__ = [
    "ColMap",
    "check_collisions",
    "col_entry",
    "normalize_col",
    "normalize_source",
    "source",
]
