#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""One generic checker, three tiers of scrutiny.

There is no ``if engine == ...`` here: the checker is driven entirely by the
``EngineSpec`` manifests. Adding an engine adds zero lines to this file.

The tiers exist because they fail for different reasons at different costs:

* presence  — did the pipeline wire up and run? (free; every engine, every PR)
* shape     — did it produce well-formed output? (cheap; where declared)
* value     — did it compute the right numbers? (expensive; reference engines)

Coarser tiers run first so the *first* failure points at the real fault: a run
that produced nothing fails presence cleanly, instead of a value check dying in
a confusing ``FileNotFoundError``.
"""

# Core packages
import csv
import pathlib
import typing as tp
import logging
import os

# 3rd party packages
import polars as pl
from polars.testing import assert_frame_equal

# Project packages
from tests._framework.engines import EngineSpec, ExpectedOutput, StageManifest
from tests._framework.comparisons import ComparisonSpec
from sierra.core import config

_logger = logging.getLogger("tests.verify")

if level := os.environ.get("SIERRA_TEST_LOGGING", ""):
    _logger.setLevel(level)


def _log_check(tier: str, rel, detail: str) -> None:
    _logger.debug("[%-8s] %s %s", tier, str(rel), detail)


# SIERRA's default center/spread when the user passes neither on the command
# line. Kept here as the one place the defaults are named; the actual on-disk
# extensions still come from config.STATS, never from these strings directly.
DEFAULT_CENTER = "mean"
DEFAULT_SPREAD = "none"


def _stat_exts(center: tp.Optional[str], spread: tp.Optional[str]) -> tp.List[str]:
    """The on-disk statistics-file extensions for a center/spread pair.

    ALWAYS sourced from ``sierra.core.config.STATS`` -- never from the literal
    ``--center``/``--spread`` names. This matters because the file suffix a
    measure produces is not necessarily its option name (e.g. a spread of
    ``conf95`` may emit ``.stddev``), and SIERRA's config is the authority on
    that mapping. Any manifest path containing ``{stat}`` is expanded over the
    returned extensions.

    ``center``/``spread`` here are *lookup keys* into ``config.STATS``, not
    suffixes. When omitted, SIERRA's defaults are used.
    """
    c = center if center is not None else DEFAULT_CENTER
    s = spread if spread is not None else DEFAULT_SPREAD
    return list(config.STATS[c].spreads[s].exts)


def _expand(
    entry: ExpectedOutput,
    i: int,
    n_runs: int,
    stats: tp.Sequence[str],
    j: tp.Optional[int] = None,
) -> tp.List[str]:
    """Expand ``{i}``/``{j}``/``{run}``/``{stat}`` in a manifest path.

    ``{j}`` is the second experiment index for bivariate batch criteria, whose
    experiments are named ``c1-exp{i}+c2-exp{j}``. Univariate manifests never
    contain ``{j}`` and pass ``j=None``.
    """
    templates = [entry.path]
    if "{stat}" in entry.path:
        templates = [entry.path.replace("{stat}", s) for s in stats]

    fmt = dict(i=i)
    if j is not None:
        fmt["j"] = j

    out = []
    for tmpl in templates:
        if "{run}" in tmpl:
            out.extend(tmpl.format(run=r, **fmt) for r in range(n_runs))
        else:
            out.append(tmpl.format(**fmt))
    return out


def check_presence(batch_root: pathlib.Path, entry: ExpectedOutput, rel: str) -> None:
    """Tier 1. Asserts a directory when ``entry.is_dir``, else a file."""
    path = batch_root / rel
    if entry.is_dir:
        _log_check("presence", path.relative_to(batch_root), "dir exists")
        assert path.is_dir(), f"[presence] missing dir: {path}"
    else:
        _log_check("presence", path.relative_to(batch_root), "file exists")
        assert path.is_file(), f"[presence] missing: {path}"


def check_shape(batch_root: pathlib.Path, entry: ExpectedOutput, rel: str) -> None:
    """Tier 2 — only touches files, no goldens. Cheap and low-churn."""
    path = batch_root / rel

    if entry.forbidden_content:
        text = path.read_text()
        for bad in entry.forbidden_content:
            _log_check("shape", path.relative_to(batch_root), "forbiden content")
            assert bad not in text, f"[shape] {path} contains forbidden {bad!r}"

    if (
        entry.min_rows is None
        and entry.columns is None
        and entry.n_cols is None
        and entry.columns_contain is None
    ):
        return

    df = pl.read_csv(path)
    if entry.min_rows is not None:
        _log_check("shape", path.relative_to(batch_root), "# rows")
        assert (
            df.height >= entry.min_rows
        ), f"[shape] {path}: {df.height} rows < min {entry.min_rows}"
    if entry.columns is not None:
        _log_check("shape", path.relative_to(batch_root), "column names")
        assert (
            tuple(df.columns) == entry.columns
        ), f"[shape] {path}: columns {tuple(df.columns)} != {entry.columns}"
    if entry.n_cols is not None:
        _log_check("shape", path.relative_to(batch_root), "# columns")
        assert (
            len(df.columns) == entry.n_cols
        ), f"[shape] {path}: {len(df.columns)} columns != expected {entry.n_cols}"
    if entry.columns_contain is not None:
        have = set(df.columns)
        missing = [c for c in entry.columns_contain if c not in have]
        _log_check("shape", path.relative_to(batch_root), "column list contains")
        assert not missing, (
            f"[shape] {path}: missing required columns {missing} "
            f"(have {tuple(df.columns)})"
        )


def check_value(
    batch_root: pathlib.Path,
    goldens_root: pathlib.Path,
    entry: ExpectedOutput,
    rel: str,
) -> None:
    """Tier 3 — full golden comparison. Expensive; only where ``value_check``.

    The golden lives at the SAME relative path under ``goldens_root`` as the
    produced file does under ``batch_root``, so the expanded ``rel`` (with
    ``{i}``/``{stat}`` already substituted) indexes both. ``check_column_order``
    is relaxed because collation column order is not part of the contract.
    """
    if not entry.value_check:
        return
    got = pl.read_csv(batch_root / rel)
    want = pl.read_csv(goldens_root / rel)
    assert_frame_equal(got, want, check_dtypes=False, check_column_order=False)


def _verify_entries(
    entries: tp.Sequence[ExpectedOutput],
    batch_root: pathlib.Path,
    goldens_root: tp.Optional[pathlib.Path],
    idxs: tp.Iterable[int],
    n_runs: int,
    stats: tp.Sequence[str],
    max_tier: int,
) -> None:
    for entry in entries:
        for i in idxs:
            for rel in _expand(entry, i, n_runs, stats):
                check_presence(batch_root, entry, rel)  # tier 1 always
                if entry.is_dir:
                    # A directory has no rows/columns/goldens to check.
                    continue
                if max_tier >= 2:
                    shape_bits = []
                    if entry.min_rows is not None:
                        shape_bits.append(f"min_rows={entry.min_rows}")
                    if entry.columns is not None:
                        shape_bits.append(f"cols={len(entry.columns)}")
                    if entry.n_cols is not None:
                        shape_bits.append(f"n_cols={entry.n_cols}")
                    if entry.columns_contain is not None:
                        shape_bits.append(f"contains={len(entry.columns_contain)}")
                    _log_check("shape", rel, ",".join(shape_bits) or "presence-only")
                    check_shape(batch_root, entry, rel)
                if max_tier >= 3 and goldens_root is not None and entry.value_check:
                    _log_check("value", rel, "golden")
                    check_value(batch_root, goldens_root, entry, rel)


def verify_manifest(
    manifest: StageManifest,
    batch_root: pathlib.Path,
    cardinality: int,
    n_runs: int,
    *,
    max_tier: int = 1,
    goldens_root: tp.Optional[pathlib.Path] = None,
    stats: tp.Optional[tp.Sequence[str]] = None,
    scope: str = "all",
) -> None:
    """Verify a ``StageManifest`` against a batch root, up to ``max_tier``.

    The manifest-agnostic core: ``verify_stage`` resolves ``spec.stages[stage]``
    and calls this, but any caller with a manifest in hand can use it directly.
    That is the declarative home for plugin-specific outputs (e.g. modelrunner's
    ``.model``/``.legend`` files), which don't belong in an engine's shared
    ``stages`` manifest because they're only produced when that plugin is
    enabled.

    ``stats`` are pre-resolved stat extensions (from ``_stat_exts``); None means
    the manifest contains no ``{stat}`` paths to expand.

    ``scope`` limits which parts are checked: ``"all"`` (default) checks per-exp,
    inter-exp, and absent; ``"per_exp"`` and ``"inter_exp"`` restrict to that
    part. ``absent`` is checked only under ``"all"``.
    """
    if scope not in ("all", "per_exp", "inter_exp"):
        raise ValueError(f"scope must be all/per_exp/inter_exp, got {scope!r}")

    stats = stats or ()

    _logger.info(
        "Begin verify manifest: tier<=%d scope=%s cardinality=%d n_runs=%d "
        "per_exp=%d inter_exp=%d absent=%d root=%s",
        max_tier,
        scope,
        cardinality,
        n_runs,
        len(manifest.per_exp),
        len(manifest.inter_exp),
        len(manifest.absent),
        batch_root,
    )

    if scope in ("all", "per_exp"):
        _verify_entries(
            manifest.per_exp,
            batch_root,
            goldens_root,
            range(cardinality),
            n_runs,
            stats,
            max_tier,
        )
    if scope in ("all", "inter_exp"):
        _verify_entries(
            manifest.inter_exp,
            batch_root,
            goldens_root,
            range(cardinality),
            n_runs,
            stats,
            max_tier,
        )

    # 'absent' entries must NOT be produced. Which ones apply depends on scope:
    # an intra-experiment run verifies intra 'absent' paths, an inter-experiment
    # (collation) run verifies inter-exp 'absent' paths. Classify by whether the
    # path is under 'inter-exp/'.
    def _is_interexp(tmpl: str) -> bool:
        return "inter-exp" in tmpl

    for tmpl in manifest.absent:
        if scope == "per_exp" and _is_interexp(tmpl):
            continue
        if scope == "inter_exp" and not _is_interexp(tmpl):
            continue
        for i in range(cardinality):
            for rel in _expand(ExpectedOutput(path=tmpl), i, n_runs, stats):
                _log_check("absent", rel, "must-not-exist")
                path = batch_root / rel
                assert not path.is_file(), f"[absent] unexpectedly present: {path}"


def graph_paths(
    spec: EngineSpec,
    stage: int,
    cardinality: tp.Optional[int] = None,
    *,
    scope: str = "all",
) -> tp.List[str]:
    """Return the concrete ``.png`` graph paths a stage's manifest declares.

    Filters the manifest to graph entries (``.png`` suffix) and expands ``{i}``
    over experiments, so callers get the exact per-exp + inter-exp graph list
    without hard-coding names. This keeps graph names in ONE place (the manifest)
    -- e.g. the prod.graphs backend smoke derives its expected files from here
    and only adds the ``.html`` backend dimension itself.
    """
    manifest = spec.stages[stage]
    card = cardinality or spec.cardinality
    out: tp.List[str] = []
    groups = []
    if scope in ("all", "per_exp"):
        groups.append((manifest.per_exp, True))
    if scope in ("all", "inter_exp"):
        groups.append((manifest.inter_exp, False))
    for entries, per_exp in groups:
        for e in entries:
            if not e.path.endswith(".png"):
                continue
            if per_exp:
                for i in range(card):
                    out.extend(_expand(e, i, spec.n_runs, ()))
            else:
                # inter-exp graph paths have no {i}; expand once.
                out.extend(_expand(e, 0, spec.n_runs, ()))
    return out


def verify_stage(
    spec: EngineSpec,
    stage: int,
    batch_root: pathlib.Path,
    *,
    max_tier: int = 1,
    goldens_root: tp.Optional[pathlib.Path] = None,
    center: tp.Optional[str] = None,
    spread: tp.Optional[str] = None,
    cardinality_override: tp.Optional[int] = None,
    scope: str = "all",
) -> None:
    """Verify one stage's outputs for one engine, up to ``max_tier``.

    Smoke tests call this with ``max_tier=1`` (presence). The cheap-regression
    layer calls with ``max_tier=2``. Full regression calls ``max_tier=3`` and a
    ``goldens_root``. All three read the SAME manifest, so they cannot drift.

    ``center``/``spread`` are *lookup keys* into ``sierra.core.config.STATS``;
    any manifest path containing ``{stat}`` is expanded over the extensions that
    config reports for that pair (never over the literal center/spread names).
    When omitted, SIERRA's defaults are used. This is what lets one stage
    manifest serve every ``--center``/``--spread`` combination while keeping the
    on-disk suffixes authoritative.

    ``cardinality_override`` checks fewer experiments than the spec's default,
    for runs against an alternate batch criteria (e.g. ros1robot's Log8 sweep,
    checked to cardinality 3).

    ``scope`` limits which parts of the manifest are checked: ``"all"`` (default)
    checks per-exp, inter-exp, and absent; ``"per_exp"`` checks only per-exp
    entries; ``"inter_exp"`` checks only inter-exp entries. ``"per_exp"`` covers
    plugin runs that deliberately produce only intra-experiment statistics and
    no collation. ``absent`` is checked only under ``"all"``, since it is a
    whole-stage contract.
    """
    manifest: StageManifest = spec.stages[stage]
    stats = _stat_exts(center, spread)
    cardinality = cardinality_override or spec.cardinality

    # Goldens are laid out per engine + center/spread, mirroring the batch-root
    # tree beneath. Resolve that subdir here so one manifest entry (value_check)
    # serves every center/spread combination. The caller passes the *base*
    # goldens dir; the concrete center/spread are known only here.
    if goldens_root is not None and max_tier >= 3:
        c = center if center is not None else DEFAULT_CENTER
        s = spread if spread is not None else DEFAULT_SPREAD
        goldens_root = goldens_root / f"{spec.name}-{c}-{s}"

    verify_manifest(
        manifest,
        batch_root,
        cardinality,
        spec.n_runs,
        max_tier=max_tier,
        goldens_root=goldens_root,
        stats=stats,
        scope=scope,
    )


def verify_bivar_stage(
    spec: EngineSpec,
    stage: int,
    batch_root: pathlib.Path,
    cardinality0: int,
    cardinality1: int,
    *,
    max_tier: int = 1,
    goldens_root: tp.Optional[pathlib.Path] = None,
    center: tp.Optional[str] = None,
    spread: tp.Optional[str] = None,
) -> None:
    """Verify one bivariate stage's outputs.

    Bivariate batch criteria produce a 2D experiment cross-product named
    ``c1-exp{i}+c2-exp{j}``. Manifest paths use ``{i}`` and ``{j}``; everything
    else (``{stat}`` via config.STATS, tiers, goldens) works exactly as in the
    univariate ``verify_stage``.

    The manifest is looked up from ``spec.bivar_stages[stage]`` so an engine's
    univariate and bivariate expectations stay separate.
    """
    manifest: StageManifest = spec.bivar.stages[stage]
    stats = _stat_exts(center, spread)

    def _verify(entries):
        for entry in entries:
            for i in range(cardinality0):
                for j in range(cardinality1):
                    for rel in _expand(entry, i, spec.n_runs, stats, j=j):
                        check_presence(batch_root, entry, rel)
                        if entry.is_dir:
                            continue
                        if max_tier >= 2:
                            check_shape(batch_root, entry, rel)
                        if max_tier >= 3 and goldens_root is not None:
                            check_value(batch_root, goldens_root, entry, rel)

    _verify(manifest.per_exp)
    _verify(manifest.inter_exp)

    for tmpl in manifest.absent:
        for i in range(cardinality0):
            for j in range(cardinality1):
                for rel in _expand(
                    ExpectedOutput(path=tmpl), i, spec.n_runs, stats, j=j
                ):
                    path = batch_root / rel
                    assert not path.is_file(), f"[absent] unexpectedly present: {path}"


def _csv_dims(path: pathlib.Path) -> tp.Tuple[int, int]:
    """Return (n_data_rows, n_cols) for a collated stage-5 CSV.

    Excludes the header row from the row count.
    """
    with open(path) as f:
        rows = list(csv.reader(f))
    n_rows = max(0, len(rows) - 1)  # minus header
    n_cols = len(rows[0]) if rows else 0
    return n_rows, n_cols


def _check_comparison_csvs(
    root: pathlib.Path, spec: ComparisonSpec, n_csvs: int
) -> None:
    """CSV count, per-CSV column count, and per-measure row filtering."""
    csvs = list(root.iterdir())
    _log_check("shape", root, "# comparison CSVs")
    assert (
        len(csvs) == n_csvs
    ), f"[{spec.kind}] expected {n_csvs} CSVs in {root}, found {len(csvs)}"

    expected_cols = spec.n_things() + 1  # +1 for the index column
    for path in csvs:
        n_rows, n_cols = _csv_dims(path)
        _log_check("shape", path, "# columns")

        assert n_cols == expected_cols, (
            f"[{spec.kind}] expected {spec.n_things()} things (+index = "
            f"{expected_cols} cols) in {path.name}, got {n_cols}"
        )
        # include_exp row filtering, only for the measures the spec pins.
        for frag, exp_rows in spec.measure_rows.items():
            if frag in path.name:
                _log_check("shape", path, "# rows")
                assert n_rows == exp_rows, (
                    f"[{spec.kind}] expected {exp_rows} rows in {path.name}, "
                    f"got {n_rows}"
                )


def _check_comparison_models(root: pathlib.Path, spec: ComparisonSpec) -> None:
    """Model dir: one .model (+matching .legend) per measure, right shape."""
    assert root.is_dir(), f"[{spec.kind}] models dir {root} does not exist"

    model_ext = config.MODELS_EXT["model"]
    legend_ext = config.MODELS_EXT["legend"]
    model_files = list(root.glob(f"*{model_ext}"))

    _log_check("shape", root, "# model files")
    assert len(model_files) == len(spec.model_rows), (
        f"[{spec.kind}] expected {len(spec.model_rows)} '{model_ext}' files in "
        f"{root}, found {len(model_files)}: {[f.name for f in model_files]}"
    )

    expected_cols = spec.n_things() + 1
    for frag, exp_rows in spec.model_rows.items():
        matches = [f for f in model_files if frag in f.name]
        _log_check(
            "presence",
            frag,
            "1:1 model:csv match",
        )
        assert len(matches) == 1, (
            f"[{spec.kind}] expected exactly 1 model file for '{frag}' in "
            f"{root}, found {len(matches)}"
        )
        mf = matches[0]

        lf = mf.with_suffix(legend_ext)
        _log_check("presence", lf, "legend file")
        assert (
            lf.exists()
        ), f"[{spec.kind}] model {mf.name} has no matching legend {lf.name}"

        n_rows, n_cols = _csv_dims(mf)
        _log_check("shape", mf, "# rows")
        assert (
            n_rows == exp_rows
        ), f"[{spec.kind}] expected {exp_rows} rows in {mf.name}, got {n_rows}"
        _log_check("shape", mf, "# cols")
        assert n_cols == expected_cols, (
            f"[{spec.kind}] expected index + {spec.n_things()} things in "
            f"{mf.name}, got {n_cols} ({n_cols - 1} data column(s))"
        )


def verify_comparison(
    spec: ComparisonSpec, sierra_root: pathlib.Path, n_csvs: int
) -> None:
    """Verify one stage-5 comparison's outputs from a ``ComparisonSpec``.

    This is a deliberately SEPARATE checking primitive from ``verify_manifest``,
    not an oversight: comparison outputs are checked as a *directory of unknown-
    exact-names* -- "exactly N CSVs exist", "each has n_things+1 columns", "any
    file whose name contains 'cc-food-counts' has 3 rows" -- whereas the manifest
    model checks *specifically-named paths*. The two are different kinds of
    check (exhaustive count + runtime-derived shape vs. named-path presence), so
    stage 5 gets its own spec type (``ComparisonSpec``) and checker rather than
    forcing count/fragment/runtime-shape machinery onto ``StageManifest`` that
    only this caller would use. It still shares the framework's logging and is
    fully spec-driven -- there are no ``if kind == ...`` branches here.

    Which parts run is driven by what the spec declares:

    * ``spec.n_graphs`` set   -> check the ``-{kind}-graphs`` file count.
    * ``spec.model_rows`` set -> check the ``-{kind}-models`` root.

    ``graph_root_override`` lets the bivariate caller (which rebuilds the graph
    root per primary-axis and checks it each time) point at an explicit dir;
    otherwise the root is derived from the spec. ``n_graphs_override`` similarly
    lets a caller override the expected count for a specific invocation.
    """
    sierra_root = pathlib.Path(sierra_root)

    _check_comparison_csvs(sierra_root / spec.root("csvs"), spec, n_csvs)

    if spec.n_graphs is not None:
        graph_root = sierra_root / spec.root("graphs")
        n_expected = spec.n_graphs
        graphs = list(pathlib.Path(graph_root).iterdir())

        _log_check("presence", graph_root, "# graphs")
        assert len(graphs) == n_expected, (
            f"[{spec.kind}] expected {n_expected} files in {graph_root}, "
            f"found {len(graphs)}"
        )

    if spec.model_rows is not None:
        _check_comparison_models(sierra_root / spec.root("models"), spec)
