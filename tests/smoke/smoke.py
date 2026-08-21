#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Smoke tests — presence tier (fast, broad, every engine, every PR).

Three scopes live here, and the file layout makes the core/plugin/conformance
boundary structural rather than a matter of discipline:

* ``test_conformance_*``  — the contract core imposes on EVERY engine
                            (parametrized over ALL_ENGINES). Universal.
* ``test_plugin_*``       — one engine's own artifacts (its manifest).
* ``test_core_*``         — machinery that would still make sense if every
                            plugin were deleted; parametrized over nothing,
                            using only the REFERENCE_ENGINE to drive dispatch.

Rule of thumb encoded here:
    deleting all plugins makes it meaningless   -> core
    the assertion names a format/engine artifact -> plugin
    every engine-of-this-kind must satisfy it    -> conformance
"""

# Core packages
import pathlib
import shutil

# 3rd party packages
import nox

# Project packages
from tests._framework import engines, verify, env
from tests._framework.command import SierraCommand
from sierra.core import batchroot


def _batch_root(session, spec: engines.EngineSpec, bc: str = None) -> pathlib.Path:
    """Build the batch root from the spec. ``bc`` overrides the spec's primary
    batch_criteria (used for extra_criteria runs)."""
    leaf = batchroot.ExpRootLeaf(
        bc=[bc or spec.batch_criteria], template_stem=spec.template_stem
    )
    return batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project=spec.project,
        controller=spec.controller,
        leaf=leaf,
        scenario=spec.scenario,
    ).to_path()


def _run(session, spec: engines.EngineSpec, *stages: int) -> pathlib.Path:
    base = session.env[spec.base_cmd_env].split()
    cmd = (
        SierraCommand.from_base(base)
        .set("--batch-criteria", spec.batch_criteria)
        .pipeline(*stages)
        .render()
    )
    session.run(*cmd, silent=True)
    return _batch_root(session, spec)


# ---------------------------------------------------------------------------
# CONFORMANCE — universal structure, run over every engine
# ---------------------------------------------------------------------------
@nox.session(python=env.VERSIONS, tags=["smoke", "conformance", "presence"])
@nox.parametrize(
    "engine",
    engines.ALL_ENGINES,
    ids=[e.name for e in engines.ALL_ENGINES],
    # ROS engine rows are tagged `ros` so they select into the ubuntu20.04
    # `ros` slice only; non-ROS rows carry no extra tag and run on the default
    # image. See EngineSpec.is_ros.
    tags=[["ros"] if e.is_ros else [] for e in engines.ALL_ENGINES],
)
@env.session_setup
@env.session_teardown
def conformance_stage1(session, engine):
    """Every engine must produce the SIERRA stage-1 input structure.

    Runs the engine's primary batch criteria plus any ``extra_criteria`` (e.g.
    ros1robot's second population_size sweep), checking each at its declared
    cardinality.
    """
    runs = [(engine.batch_criteria, engine.cardinality)] + list(engine.extra_criteria)
    for bc, cardinality in runs:
        base = session.env[engine.base_cmd_env].split()
        cmd = (
            SierraCommand.from_base(base)
            .set("--batch-criteria", bc)
            .pipeline(1)
            .render()
        )
        session.run(*cmd, silent=True)
        batch_root = _batch_root(session, engine, bc=bc)
        # Check at the cardinality for THIS bc (may differ from engine default).
        verify.verify_stage(
            engine, 1, batch_root, max_tier=1, cardinality_override=cardinality
        )


# ---------------------------------------------------------------------------
# PLUGIN — one engine's own artifacts (only engines that declare a stage-3
# manifest participate; ARGoS's deeper stages would add their own)
# ---------------------------------------------------------------------------
@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "presence", "grpb"])
@nox.parametrize(
    "engine",
    [e for e in engines.ALL_ENGINES if 3 in e.stages and e is not engines.ARGOS],
    ids=[
        e.name for e in engines.ALL_ENGINES if 3 in e.stages and e is not engines.ARGOS
    ],
    tags=[
        ["ros"] if e.is_ros else []
        for e in engines.ALL_ENGINES
        if 3 in e.stages and e is not engines.ARGOS
    ],
)
@env.session_setup
@env.session_teardown
def plugin_stage3(session, engine):
    """Engine-specific statistics outputs exist (presence only).

    ARGoS is handled separately (``smoke_plugin_argos_stage3``) because it runs
    across a full center/spread sweep; the lightweight engines only check the
    default statistics.
    """
    batch_root = _run(session, engine, 1, 2, 3)
    verify.verify_stage(engine, 3, batch_root, max_tier=1)


@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "presence", "grpb"])
@nox.parametrize(
    "engine",
    [e for e in engines.ALL_ENGINES if 2 in e.stages],
    ids=[e.name for e in engines.ALL_ENGINES if 2 in e.stages],
    tags=[["ros"] if e.is_ros else [] for e in engines.ALL_ENGINES if 2 in e.stages],
)
@env.session_setup
@env.session_teardown
def plugin_stage2(session, engine):
    """Engine-specific run outputs exist after stage 2 (presence only)."""
    batch_root = _run(session, engine, 1, 2)
    verify.verify_stage(engine, 2, batch_root, max_tier=1)


@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "presence", "grpb"])
@nox.parametrize(
    "engine",
    [e for e in engines.ALL_ENGINES if 4 in e.stages and e is not engines.ARGOS],
    ids=[
        e.name for e in engines.ALL_ENGINES if 4 in e.stages and e is not engines.ARGOS
    ],
    tags=[
        ["ros"] if e.is_ros else []
        for e in engines.ALL_ENGINES
        if 4 in e.stages and e is not engines.ARGOS
    ],
)
@env.session_setup
@env.session_teardown
def plugin_stage4(session, engine):
    """Engine-specific graphs and collated CSVs exist (presence only).

    ARGoS handled separately (``plugin_argos_stage4``): center/spread
    sweep and a second batch criteria.
    """
    batch_root = _run(session, engine, 1, 2, 3, 4)
    verify.verify_stage(engine, 4, batch_root, max_tier=1)


# The center/spread combinations the stage-3/4 smoke sweeps. We don't sweep all
# of them because that's covered in regression. We just sweep SOME, so that we
# can verify that everything works.
_STATS_SWEEP = [
    ("mean", "bw"),
    ("median", "iqr"),
]


@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "argos", "presence", "grpb"])
@env.session_setup
@env.session_teardown
def plugin_argos_stage4(session):
    """ARGoS stage-4 graphs/CSVs across the center/spread sweep and two bc."""
    spec = engines.ARGOS
    batch_root = _batch_root(session, spec, bc="population_size.Linear3.C3")
    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--batch-criteria", "population_size.Linear3.C3")
        .pipeline(1, 2, 3, 4)
        .render()
    )
    session.run(*cmd, silent=True)
    verify.verify_stage(spec, 4, batch_root, max_tier=1)


# ---------------------------------------------------------------------------
# PLUGIN — specialized ARGoS/yamlsim sessions.
#
# These are engine-specific behaviors that don't fit the declarative stage
# manifest (custom flags, glob-based frame/image counting, video artifacts), so
# they stay as explicit sessions.
# ---------------------------------------------------------------------------
@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "argos", "presence", "grpb"])
@env.session_setup
@env.session_teardown
def plugin_argos_physics_engines(session):
    """Multiple physics engines don't crash (smallest, mid, largest)."""
    spec = engines.ARGOS
    for n in (1, 16, 24):
        cmd = (
            SierraCommand.from_base(session.env[spec.base_cmd_env].split())
            .set("--batch-criteria", "population_size.Linear3.C3")
            .set("--physics-n-engines", str(n))
            .pipeline(1, 2)
            .render()
        )
        env.reset_root(session)
        session.run(*cmd, silent=True)


