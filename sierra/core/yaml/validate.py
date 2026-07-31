#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Shared machinery for validating loaded YAML config against strictyaml schemas.

This module holds the parts of config validation that are not specific to any
one config file: the aggregating error type, and the per-entry "check one
mapping against a schema" step. Consumers build their file-shape-specific walks
on top of these, so that every config file reports *all* of its problems at once
rather than failing on the first.

Kept separate from :mod:`sierra.core.pipeline.yaml` (which *loads* config off
disk and participates in the project-override tiered-loading contract) so that
loading a config does not drag in strictyaml. Importing this module is the
opt-in that pulls in the validation dependency.

"""

# Core packages
import typing as tp

# 3rd party packages
import yaml
import strictyaml

# Project packages


class ConfigError(RuntimeError):
    """Raised when a YAML config does not conform to its schemas.

    Carries every problem found rather than just the first, so a file with
    several faults can be fixed in one pass.
    """

    def __init__(self, problems: list[str], what: str = "YAML config") -> None:
        self.problems = problems
        self.what = what
        super().__init__(
            "{} problem(s) in {}:\n  - {}".format(
                len(problems), what, "\n  - ".join(problems)
            )
        )

    def __reduce__(self):
        # multiprocessing pickles a worker's exception and re-raises it in the
        # parent. The default reconstruction calls type(self)(*self.args), and
        # self.args is the single formatted message string -- which would be
        # passed as `problems`, then join()'d character-by-character.
        #
        # Reconstruct via a rebuild helper that bypasses __init__ and restores
        # state directly, so this works regardless of a subclass's constructor
        # signature (e.g. the graphs ConfigError takes only `problems`).
        return (
            _rebuild_config_error,
            (self.__class__, self.problems, self.what, self.args),
        )


def _rebuild_config_error(cls, problems, what, args):
    """Reconstruct a (possibly subclassed) :class:`ConfigError` on unpickle.

    Bypasses ``__init__`` (whose signature varies across subclasses) and sets
    the state the class contract guarantees: ``problems``, ``what``, and the
    base ``Exception`` args (which carry the formatted message).
    """
    err = cls.__new__(cls)
    err.problems = problems
    err.what = what
    # Restore the formatted message so str(err) is unchanged after a round-trip.
    Exception.__init__(err, *args)
    return err


def validate_entry(
    entry: tp.Any,
    schema: tp.Any,
    where: str,
    problems: list[str],
) -> tp.Optional[dict]:
    """Validate one mapping against a strictyaml ``schema``.

    Returns the validated mapping (with schema defaults materialized) on
    success, or ``None`` on failure -- in which case a description is appended
    to ``problems`` and validation is expected to continue, so the caller can
    report every fault together.

    ``where`` is a human-readable locator (e.g. ``"intra-exp/cat[2]"`` or
    ``"collate[3]"``) used only in problem messages.

    The entry is round-tripped through ``yaml.dump`` and ``strictyaml.load`` so
    that a plain Python mapping (as produced by the ordinary YAML loader) can be
    checked against a strictyaml schema.
    """
    if not isinstance(entry, dict):
        problems.append(
            "{}: expected a mapping, got {}".format(where, type(entry).__name__)
        )
        return None

    try:
        return strictyaml.load(yaml.dump(entry), schema).data
    except strictyaml.YAMLError as e:
        problems.append("{}: non-conformant config: {}".format(where, e))
        return None


__all__ = ["ConfigError", "validate_entry"]
