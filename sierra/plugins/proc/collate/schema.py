#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""strictyaml schemas for ``collate.yaml``.

``collate.yaml`` is a flat list of collation *targets*, each of which is one of
two spellings:

- single-source: a ``file`` naming one output, plus the ``cols`` to lift from
  it. The common case.

- multi-source: a ``name`` plus a list of ``sources``, each naming a ``file``
  and its ``cols``, whose (renamed) columns are joined per run. Used when a
  collated output must draw columns from more than one file.

These schemas validate the *shape* of one target: which keys are present, their
types, and (via strictyaml's default strictness) that no unknown keys appear.
They deliberately do **not** express:

- The file-vs-sources discriminator (exactly one spelling per entry). That is a
  cross-key constraint strictyaml cannot state; the validator dispatches on key
  presence instead.

- Cross-source column collisions, duplicate columns within a source, or empty
  source lists. Those are whole-target semantic invariants, checked after
  shape validation in :mod:`sierra.plugins.proc.collate.cconfig`.

Collation is intra-experiment only (it lifts per-run raw data within an
experiment so that e.g. models can compute from the raw distribution rather than
the summary statistics), so -- unlike ``graphs.yaml`` -- there is no inter-exp
section and the file is a bare list rather than a section mapping. If
inter-experiment collation is ever added, a discriminating top-level key will
need reintroducing, which would be a breaking config change; the flat shape is a
deliberate bet that it never will be.
"""
# Core packages

# 3rd party packages
import strictyaml

# Project packages
from sierra.core.yaml import sources

#: One column entry within a source's ``cols`` list. Re-exported from
#: :mod:`sierra.core.yaml.sources` (shared with intra-experiment graph configs).
col_entry = sources.col_entry

#: One source file within a multi-source target. Shared shape.
source = sources.source

#: Single-source target: one file, its columns, and an optional explicit output
#: name (which defaults to the file stem in the validator).
single_source = strictyaml.Map(
    {
        "file": strictyaml.Str(),
        strictyaml.Optional("name"): strictyaml.Str(),
        "cols": strictyaml.Seq(col_entry),
    }
)

#: Multi-source target: an explicit output name plus the sources to join.
multi_source = strictyaml.Map(
    {
        "name": strictyaml.Str(),
        "sources": strictyaml.Seq(source),
    }
)


__all__ = ["col_entry", "multi_source", "single_source", "source"]