@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "argos", "presence", "grpb"])
@nox.parametrize("camera_config", ["overhead", "sw", "sw+interp"])
@env.session_setup
@env.session_teardown
def plugin_argos_vc(session, camera_config):
    """Visual capture: frames are rendered under each run's output dir."""
    spec = engines.ARGOS
    batch_root = _batch_root(session, spec, bc="population_size.Linear1.C1")
    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--batch-criteria", "population_size.Linear1.C1")
        .set_multi("--prod", ["prod.render", "prod.graphs"])
        .set("--engine-vc")
        .set("--camera-config", camera_config)
        .pipeline(1, 2, 3, 4)
        .render()
    )
    session.run(*cmd, silent=True)

    output_root = batch_root / "exp-outputs"
    for i in range(spec.n_runs):
        frames_dir = output_root / f"c1-exp0/template_run{i}_output/frames"
        assert frames_dir.is_dir(), f"Directory {frames_dir} does not exist"
        assert list(frames_dir.glob("*")), f"No frames found in {frames_dir}"


@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "argos", "presence", "grpa"])
@env.session_setup
@env.session_teardown
def plugin_argos_imagize(session):
    """Imagize: floor-state images are generated from run output."""
    spec = engines.ARGOS
    batch_root = _batch_root(session, spec, bc="population_size.Linear1.C1")
    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--batch-criteria", "population_size.Linear1.C1")
        .set_multi("--proc", ["proc.statistics", "proc.imagize", "proc.collate"])
        .set_multi("--prod", ["prod.render", "prod.graphs"])
        .set("--project-rendering")
        # Run VERY short sim to minimize CI time
        .set("--exp-setup", "exp_setup.T5.K5")
        .pipeline(1, 2, 3, 4)
        .render()
    )
    session.run(*cmd, silent=True)

    output_root = batch_root / "exp-outputs"
    imagize_root = batch_root / "imagize"
    for i in range(spec.n_runs):
        floor_state_dir = (
            output_root / f"c1-exp0/template_run{i}_output/output/floor-state"
        )
        assert floor_state_dir.is_dir(), f"Directory {floor_state_dir} missing"
    png_files = list((imagize_root / "c1-exp0/floor-state").glob("*.png"))
    assert png_files, "No imagize PNGs generated"


