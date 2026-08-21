#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Declarative description of stage-5 comparison outputs.

Stage 5 does not fit the per-experiment ``StageManifest`` model: its outputs are
not named ``c1-exp{i}`` but by the *pair* being compared, in roots like
``{a}+{b}-cc-csvs`` / ``-cc-graphs`` / ``-cc-models`` (inter-controller) or
``{a}+{b}-sc-*`` (inter-scenario). So comparisons get their own small spec here,
consumed by ``verify.verify_comparison``.

Adding a comparison (or a new engine's comparison) is a ``ComparisonSpec`` entry
here, not a new checker branch.
"""

# Core packages
import dataclasses
import typing as tp


@dataclasses.dataclass(frozen=True)
class ComparisonSpec:
    """One stage-5 comparison's expected outputs.

    A comparison collates a per-measure artifact across the ``things`` being
    compared (controllers for ``kind="cc"``, scenarios for ``kind="sc"``). Every
    collated CSV/model has one data column per compared thing, plus an index
    column. Row counts vary per measure because ``include_exp`` can filter the
    experiments a given measure draws from.
    """

    #: "cc" (inter-controller) or "sc" (inter-scenario). Selects the root-name
    #: infix and the error wording only; the checks are identical.
    kind: str

    #: The two things being compared, in the order SIERRA names the root
    #: (``{left}+{right}-{kind}-{artifact}``). Controllers for cc, scenarios for
    #: sc. ``len`` gives the expected data-column count (+1 for the index).
    things: tp.Tuple[str, ...]

    #: The project subdir under SIERRA_ROOT that holds the comparison roots.
    project: str = "projects.sample_argos"

    #: Expected number of files in the ``-{kind}-graphs`` root.
    n_graphs: tp.Optional[int] = None

    #: Maps a filename fragment (e.g. "cc-food-counts") onto the number of data
    #: rows that measure's collated CSV/model must have, reflecting its
    #: ``include_exp`` filtering. Fragments not listed are only shape-checked
    #: (column count), not row-checked.
    measure_rows: tp.Mapping[str, int] = dataclasses.field(default_factory=dict)

    # ---- model expectations -------------------------------------------------
    #: Maps a model filename fragment onto its expected data-row count. When set,
    #: the ``-{kind}-models`` root is checked: exactly len(model_rows) ``.model``
    #: files, each with a matching ``.legend`` and the right row/column shape.
    #: None skips the models root.
    model_rows: tp.Optional[tp.Mapping[str, int]] = None

    def root(self, artifact: str) -> str:
        """Relative path (under SIERRA_ROOT) of a comparison output root.

        ``artifact`` is one of ``csvs`` / ``graphs`` / ``models``.
        """
        pair = "+".join(self.things)
        return f"{self.project}/{pair}-{self.kind}-{artifact}"

    def n_things(self) -> int:
        return len(self.things)


# --- The lightweight (jsonsim) comparison registry -------------------------
# The comparison-root fragments follow the SIERRA naming
# ``{kind}-{measure}``, so e.g. ``cc-signal-summary-measured``.

_JS_PROJECT = "projects.sample_jsonsim"
JS_KALMAN = "signal.kalman"
_LOWPASS = "signal.lowpass"
_BANDPASS = "signal.bandpass"
_BANDSTOP = "signal.bandstop"
JS_CLEANROOM = "cleanroom"
JS_FIELDTEST = "fieldtest"

#: The two inter-exp measures stage 5 compares (bare inter-exp graph dests).
_JS_MEASURES = ["signal-summary"]

# --- run-confirmed numbers ---
_JS_MEASURE_ROWS_CC = {f"cc-{m}": 5 for m in _JS_MEASURES}
_JS_MEASURE_ROWS_SC = {f"sc-{m}": 5 for m in _JS_MEASURES}

#: Inter-controller univariate: signal.kalman vs signal.lowpass, one scenario.
JS_CC_UNIVAR = ComparisonSpec(
    kind="cc",
    things=(JS_KALMAN, _LOWPASS),
    project=_JS_PROJECT,
    n_graphs=len(_JS_MEASURES),
    measure_rows=_JS_MEASURE_ROWS_CC,
)

#: Inter-scenario univariate: one controller across cleanroom vs fieldtest.
JS_SC_UNIVAR = ComparisonSpec(
    kind="sc",
    things=(JS_CLEANROOM, JS_FIELDTEST),
    project=_JS_PROJECT,
    n_graphs=len(_JS_MEASURES),
    measure_rows=_JS_MEASURE_ROWS_SC,
)

#: Inter-controller model collation (needs the modelrunner in stages 1-4).
JS_CC_MODELS = ComparisonSpec(
    kind="cc",
    things=(JS_KALMAN, _LOWPASS),
    project=_JS_PROJECT,
    model_rows=_JS_MEASURE_ROWS_CC,
)

#: Inter-scenario model collation.
JS_SC_MODELS = ComparisonSpec(
    kind="sc",
    things=(JS_CLEANROOM, JS_FIELDTEST),
    project=_JS_PROJECT,
    model_rows=_JS_MEASURE_ROWS_SC,
)

#: Inter-controller BIVARIATE: only a graph-file count is asserted (one graph
#: per measure), mirroring the ARGoS bivar checker.
JS_CC_BIVAR = ComparisonSpec(
    kind="cc",
    things=(_BANDPASS, _BANDSTOP),
    project=_JS_PROJECT,
    n_graphs=len(_JS_MEASURES),
)
