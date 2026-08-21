#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Declarative description of every engine SIERRA can drive.

Each engine is described *once* by an ``EngineSpec``; the conformance and plugin
checkers iterate over these specs.

The three verification tiers (presence / shape / value) all read from the SAME
``ExpectedOutput`` list, so the expected-file set can never drift between a
"does it exist" check and a "does it have the right rows" check — they are the
same declaration, read at different depths.

"""

# Core packages
import dataclasses
import typing as tp


@dataclasses.dataclass(frozen=True)
class ExpectedOutput:
    """One output artifact, described at up to three levels of scrutiny.

    Tier 1 (presence)  : the file must exist.                 -> always checked
    Tier 2 (shape)     : min_rows / columns, if given.        -> cheap regression
    Tier 3 (value)     : golden, if given.                    -> full regression

    Fill in only as much as you want checked for a given engine. A brand-new
    engine can ship with presence-only manifests and grow shape/value coverage
    later without touching any checker code.
    """

    #: Path relative to the batch root, with ``{i}`` for the experiment index
    #: and ``{run}`` for the run index. Expanded by the checker.
    path: str

    #: When True, the presence check asserts the path is a *directory* rather
    #: than a file, and shape/value tiers are skipped (a directory has no rows
    #: or columns). Use this when the only thing structurally certain is that a
    #: per-run output *dir* was created (e.g. an engine whose raw output
    #: filenames aren't pinned down), so the manifest still asserts "the sim ran
    #: and wrote its output tree" without guessing at filenames.
    is_dir: bool = False

    # Tier 2 — shape
    min_rows: tp.Optional[int] = None
    #: Exact column names, in order. Use for files whose full schema is known
    #: (raw simulator output). Asserts tuple equality.
    columns: tp.Optional[tp.Tuple[str, ...]] = None
    #: Exact column COUNT, name-agnostic. Use for collated files whose column
    #: count is known but names are only partly determinable — e.g. stage-3
    #: run-collation, which produces one column per run (count = n_runs) whose
    #: names contain ``run{i}`` but are otherwise scenario-dependent.
    n_cols: tp.Optional[int] = None
    #: Column names that MUST be present (subset, order-independent). Use for
    #: collated files where some names are pinned but an index/clock column may
    #: or may not precede them — e.g. stage-4 inter-exp collation, whose data
    #: columns are ``c1-exp{n}`` for n in range(cardinality).
    columns_contain: tp.Optional[tp.Tuple[str, ...]] = None
    #: Substrings that must NOT appear in the file's content.
    forbidden_content: tp.Tuple[str, ...] = ()

    # Tier 3 — value
    #: When True, this output is golden-compared at ``max_tier=3``: the expanded
    #: path is read from the batch root and from the goldens root at the SAME
    #: relative path, and the frames must match. The goldens root is passed by
    #: the caller and is center/spread-specific (see ``verify_stage``), so one
    #: manifest entry serves every ``--center``/``--spread`` combination without
    #: duplicating a golden path per combination. ``{stat}``/``{i}`` expansion is
    #: shared with the presence/shape tiers, so the golden set can never drift
    #: from the presence set.
    value_check: bool = False


@dataclasses.dataclass(frozen=True)
class StageManifest:
    """Expected outputs for one pipeline stage, split by scope.

    ``per_exp`` entries are expanded over experiments (and runs, if ``{run}``
    appears); ``inter_exp`` entries are checked once. ``absent`` entries must
    NOT exist — they pin substring-bleed regressions (e.g.
    ``subdir1/subdir2/output2D`` that no graph names).
    """

    per_exp: tp.Tuple[ExpectedOutput, ...] = ()
    inter_exp: tp.Tuple[ExpectedOutput, ...] = ()
    absent: tp.Tuple[str, ...] = ()


@dataclasses.dataclass(frozen=True)
class BivarSpec:
    """Bivariate coupling for an engine: the batch-criteria pairs, cardinalities,
    and controllers the bivar smoke sessions drive.

    Keeping this on the spec makes the bivar sessions engine-agnostic: exercising
    a new engine bivariately is a matter of populating this field (plus
    ``bivar_stages``) on that engine's spec, with no change to the session
    bodies. Every field defaults to ``None``/empty, so an engine that sets
    ``bivar_stages`` but omits a particular session's inputs is skipped for that
    session rather than mis-run.
    """

    #: (bc_pair, card0, card1) orderings for the stage-1 axis-order check. The
    #: two orderings swap cardinalities to prove grid generation is order-agnostic.
    stage1_orderings: tp.Tuple[tp.Tuple[tp.Tuple[str, str], int, int], ...] = ()
    #: (bc_pair, card0, card1) for the stage 2/3 grid.
    stage23: tp.Optional[tp.Tuple[tp.Tuple[str, str], int, int]] = None
    #: (bc_pair, card0, card1, controller) for the stage-4 grid (alt controller).
    stage4: tp.Optional[tp.Tuple[tp.Tuple[str, str], int, int, str]] = None
    #: (bc_pair, controllers, cc_leaf_template) for the stage-5 dispatch check.
    #: cc_leaf_template is formatted with ``c0=controllers[0], c1=controllers[1]``.
    stage5: tp.Optional[tp.Tuple[str, tp.Tuple[str, str], str]] = None

    #: Per-stage expected outputs for BIVARIATE batch criteria (2D experiment
    #: cross-product, paths using ``{i}`` and ``{j}``). Empty for engines that
    #: are never exercised bivariately. Separate from ``stages`` so the two
    #: geometries never bleed into each other.
    stages: tp.Mapping[int, StageManifest] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class EngineSpec:
    """Everything that varies between engines, in one place.

    The single source of truth for an engine's base command, batch roots, and
    expected outputs. Consumed by env.py (to build the command) and verify.py
    (to check outputs); there are no per-engine branches anywhere else.
    """

    name: str
    project: str
    controller: str
    scenario: str
    template_stem: str
    batch_criteria: str
    #: Name of the env var this engine's base command is published under, read
    #: by the smoke sessions (e.g. "JSONSIM_BASE_CMD"). env.py builds the value
    #: from this spec, so the command and the manifests share one source.
    base_cmd_env: str
    cardinality: int
    n_runs: int

    #: SIERRA ``--engine=`` value (e.g. "engine.argos", "plugins.jsonsim").
    engine_module: str

    #: Per-stage expected outputs. Keys are stage numbers.
    stages: tp.Mapping[int, StageManifest]

    #: The engine-specific tail of the base command: every flag NOT already
    #: derived from the structured fields above (project/controller/scenario/
    #: n-runs/engine). An explicit tuple so the exact flag set lives with the
    #: spec. Placeholders {sample_root} and {sierra_root} are expanded by env.py.
    base_flags: tp.Tuple[str, ...] = ()

    #: True if this engine can run without heavy system deps (ARGoS/ROS). The
    #: lightest such engine is the "reference plugin" core tests load to
    #: exercise plugin *dispatch* without needing the whole plugin zoo.
    lightweight: bool = False

    #: Additional batch criteria this engine's stage-1 smoke should also run,
    #: each with the cardinality to check. The primary ``batch_criteria`` above
    #: is always run at ``cardinality``; these are extra (bc, cardinality) pairs
    #: (e.g. ros1robot runs two population_size criteria).
    extra_criteria: tp.Tuple[tp.Tuple[str, int], ...] = ()

    #: Bivariate coupling (batch-criteria pairs, cardinalities, controllers) for
    #: the bivar smoke sessions. None => this engine is not exercised bivariately
    #: and the bivar sessions skip it. See ``BivarSpec``.
    bivar: tp.Optional[BivarSpec] = None

    @property
    def is_ros(self) -> bool:
        """True for the ROS1 engines (ros1robot/ros1gazebo).

        Their ROS stack only exists on the ubuntu20.04 image, so their smoke
        rows are tagged ``ros`` and run in a dedicated workflow slice pinned to
        that container; other slices' tag expressions exclude ``ros``.
        """
        return self.engine_module.startswith("engine.ros")


# --- The registry ----------------------------------------------------------
# One entry per engine. Fill manifests as deep as you want that engine checked.

#: Column schema of signal-trace.csv (jsonsim + yamlsim). col0/col1 = the
#: deterministic reference/baseline signals; the rest carry per-run noise.
_SIGNAL_COLS = ("clock", "reference", "measured", "drift", "baseline", "raw")


def _jsonsim_raw_outputs() -> tp.Tuple[ExpectedOutput, ...]:
    """Stage-2 raw per-run outputs: signal-trace + field-2d in the root and the
    two sensor dirs. Shapes are the deterministic simulator schema."""
    base = "exp-outputs/c1-exp{i}/template_run{run}_output/output/"
    out = []
    for d in ("", "sensors/primary/", "sensors/backup/"):
        out.append(
            ExpectedOutput(
                f"{base}{d}signal-trace.csv", min_rows=50, columns=_SIGNAL_COLS
            )
        )
        out.append(
            ExpectedOutput(
                f"{base}{d}field-2d.csv", min_rows=48, columns=("x", "y", "z")
            )
        )
    return tuple(out)


def _jsonsim_bivar_stages() -> tp.Mapping[int, "StageManifest"]:
    """Bivariate expected outputs (2D experiment cross-product). Paths use
    ``{i}`` and ``{j}`` for the two criteria axes; the c1-exp{i}+c2-exp{j} grid
    is walked by verify_bivar_stage.

    Under bivariate criteria only the ``*_bivar`` graph categories render (per
    graphs.yaml): the inter-exp heatmap surfaces. Intra-exp graphs keep their
    univariate types with the grid path template. Derived directly from the
    jsonsim graphs.yaml / collate.yaml.
    """
    return {
        1: StageManifest(
            per_exp=(
                ExpectedOutput("exp-inputs/c1-exp{i}+c2-exp{j}/exp_def.pkl"),
                ExpectedOutput("exp-inputs/c1-exp{i}+c2-exp{j}/seeds.pkl"),
                ExpectedOutput("exp-inputs/c1-exp{i}+c2-exp{j}/template_run{run}.json"),
            ),
        ),
        2: StageManifest(
            per_exp=(
                ExpectedOutput(
                    "exp-outputs/c1-exp{i}+c2-exp{j}/template_run{run}_output/"
                    "output/signal-trace.csv",
                    min_rows=50,
                    columns=_SIGNAL_COLS,
                ),
            ),
        ),
        3: StageManifest(
            per_exp=(
                ExpectedOutput(
                    "statistics/c1-exp{i}+c2-exp{j}/signal-trace.{stat}",
                    min_rows=50,
                    columns=_SIGNAL_COLS,
                ),
            ),
        ),
        4: StageManifest(
            per_exp=(
                # Intra-exp graphs render per grid cell, univariate types.
                ExpectedOutput("graphs/c1-exp{i}+c2-exp{j}/SLN-signal-intra.png"),
            ),
            inter_exp=(
                # Bivariate surfaces: the HM_bivar category over the 2D grid.
                ExpectedOutput("graphs/inter-exp/HM-signal-surface.png"),
                ExpectedOutput("graphs/inter-exp/HM-sensor-primary-surface.png"),
                ExpectedOutput("graphs/inter-exp/HM-sensor-backup-surface.png"),
            ),
        ),
    }


JSONSIM = EngineSpec(
    name="jsonsim",
    project="projects.sample_jsonsim",
    controller="signal.kalman",
    scenario="cleanroom",
    template_stem="template",
    batch_criteria="max_speed.1.9.C5",
    base_cmd_env="JSONSIM_BASE_CMD",
    engine_module="plugins.jsonsim",
    base_flags=(
        "--exp-setup=exp_setup.T50",
        "-xstrict",
        "--expdef-template={sample_root}/exp/jsonsim/template.json",
        "-xno-devnull",
        "--expdef=expdef.json",
        "--jsonsim-path={sample_root}/plugins/jsonsim/jsonsim.py",
        "--log-level=TRACE",
    ),
    cardinality=5,
    n_runs=4,
    lightweight=True,  # pure-python -> the reference plugin for core tests
    stages={
        1: StageManifest(
            per_exp=(
                ExpectedOutput("exp-inputs/c1-exp{i}/exp_def.pkl"),
                ExpectedOutput("exp-inputs/c1-exp{i}/seeds.pkl"),
                ExpectedOutput(
                    "exp-inputs/c1-exp{i}/template_run{run}.json",
                    forbidden_content=("-1", "foobar"),
                ),
            ),
        ),
        # Stage 2 = raw per-run simulation outputs, BEFORE statistics/collation.
        # A distinct stage so execenv/parallelism smoke can assert "the sim ran
        # and wrote raw output" without pulling in stage-3 statistics. Shape data
        # is the deterministic simulator schema: signal-trace is 50 rows
        # (n_datapoints=T50) x (clock, reference, measured, drift, baseline, raw);
        # field-2d is 48 rows (8x6) x (x, y, z). Checked at tier 2+.
        2: StageManifest(
            per_exp=_jsonsim_raw_outputs(),
        ),
        3: StageManifest(
            # value_check entries are golden-compared at tier 3: intra-exp stat
            # files and inter-exp collated CSVs, compared against goldens under
            # ``regression/goldens/jsonsim-{center}-{spread}/``. The presence and
            # shape tiers already cover these same paths, so the golden set
            # cannot drift from the presence set.
            per_exp=(
                # {stat} files are per-datapoint statistics across the N runs, so
                # they preserve the raw simulator schema. signal-trace -> 50 rows
                # x its 6 columns; field-2d -> 48 rows x (x, y, z). Shape checked
                # at tier 2+; value at tier 3.
                ExpectedOutput(
                    "statistics/c1-exp{i}/signal-trace.{stat}",
                    min_rows=50,
                    columns=_SIGNAL_COLS,
                    value_check=True,
                ),
                ExpectedOutput(
                    "statistics/c1-exp{i}/field-2d.{stat}",
                    min_rows=48,
                    columns=("x", "y", "z"),
                    value_check=True,
                ),
                ExpectedOutput(
                    "statistics/c1-exp{i}/sensors/primary/signal-trace.{stat}",
                    min_rows=50,
                    columns=_SIGNAL_COLS,
                    value_check=True,
                ),
                ExpectedOutput(
                    "statistics/c1-exp{i}/sensors/backup/signal-trace.{stat}",
                    min_rows=50,
                    columns=_SIGNAL_COLS,
                    value_check=True,
                ),
                ExpectedOutput(
                    "statistics/c1-exp{i}/sensors/backup/field-2d.{stat}",
                    min_rows=48,
                    columns=("x", "y", "z"),
                    value_check=True,
                ),
                # Analysis datasets feeding the scatter/histogram graphs.
                ExpectedOutput(
                    "statistics/c1-exp{i}/anscombe.{stat}",
                    min_rows=11,
                    value_check=True,
                ),
                ExpectedOutput("statistics/c1-exp{i}/dose-response.{stat}"),
                ExpectedOutput("statistics/c1-exp{i}/lognormal.{stat}"),
                ExpectedOutput("statistics/c1-exp{i}/bimodal.{stat}"),
                ExpectedOutput("statistics/c1-exp{i}/beta-family.{stat}"),
            ),
            inter_exp=(
                # Per-experiment run-collation (collate.yaml): one column per run
                # (n_runs), preserving the source row count. signal-trace rows =
                # 50; column count is n_runs (index-column-immune subset check
                # not used here since names are scenario-dependent).
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp{i}/signal-trace-measured.csv",
                    min_rows=50,
                    value_check=True,
                ),
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp{i}/signal-trace-drift.csv",
                    min_rows=50,
                    value_check=True,
                ),
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp{i}/sensors/primary/"
                    "signal-trace-measured.csv",
                    min_rows=50,
                    value_check=True,
                ),
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp{i}/sensor-combined-measured.csv",
                    value_check=True,
                ),
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp{i}/"
                    "sensor-combined-measured_backup.csv",
                    value_check=True,
                ),
            ),
            # Substring-bleed regressions: collation must resolve to exactly the
            # named columns, never fan out to un-collated columns or sibling dirs.
            absent=(
                "statistics/inter-exp/c1-exp{i}/signal-trace-reference.csv",
                "statistics/inter-exp/c1-exp{i}/signal-trace-baseline.csv",
                "statistics/inter-exp/c1-exp{i}/sensors/backup/"
                "signal-trace-measured.csv",
            ),
        ),
        4: StageManifest(
            per_exp=(
                # Intra-exp graphs, type-prefixed (SLN/HM/SP/HG) per graphs.yaml.
                ExpectedOutput("graphs/c1-exp{i}/SLN-signal-intra.png"),
                ExpectedOutput("graphs/c1-exp{i}/SLN-sensor-primary-intra.png"),
                ExpectedOutput("graphs/c1-exp{i}/SLN-sensor-backup-intra.png"),
                ExpectedOutput("graphs/c1-exp{i}/SLN-sensor-combined.png"),
                ExpectedOutput("graphs/c1-exp{i}/HM-field-heatmap.png"),
                ExpectedOutput("graphs/c1-exp{i}/HM-field-heatmap-backup.png"),
                ExpectedOutput("graphs/c1-exp{i}/SP-signal-correlation.png"),
                ExpectedOutput("graphs/c1-exp{i}/SP-dose-response-fit.png"),
                ExpectedOutput("graphs/c1-exp{i}/SP-anscombe-1.png"),
                ExpectedOutput("graphs/c1-exp{i}/SP-anscombe-2.png"),
                ExpectedOutput("graphs/c1-exp{i}/SP-anscombe-3.png"),
                ExpectedOutput("graphs/c1-exp{i}/SP-anscombe-4.png"),
                ExpectedOutput("graphs/c1-exp{i}/HG-lognormal-dist.png"),
                ExpectedOutput("graphs/c1-exp{i}/HG-bimodal-dist.png"),
                ExpectedOutput("graphs/c1-exp{i}/HG-beta-shapes.png"),
            ),
            inter_exp=(
                # Inter-exp collated summaries: one data column per experiment,
                # named c1-exp{n}. columns_contain is index-column-immune.
                ExpectedOutput(
                    "statistics/inter-exp/signal-summary.{stat}",
                    columns=("c1-exp0", "c1-exp1", "c1-exp2", "c1-exp3", "c1-exp4"),
                ),
                ExpectedOutput(
                    "statistics/inter-exp/sensor-primary-summary.{stat}",
                    columns=("c1-exp0", "c1-exp1", "c1-exp2", "c1-exp3", "c1-exp4"),
                ),
                ExpectedOutput(
                    "statistics/inter-exp/sensor-backup-summary.{stat}",
                    columns=("Experiment ID", "signal.kalman+cleanroom"),
                ),
                ExpectedOutput(
                    "statistics/inter-exp/signal-scatter-summary.{stat}",
                    columns=("exp", "x", "y"),
                ),
                # Inter-exp graphs (_default categories).
                ExpectedOutput("graphs/inter-exp/SLN-signal-summary.png"),
                ExpectedOutput("graphs/inter-exp/SLN-sensor-primary-summary.png"),
                ExpectedOutput("graphs/inter-exp/SM-sensor-backup-summary.png"),
                ExpectedOutput("graphs/inter-exp/SP-signal-scatter-summary.png"),
            ),
        ),
    },
    bivar=BivarSpec(
        # Two univariate criteria (max_speed x fuel) form the 2D grid. jsonsim
        # ships four signal controllers (signal.{kalman,lowpass,bandpass,
        # bandstop}), so it CAN be exercised bivariately at every stage: stage4
        # runs the grid under an alt controller (signal.lowpass, != the default
        # signal.kalman), and stage5 drives a cardinality-2 inter-controller
        # comparison over a comparable pair (bandpass/bandstop, the same pair
        # the compare/graphs bivar smoke uses).
        stage1_orderings=(
            (("max_speed.1.9.C3", "fuel.1.9.C5"), 3, 5),
            (("fuel.1.9.C5", "max_speed.1.9.C3"), 5, 3),
        ),
        stage23=(("max_speed.1.9.C2", "fuel.1.9.C3"), 2, 3),
        # (bc_pair, card0, card1, controller): same 2x3 grid as stage23, run
        # under an alternate (non-default) controller so stage-4 graph/CSV
        # generation is exercised off the default. The controller MUST be one
        # that emits the HM_bivar surface graphs the stage-4 manifest checks
        # (graphs/inter-exp/HM-*-surface.png) -- only signal.bandstop generates
        # those, so an arbitrary alt like signal.lowpass would run fine but fail
        # verification with the surfaces missing.
        stage4=(("max_speed.1.9.C2", "fuel.1.9.C3"), 2, 3, "signal.bandstop"),
        # (bc, controllers, cc_leaf_template): bc is a space-joined pair the
        # session splits back apart (cardinality-2 dispatch), identical to the
        # stage23 grid so it can't drift from compare/graphs' _BIVAR_BC. The
        # leaf template is formatted with c0/c1 at consume time.
        stage5=(
            "max_speed.1.9.C2 fuel.1.9.C3",
            ("signal.bandpass", "signal.bandstop"),
            "{c0}+{c1}-cc-graphs",
        ),
        stages=_jsonsim_bivar_stages(),
    ),
)

YAMLSIM = EngineSpec(
    name="yamlsim",
    project="projects.sample_yamlsim",
    controller="default.default",
    scenario="scenario1",
    template_stem="template",
    batch_criteria="noise_floor.1.9.C5",
    base_cmd_env="YAMLSIM_BASE_CMD",
    engine_module="plugins.yamlsim",
    base_flags=(
        "-xstrict",
        "--expdef-template={sample_root}/exp/yamlsim/template.yaml",
        "-xno-devnull",
        "--expdef=expdef.yaml",
        "--yamlsim-path={sample_root}/plugins/yamlsim/yamlsim.py",
        "--log-level=TRACE",
    ),
    cardinality=5,
    n_runs=4,
    lightweight=True,
    stages={
        1: StageManifest(
            per_exp=(
                ExpectedOutput("exp-inputs/c1-exp{i}/exp_def.pkl"),
                ExpectedOutput("exp-inputs/c1-exp{i}/template_run{run}.yaml"),
            ),
        ),
        # Stage 2 = raw per-run outputs. The simulator writes signal-trace.csv at
        # the run output root plus a nested sensors/primary copy (the latter is
        # what collation's multi-source join lifts). classification.csv and the
        # networks/ graphml dir are also produced here but are exercised through
        # their stage-4 graphs (CM/NW), not shape-checked as raw.
        2: StageManifest(
            per_exp=(
                ExpectedOutput(
                    "exp-outputs/c1-exp{i}/template_run{run}_output/output/"
                    "signal-trace.csv",
                    min_rows=50,
                    columns=_SIGNAL_COLS,
                ),
                ExpectedOutput(
                    "exp-outputs/c1-exp{i}/template_run{run}_output/output/"
                    "sensors/primary/signal-trace.csv",
                    min_rows=50,
                    columns=_SIGNAL_COLS,
                ),
            ),
        ),
        3: StageManifest(
            per_exp=(
                # signal-trace.{stat} preserves the raw schema: 50 rows x the 6
                # signal columns. classification (confusion) rows are random per
                # run, so it stays presence-only (no deterministic row count).
                ExpectedOutput(
                    "statistics/c1-exp{i}/signal-trace.{stat}",
                    min_rows=50,
                    columns=_SIGNAL_COLS,
                ),
                ExpectedOutput("statistics/c1-exp{i}/classification.{stat}"),
            ),
            inter_exp=(
                # Per-experiment run-collation (collate.yaml).
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp{i}/signal-trace-measured.csv",
                    min_rows=50,
                ),
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp{i}/signal-trace-drift.csv",
                    min_rows=50,
                ),
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp{i}/sensors/primary/"
                    "signal-trace-measured.csv",
                    min_rows=50,
                ),
            ),
            absent=(
                # Collation resolves to exactly the named columns.
                "statistics/inter-exp/c1-exp{i}/signal-trace-reference.csv",
                "statistics/inter-exp/c1-exp{i}/signal-trace-baseline.csv",
            ),
        ),
        4: StageManifest(
            per_exp=(
                # Intra-exp graphs per yamlsim graphs.yaml: line, confusion, and
                # three histogram render kinds.
                ExpectedOutput("graphs/c1-exp{i}/SLN-signal-intra.png"),
                ExpectedOutput("graphs/c1-exp{i}/CM-classification.png"),
                ExpectedOutput("graphs/c1-exp{i}/HG-signal-hist-overlay.png"),
                ExpectedOutput("graphs/c1-exp{i}/HG-signal-hist-steps.png"),
                ExpectedOutput("graphs/c1-exp{i}/HG-signal-hist-facet.png"),
            ),
            inter_exp=(
                ExpectedOutput(
                    "statistics/inter-exp/signal-summary.{stat}",
                    columns=("c1-exp0", "c1-exp1", "c1-exp2", "c1-exp3", "c1-exp4"),
                ),
                ExpectedOutput("graphs/inter-exp/SLN-signal-summary.png"),
                ExpectedOutput("graphs/inter-exp/HG-signal-hist-overlay.png"),
            ),
        ),
    },
)

ARGOS = EngineSpec(
    name="argos",
    project="projects.sample_argos",
    controller="foraging.footbot_foraging",
    scenario="LowBlockCount.10x10x2",
    template_stem="template",
    batch_criteria="population_size.Linear3.C3",
    base_cmd_env="ARGOS_BASE_CMD",
    engine_module="engine.argos",
    base_flags=(
        "--exp-setup=exp_setup.T50.K5",
        "--physics-n-engines=1",
        "-xstrict",
        "--expdef-template={sample_root}/exp/argos/template.argos",
        "--with-robot-leds",
        "--with-robot-rab",
        "--log-level=TRACE",
        # Factor from the hard-coded output interval of 10 in the ARGoS
        # sample project.
        "--exp-n-datapoints-factor=0.1",
    ),
    cardinality=3,
    n_runs=4,
    lightweight=False,  # needs ARGoS installed
    stages={
        1: StageManifest(
            per_exp=(
                ExpectedOutput("exp-inputs/c1-exp{i}/exp_def.pkl"),
                ExpectedOutput("exp-inputs/c1-exp{i}/seeds.pkl"),
                ExpectedOutput("exp-inputs/c1-exp{i}/template_run{run}.argos"),
            ),
        ),
        2: StageManifest(
            per_exp=(
                ExpectedOutput(
                    "exp-outputs/c1-exp{i}/template_run{run}_output/"
                    "output/collected-data.csv"
                ),
            ),
        ),
        # {stat} expands over config.STATS extensions. One manifest, every combo.
        3: StageManifest(
            per_exp=(ExpectedOutput("statistics/c1-exp{i}/collected-data.{stat}"),),
            inter_exp=(
                ExpectedOutput(
                    "statistics/inter-exp/c1-exp0/" "collected-data-collected_food.csv"
                ),
            ),
        ),
        4: StageManifest(
            per_exp=(
                ExpectedOutput("graphs/c1-exp{i}/SLN-food-counts.png"),
                ExpectedOutput("graphs/c1-exp{i}/SLN-robot-counts.png"),
                ExpectedOutput("graphs/c1-exp{i}/SLN-swarm-energy.png"),
            ),
            inter_exp=(
                # stat-suffixed collated CSVs
                ExpectedOutput("statistics/inter-exp/food-counts.{stat}"),
                ExpectedOutput("statistics/inter-exp/robot-counts-resting.{stat}"),
                ExpectedOutput("statistics/inter-exp/robot-counts-walking.{stat}"),
                ExpectedOutput("statistics/inter-exp/swarm-energy.{stat}"),
                # inter-exp graphs (no stat suffix; one per measure)
                ExpectedOutput("graphs/inter-exp/SLN-food-counts.png"),
                ExpectedOutput("graphs/inter-exp/SLN-robot-counts-walking.png"),
                ExpectedOutput("graphs/inter-exp/SLN-robot-counts-resting.png"),
                ExpectedOutput("graphs/inter-exp/SLN-swarm-energy.png"),
            ),
        ),
    },
    # No bivar spec: ARGoS is validated univariately (plugin_argos_* sessions).
    # Bivariate is generic 2D-criteria machinery layered on the same per-cell
    # execution univar already exercises -- if ARGoS runs univar, it runs bivar,
    # so re-testing it bivariately with a heavyweight binary engine adds nothing.
    # The generic bivar sweep runs on the lightweight engines (BIVAR_ENGINES).
)

ROS1ROBOT = EngineSpec(
    name="ros1robot",
    project="projects.sample_ros1robot",
    controller="turtlebot3.wander",
    scenario="OutdoorWorld.10x10x2",
    template_stem="turtlebot3",
    batch_criteria="population_size.Linear3.C3",
    base_cmd_env="ROS1ROBOT_BASE_CMD",
    engine_module="engine.ros1robot",
    base_flags=(
        "--exp-setup=exp_setup.T10.K5.N50",
        "--expdef-template={sample_root}/exp/ros1robot/turtlebot3.launch",
        "--robot",
        "turtlebot3",
        "--execenv",
        "robot.turtlebot3",
        "-sonline-check",
        "-ssync",
        "--log-level=TRACE",
    ),
    cardinality=3,
    n_runs=4,
    lightweight=False,  # needs ROS
    extra_criteria=(("population_size.Log8", 3),),
    stages={
        1: StageManifest(
            per_exp=(
                ExpectedOutput("exp-inputs/c1-exp{i}/commands_run{run}_master.txt"),
                ExpectedOutput("exp-inputs/c1-exp{i}/commands_run{run}_slave.txt"),
                ExpectedOutput(
                    "exp-inputs/c1-exp{i}/turtlebot3_run{run}_master.launch"
                ),
                # Robot index == exp index ({i}): a per-robot launch file exists
                # for this experiment's robot.
                ExpectedOutput(
                    "exp-inputs/c1-exp{i}/turtlebot3_run{run}_robot{i}.launch"
                ),
            ),
        ),
    },
)

ROS1GAZEBO = EngineSpec(
    name="ros1gazebo",
    project="projects.sample_ros1gazebo",
    controller="turtlebot3.wander",
    scenario="HouseWorld.10x10x2",
    template_stem="turtlebot3_house",
    batch_criteria="population_size.Linear3.C3",
    base_cmd_env="ROS1GAZEBO_BASE_CMD",
    engine_module="engine.ros1gazebo",
    base_flags=(
        "--exp-setup=exp_setup.T5.K2",
        "-xstrict",
        "--expdef-template={sample_root}/exp/ros1gazebo/turtlebot3_house.launch",
        "--robot",
        "turtlebot3",
        "--log-level=TRACE",
    ),
    cardinality=3,
    n_runs=4,
    lightweight=False,  # needs ROS + Gazebo
    stages={
        1: StageManifest(
            per_exp=(
                ExpectedOutput(
                    "exp-inputs/c1-exp{i}/turtlebot3_house_run{run}_master.launch"
                ),
                ExpectedOutput(
                    "exp-inputs/c1-exp{i}/turtlebot3_house_run{run}_robots.launch"
                ),
            ),
        ),
        # ros1gazebo generates no stage-2 output to check; an empty manifest
        # lets callers invoke verify_stage(ROS1GAZEBO, 2) uniformly rather than
        # special-casing it.
        2: StageManifest(),
        # deeper stages intentionally absent rather than stubbed.
    },
)


#: Every engine. The conformance suite runs the UNIVERSAL structure checks
#: over all of these; plugin checks run the engine-specific manifests.
ALL_ENGINES: tp.Tuple[EngineSpec, ...] = (
    JSONSIM,
    YAMLSIM,
    ARGOS,
    ROS1ROBOT,
    ROS1GAZEBO,
)

#: Engines usable to exercise core plugin-dispatch without system deps.
REFERENCE_ENGINE: EngineSpec = JSONSIM

#: Engines exercised by the generic bivar smoke sweep: those with a populated
#: ``bivar`` spec. This tests the engine-agnostic 2D-criteria machinery (stage
#: dispatch, cross-product experiment naming, collation across a grid), which is
#: identical regardless of engine -- so only the lightweight pure-python engines
#: carry it (they're fast and need no compiled binary).
#:
#: Heavyweight binary engines (ARGoS, ROS) deliberately have NO bivar spec: they
#: are validated univariately (the ``plugin_argos_*`` sessions), and bivariate is
#: just that same per-cell execution run over a 2D grid -- if an engine runs
#: univar it runs bivar, so re-testing it bivariately adds nothing but wall time.
#: Adding a lightweight engine to the sweep is a data edit: give it a ``bivar``
#: spec + ``bivar_stages`` and it joins automatically.
BIVAR_ENGINES = tuple(e for e in ALL_ENGINES if e.bivar is not None)

#: Lookup by short name (the ``name`` field), for callers that only have the
#: engine as a string (e.g. plugin smoke sessions parametrized over engine
#: strings). Lets those call ``verify_stage(BY_NAME[s], ...)`` instead of
#: carrying their own name->spec mapping.
BY_NAME: tp.Mapping[str, EngineSpec] = {e.name: e for e in ALL_ENGINES}