@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "argos", "presence", "grpa"])
@env.session_setup
@env.session_teardown
def plugin_argos_cmdline(session):
    """--n-agents is applied to generated run inputs (quantity=\"10\")."""
    spec = engines.ARGOS
    batch_root = _batch_root(session, spec)
    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--batch-criteria", "population_size.Linear3.C3")
        .set("--n-agents", "10")
        .pipeline(1)
        .render()
    )
    session.run(*cmd, silent=True)

    input_root = batch_root / "exp-inputs"
    for i in range(spec.cardinality):
        for run in range(spec.n_runs):
            template_file = input_root / f"c1-exp{i}/template_run{run}.argos"
            assert template_file.is_file(), f"{template_file} does not exist"
            assert (
                'quantity="10"' in template_file.read_text()
            ), f'{template_file} missing quantity="10"'


@nox.session(python=env.VERSIONS, tags=["smoke", "engine", "yamlsim", "presence", "grpb"])
@env.session_setup
@env.session_teardown
def plugin_yamlsim_imagize(session):
    """Imagize (yamlsim): graphml renders produce images and a video."""
    spec = engines.YAMLSIM
    batch_root = _batch_root(session, spec, bc="noise_floor.1.3.C3")
    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--batch-criteria", "noise_floor.1.3.C3")
        .set("--proc", "proc.imagize")
        .set("--prod", "prod.render")
        .set("--imagize-no-stats")
        .set("--project-rendering")
        .set("--storage", "storage.graphml")
        .pipeline(1, 2, 3, 4)
        .render()
    )
    session.run(*cmd, silent=True)

    output_root = batch_root / "exp-outputs"
    imagize_root = batch_root / "imagize"
    video_root = batch_root / "videos"
    for i in range(spec.n_runs):
        er = f"c1-exp0/template_run{i}_output/output/networks"
        assert (output_root / er).is_dir(), f"Directory {output_root / er} missing"
        png_files = list((imagize_root / er).glob("*.png"))
        assert png_files, f"No PNGs in {imagize_root / er}"
        # Every run must produce a video.
        video_file = video_root / er / "networks.mp4"
        assert video_file.is_file(), f"Video {video_file} does not exist"


