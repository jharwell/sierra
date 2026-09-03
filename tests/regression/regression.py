#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Regression tests — shape (tier 2) and value (tier 3)."""

# Core packages
import pathlib

# 3rd party packages
import nox

# Project packages
from tests._framework import engines, verify, env
from tests._framework.command import SierraCommand
from sierra.core import batchroot

_HERE = pathlib.Path(__file__).parent
_GOLDENS = _HERE / "goldens"


def _run_full(session, spec, center, spread, *stages):
    stages = stages or (1, 2, 3)
    leaf = batchroot.ExpRootLeaf(
        bc=[spec.batch_criteria], template_stem=spec.template_stem
    )
    batch_root = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project=spec.project,
        controller=spec.controller,
        leaf=leaf,
        scenario=spec.scenario,
    ).to_path()

    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--batch-criteria", spec.batch_criteria)
        .set("--center", center)
        .set("--spread", spread)
        .pipeline(*stages)
        .render()
    )
    session.run(*cmd, silent=True)
    return batch_root


# ---------------------------------------------------------------------------------
# Tier 2 — shape. Cheap, no goldens. Runs on the lightweight reference engines.
# ---------------------------------------------------------------------------------
@nox.session(python=env.VERSIONS, tags=["regression", "shape"])
@nox.parametrize(
    "engine",
    [e for e in engines.ALL_ENGINES if e.lightweight and 3 in e.stages],
    ids=[e.name for e in engines.ALL_ENGINES if e.lightweight and 3 in e.stages],
)
@env.session_setup
@env.session_teardown
def regression_shape_stage3(session, engine):
    center, spread = "mean", "conf95"
    batch_root = _run_full(session, engine, center, spread)
    verify.verify_stage(engine, 3, batch_root, max_tier=2, center=center, spread=spread)


@nox.session(python=env.VERSIONS, tags=["regression", "shape"])
@nox.parametrize(
    "engine",
    [e for e in engines.ALL_ENGINES if e.lightweight and 4 in e.stages],
    ids=[e.name for e in engines.ALL_ENGINES if e.lightweight and 4 in e.stages],
)
@env.session_setup
@env.session_teardown
def regression_shape_stage4(session, engine):
    center, spread = "mean", "conf95"
    batch_root = _run_full(session, engine, center, spread, 1, 2, 3, 4)
    verify.verify_stage(engine, 4, batch_root, max_tier=2, center=center, spread=spread)


# --------------------------------------------------------------------------------
# Tier 3 — value. Expensive; golden compare across measures of center/spread.
# --------------------------------------------------------------------------------
@nox.session(python=env.VERSIONS, tags=["regression", "value"])
@nox.parametrize(
    "stats",
    [("mean", "conf95"), ("mean", "bw"), ("median", "iqr")],
    ids=["mean-conf95", "mean-bw", "median-iqr"],
)
@env.session_setup
@env.session_teardown
def regression_value_statistics(session, stats):
    center, spread = stats
    engine = engines.REFERENCE_ENGINE
    batch_root = _run_full(session, engine, center, spread)
    # Only entries whose manifest sets ``value_check`` are golden-compared; the
    # rest fall through to presence+shape automatically. Stat extensions resolve
    # from config.STATS for this center/spread.
    verify.verify_stage(
        engine,
        3,
        batch_root,
        max_tier=3,
        goldens_root=_GOLDENS / "statistics",
        center=center,
        spread=spread,
    )


# 2026-09-03 [JRH]: Only test with 3.12 because networkx on python 3.9 vs 3.12
# has some important differences which can't be overcome with pinning; once
# SIERRA moves to 3.10 this can go away.
@nox.session(python=["3.12"], tags=["regression", "value"])
@env.session_setup
@env.session_teardown
def regression_value_graphs(session, *_):
    """Blessed-PNG comparison for every generator in ``sierra.core.graphs``.

    Pass ``--bless`` (after ``--``) to (re)bless goldens instead of
    comparing; any other trailing args are forwarded to pytest.
    """
    posargs = list(session.posargs)
    if "--bless" in posargs:
        posargs.remove("--bless")
        mpl_args = [f"--mpl-generate-path={_GOLDENS}/graphs"]
    else:
        # Default to compare mode; allow the caller to override/add flags.
        mpl_args = ["--mpl"] if "--mpl" not in posargs else []

    # We use 'coverage run' instead of 'pytest' directly, because the latter
    # autocombines all coverage at reports it at the end of the session
    # into .coverage, which is not unique across CI jobs.
    session.run(
        "coverage",
        "run",
        "-m",
        "pytest",
        str(_HERE / "graphs/test_graphs.py"),
        *mpl_args,
        *posargs,
        silent=False,
        env={"SIERRA_REPO_ROOT": str(session.invoked_from)},
    )