# ---------------------------------------------------------------------------
# CORE — bivariate batch criteria (2D experiment cross-product).
#
# These exercise the framework's handling of bivariate batch criteria. The
# per-engine coupling (which batch-criteria pairs, cardinalities, and
# controllers to drive) lives in each engine's ``spec.bivar`` (a BivarSpec);
# the 2D expected-file structure lives in ``spec.bivar.stages``. Sessions are
# parametrized over ``engines.BIVAR_ENGINES`` (engines with a populated
# ``bivar`` spec)
# ---------------------------------------------------------------------------
_BIVAR_IDS = [e.name for e in engines.BIVAR_ENGINES]


def _bivar_batch_root(session, spec, bc_pair, controller=None):
    """Batch root for an ordered pair of batch criteria, for any engine."""
    leaf = batchroot.ExpRootLeaf(bc=list(bc_pair), template_stem=spec.template_stem)
    return batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project=spec.project,
        controller=controller or spec.controller,
        leaf=leaf,
        scenario=spec.scenario,
    ).to_path()


def _bivar_cmd(
    session, spec, bc_pair, *stages, controller=None, center=None, spread=None
):
    """Build a bivar SIERRA command from the spec. Engine-specific flags (e.g.
    ARGoS ``--physics-n-engines``) come from ``spec.base_flags`` via the base
    command, NOT inline here, which is what keeps this engine-agnostic."""
    cmd = SierraCommand.from_base(session.env[spec.base_cmd_env].split())
    cmd.set_multi("--batch-criteria", bc_pair)

    if controller is not None:
        cmd = cmd.set("--controller", controller)
    if center is not None:
        cmd = cmd.set("--center", center)
    if spread is not None:
        cmd = cmd.set("--spread", spread)
    return cmd.pipeline(*stages).render()


@nox.session(python=env.VERSIONS, tags=["smoke", "core", "presence", "grpb"])
@nox.parametrize("engine", engines.BIVAR_ENGINES, ids=_BIVAR_IDS)
@env.session_setup
@env.session_teardown
def core_stage1_bivar(session, engine):
    """Stage-1 bivariate inputs, checked in BOTH batch-criteria orderings.

    The two orderings swap the cardinalities, exercising that the experiment
    grid is generated correctly regardless of axis order.
    """
    for bc_pair, card0, card1 in engine.bivar.stage1_orderings:
        env.reset_root(session)
        batch_root = _bivar_batch_root(session, engine, bc_pair)
        session.run(*_bivar_cmd(session, engine, bc_pair, 1), silent=True)
        verify.verify_bivar_stage(engine, 1, batch_root, card0, card1, max_tier=1)


@nox.session(python=env.VERSIONS, tags=["smoke", "core", "presence", "grpb"])
@nox.parametrize("engine", engines.BIVAR_ENGINES, ids=_BIVAR_IDS)
@env.session_setup
@env.session_teardown
def core_stage2_bivar(session, engine):
    """Stage-2 bivariate run outputs exist across the grid."""
    bc_pair, card0, card1 = engine.bivar.stage23
    batch_root = _bivar_batch_root(session, engine, bc_pair)
    session.run(*_bivar_cmd(session, engine, bc_pair, 1, 2), silent=True)
    verify.verify_bivar_stage(engine, 2, batch_root, card0, card1, max_tier=1)


@nox.session(python=env.VERSIONS, tags=["smoke", "core", "presence", "grpb"])
@nox.parametrize("engine", engines.BIVAR_ENGINES, ids=_BIVAR_IDS)
@nox.parametrize("stats", _STATS_SWEEP, ids=[f"{c}-{s}" for c, s in _STATS_SWEEP])
@env.session_setup
@env.session_teardown
def core_stage3_bivar(session, stats, engine):
    """Stage-3 bivariate statistics across the center/spread sweep."""
    center, spread = stats
    bc_pair, card0, card1 = engine.bivar.stage23
    batch_root = _bivar_batch_root(session, engine, bc_pair)
    env.reset_root(session)
    session.run(
        *_bivar_cmd(session, engine, bc_pair, 1, 2, 3, center=center, spread=spread),
        silent=True,
    )
    verify.verify_bivar_stage(
        engine, 3, batch_root, card0, card1, max_tier=1, center=center, spread=spread
    )


@nox.session(python=env.VERSIONS, tags=["smoke", "core", "presence", "grpb"])
@nox.parametrize("engine", engines.BIVAR_ENGINES, ids=_BIVAR_IDS)
@nox.parametrize("stats", _STATS_SWEEP, ids=[f"{c}-{s}" for c, s in _STATS_SWEEP])
@env.session_setup
@env.session_teardown
def core_stage4_bivar(session, stats, engine):
    """Stage-4 bivariate graphs/CSVs across the sweep (alt controller)."""
    center, spread = stats
    bc_pair, card0, card1, controller = engine.bivar.stage4
    batch_root = _bivar_batch_root(session, engine, bc_pair, controller=controller)
    env.reset_root(session)
    session.run(
        *_bivar_cmd(
            session,
            engine,
            bc_pair,
            1,
            2,
            3,
            4,
            controller=controller,
            center=center,
            spread=spread,
        ),
        silent=True,
    )
    verify.verify_bivar_stage(
        engine, 4, batch_root, card0, card1, max_tier=1, center=center, spread=spread
    )


@nox.session(python=env.VERSIONS, tags=["smoke", "core", "presence", "grpb"])
@nox.parametrize("engine", engines.BIVAR_ENGINES, ids=_BIVAR_IDS)
@env.session_setup
@env.session_teardown
def core_stage5_bivar(session, engine):
    """Stage-5 cardinality-2 dispatch + primary-axis selection run to completion.

    Cardinality-2 dispatch and ``--plot-primary-axis`` are core batch-criteria
    concerns; detailed comparison-graph verification lives in the compare/graphs
    plugin smoke. Here we only assert both axes dispatch and produce output.
    """
    bc, controllers, cc_leaf_template = engine.bivar.stage5
    for controller in controllers:
        session.run(
            *_bivar_cmd(
                session, engine, tuple(bc.split()), 1, 2, 3, 4, controller=controller
            ),
            silent=True,
        )

    stage5 = (
        SierraCommand.from_base(session.env["COVERAGE_CMD"].split())
        .set("--sierra-root", str(session.env["SIERRA_ROOT"]))
        .set("--project", engine.project)
        .set("--n-runs", "4")
        .set("--bc-cardinality", "2")
        .set("--log-level", "TRACE")
        .set_multi("--batch-criteria", bc.split())
        .set("--compare", "compare.graphs")
        .set("--across", "controllers")
        .set("--spread", "conf95")
        .set("--things", ",".join(controllers))
        .pipeline(5)
    )

    root = pathlib.Path(session.env["SIERRA_ROOT"]) / engine.project
    cc_leaf = cc_leaf_template.format(c0=controllers[0], c1=controllers[1])
    cc_graph_root = root / cc_leaf
    cc_csv_root = root / cc_leaf.replace("-cc-graphs", "-cc-csvs")

    for axis in (0, 1):
        for d in (cc_csv_root, cc_graph_root):
            if d.exists():
                shutil.rmtree(d)
        cmd = stage5.set("--plot-primary-axis", str(axis)).render()
        session.run(*cmd, silent=True)
        assert cc_graph_root.is_dir(), f"{cc_graph_root} not created (axis={axis})"
        assert any(cc_graph_root.iterdir()), f"{cc_graph_root} empty (axis={axis})"
