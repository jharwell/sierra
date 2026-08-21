#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Smoke tests for the ``compare.graphs`` stage-5 plugin.

These exercise the *plugin functionality* -- collation of inter-controller and
inter-scenario comparison CSVs/graphs, model collation/overlay, and custom
legends. Verification that SIERRA core correctly dispatches stage 5 for
univariate vs. bivariate batch criteria lives in ``core.py``; here we assume
dispatch works and check the artifacts the plugin produces.

Each session runs its own stages 1-4 to generate the data it compares, so the
sessions are independent (and correspondingly heavy).
"""

# Core packages
import shutil

# 3rd party packages
import nox

# Project packages
from tests._framework import comparisons, engines, verify
from tests._framework import env as fwenv
from tests._framework.command import SierraCommand
from sierra.core import config

_JSONSIM = engines.BY_NAME["jsonsim"]

#: Univariate criteria for the stage 1-4 data-generation runs (cardinality 5).
_UNIVAR_BC = _JSONSIM.batch_criteria  # "max_speed.1.9.C5"
#: Bivariate criteria pair for the bivar comparison.
_BIVAR_BC = list(_JSONSIM.bivar.stage23[0])

#: The center/spread combos the univar comparisons render. We don't sweep all
# of them because that's covered in regression. We just sweep SOME, so that we
# can verify that everything works.
_UNIVAR_STATS = [
    ("mean", "bw"),
    ("median", "iqr"),
]


def _stage5_base(session, cardinality: int) -> SierraCommand:
    """Base stage-5 command as a SierraCommand (pipeline 5, given cardinality)."""
    return (
        SierraCommand.from_base(session.env["COVERAGE_CMD"].split())
        .set("--sierra-root", str(session.env["SIERRA_ROOT"]))
        .set("--project", _JSONSIM.project)
        .set("--n-runs", str(_JSONSIM.n_runs))
        .set("--bc-cardinality", str(cardinality))
        .set("--log-level", "TRACE")
        .pipeline(5)
    )


def _run_stage1234(session, scenario, controllers, center, spread, bc=None, proc=None):
    """Run stages 1-4 for the given controllers in a single scenario.

    ``bc`` defaults to the univariate criteria; pass a list for bivariate.
    ``proc`` is an optional list of ``proc.*`` plugin names for --proc.
    """
    bc = bc if bc is not None else _UNIVAR_BC
    for c in controllers:
        cmd = (
            SierraCommand.from_base(session.env[_JSONSIM.base_cmd_env].split())
            .set("--controller", c)
            .set("--center", center)
            .set("--spread", spread)
            .set("--scenario", scenario)
            .pipeline(1, 2, 3, 4)
        )
        if isinstance(bc, (list, tuple)):
            cmd.set_multi("--batch-criteria", list(bc))
        else:
            cmd.set("--batch-criteria", bc)
        if proc:
            cmd.set_multi("--proc", proc)
        session.run(*cmd.render(), silent=True)


# --- split generation (stat-independent) from processing (per stat) ---------
# --center/--spread only affect stage 3+; stages 1-2 (experiment generation +
# simulation execution) produce identical raw output regardless of how it's
# later summarized. So for a session that sweeps several center/spread combos we
# run stages 1-2 ONCE, then re-run only stages 3-4 (+5) per combo into the same
# root (re-running 3-4 into an existing root is supported). This turns an N-combo
# sweep from N full pipelines into 1 generation + N cheap processing passes.
def _run_stage12(session, scenario, controllers, bc=None, proc=None):
    """Generate + execute (stages 1-2) for controllers in one scenario.

    Stat-independent: no --center/--spread. Run once; feed many _run_stage34.
    """
    bc = bc if bc is not None else _UNIVAR_BC
    for c in controllers:
        cmd = (
            SierraCommand.from_base(session.env[_JSONSIM.base_cmd_env].split())
            .set("--controller", c)
            .set("--scenario", scenario)
            .pipeline(1, 2)
        )
        if isinstance(bc, (list, tuple)):
            cmd.set_multi("--batch-criteria", list(bc))
        else:
            cmd.set("--batch-criteria", bc)
        if proc:
            cmd.set_multi("--proc", proc)
        session.run(*cmd.render(), silent=True)


def _run_stage34(session, scenario, controllers, center, spread, bc=None, proc=None):
    """Process (stages 3-4) for one center/spread over already-generated data.

    Assumes _run_stage12 has been run for the same controllers/scenario/bc into
    this session's root.
    """
    bc = bc if bc is not None else _UNIVAR_BC
    for c in controllers:
        cmd = (
            SierraCommand.from_base(session.env[_JSONSIM.base_cmd_env].split())
            .set("--controller", c)
            .set("--center", center)
            .set("--spread", spread)
            .set("--scenario", scenario)
            .pipeline(3, 4)
        )
        if isinstance(bc, (list, tuple)):
            cmd.set_multi("--batch-criteria", list(bc))
        else:
            cmd.set("--batch-criteria", bc)
        if proc:
            cmd.set_multi("--proc", proc)
        session.run(*cmd.render(), silent=True)


@nox.session(python=fwenv.VERSIONS, tags=["smoke", "compare", "presence", "grpa"])
@fwenv.session_setup
@fwenv.session_teardown
def compare_cc_univar(session):
    """Inter-controller univariate comparison: collated CSVs + graphs.

    Generates the data once (stages 1-2), then renders + verifies every
    center/spread combo by re-running only stages 3-4 and stage 5 into the same
    root. The comparison CSVs are suffix-named per stat (.mean/.stddev/.q1...),
    so each combo's -cc-csvs/-cc-graphs is cleaned before its render and
    verified immediately after, keeping verify's exact file count per-combo.
    """
    controllers = comparisons.JS_CC_UNIVAR.things
    pair = "+".join(controllers)
    cc_csv_root = session.env["SIERRA_ROOT"] / f"{_JSONSIM.project}/{pair}-cc-csvs"
    cc_graph_root = session.env["SIERRA_ROOT"] / f"{_JSONSIM.project}/{pair}-cc-graphs"

    # Stat-independent generation, once.
    _run_stage12(session, comparisons.JS_CLEANROOM, controllers)

    for center, spread in _UNIVAR_STATS:
        # Process this stat combo over the already-generated data.
        _run_stage34(session, comparisons.JS_CLEANROOM, controllers, center, spread)

        # Clean the comparison outputs so verify counts THIS combo's files only.
        for d in (cc_csv_root, cc_graph_root):
            if d.exists():
                shutil.rmtree(d)

        stage5 = (
            _stage5_base(session, cardinality=1)
            .set("--batch-criteria", _UNIVAR_BC)
            .set("--compare", "compare.graphs")
            .set("--across", "controllers")
            .set("--center", center)
            .set("--spread", spread)
            .set("--things", ",".join(controllers))
        )
        session.run(*stage5.render(), silent=True)
        n_csvs = len(config.STATS[center].spreads[spread].exts) + (spread != "none")
        verify.verify_comparison(
            comparisons.JS_CC_UNIVAR, session.env["SIERRA_ROOT"], n_csvs
        )


@nox.session(python=fwenv.VERSIONS, tags=["smoke", "compare", "presence", "grpb"])
@fwenv.session_setup
@fwenv.session_teardown
def compare_sc_univar(session):
    """Inter-scenario univariate comparison: collated CSVs + graphs.

    Same shape as compare_cc_univar: generate both scenarios once (stages 1-2),
    then render + verify each center/spread combo via stages 3-4 + stage 5.
    """
    controllers = [comparisons.JS_KALMAN]
    scenarios = comparisons.JS_SC_UNIVAR.things
    pair = "+".join(scenarios)
    sc_csv_root = session.env["SIERRA_ROOT"] / f"{_JSONSIM.project}/{pair}-sc-csvs"
    sc_graph_root = session.env["SIERRA_ROOT"] / f"{_JSONSIM.project}/{pair}-sc-graphs"

    # Stat-independent generation, once, for both scenarios.
    _run_stage12(session, comparisons.JS_CLEANROOM, controllers)
    _run_stage12(session, comparisons.JS_FIELDTEST, controllers)

    for center, spread in _UNIVAR_STATS:
        _run_stage34(session, comparisons.JS_CLEANROOM, controllers, center, spread)
        _run_stage34(session, comparisons.JS_FIELDTEST, controllers, center, spread)

        for d in (sc_csv_root, sc_graph_root):
            if d.exists():
                shutil.rmtree(d)

        stage5 = (
            _stage5_base(session, cardinality=1)
            .set("--batch-criteria", _UNIVAR_BC)
            .set("--compare", "compare.graphs")
            .set("--across", "scenarios")
            .set("--controller", comparisons.JS_KALMAN)
            .set("--center", center)
            .set("--spread", spread)
            .set("--things", ",".join(scenarios))
        )
        session.run(*stage5.render(), silent=True)
        n_csvs = len(config.STATS[center].spreads[spread].exts) + (spread != "none")
        verify.verify_comparison(
            comparisons.JS_SC_UNIVAR, session.env["SIERRA_ROOT"], n_csvs
        )


@nox.session(python=fwenv.VERSIONS, tags=["smoke", "compare", "presence", "grpa"])
@fwenv.session_setup
@fwenv.session_teardown
def compare_cc_bivar(session):
    """Inter-controller bivariate comparison across both primary axes."""

    controllers = comparisons.JS_CC_BIVAR.things
    for controller in controllers:
        cmd = (
            SierraCommand.from_base(session.env[_JSONSIM.base_cmd_env].split())
            .set("--controller", controller)
            .set_multi("--batch-criteria", _BIVAR_BC)
            .pipeline(1, 2, 3, 4)
        )
        session.run(*cmd.render(), silent=True)

    stage5 = (
        _stage5_base(session, cardinality=2)
        .set_multi("--batch-criteria", _BIVAR_BC)
        .set("--across", "controllers")
        .set("--spread", "conf95")
        .set("--plot-log-yscale")
        .set("--plot-large-text")
        .set("--plot-transpose-graphs")
        .set("--things", (",").join(controllers))
    )
    pair = "+".join(controllers)
    cc_csv_root = session.env["SIERRA_ROOT"] / f"{_JSONSIM.project}/{pair}-cc-csvs"
    cc_graph_root = session.env["SIERRA_ROOT"] / f"{_JSONSIM.project}/{pair}-cc-graphs"

    for axis in [0, 1]:
        if cc_csv_root.exists():
            shutil.rmtree(cc_csv_root)
        if cc_graph_root.exists():
            shutil.rmtree(cc_graph_root)

        session.run(
            *stage5.copy().set("--plot-primary-axis", str(axis)).render(),
            silent=True,
        )
        verify.verify_comparison(
            comparisons.JS_CC_BIVAR, session.env["SIERRA_ROOT"], n_csvs=1
        )


@nox.session(python=fwenv.VERSIONS, tags=["smoke", "compare", "presence", "grpb"])
@fwenv.session_setup
@fwenv.session_teardown
def compare_models(session):
    """Model collation + overlay for inter-controller and inter-scenario
    comparisons.

    Runs stages 1-4 with the modelrunner so per-experiment model predictions
    exist, then runs both comparisons and checks that the collated
    ``-cc-models``/``-sc-models`` directories were produced.

    The inter-controller comparison requires each controller to have been run in
    exactly one scenario (otherwise the comparison is ambiguous), so we generate
    the first scenario and run the CC comparison before generating the second
    scenario needed for the SC comparison.
    """
    controllers = comparisons.JS_CC_MODELS.things
    scenarios = comparisons.JS_SC_MODELS.things

    proc = ["proc.statistics", "proc.collate", "proc.modelrunner"]

    center = "mean"
    spread = "none"
    # First scenario only: inter-controller comparison needs each controller on
    # exactly one scenario.
    _run_stage1234(
        session,
        comparisons.JS_CLEANROOM,
        controllers,
        center=center,
        spread=spread,
        proc=proc,
    )

    # Inter-controller comparison
    cc_cmd = (
        _stage5_base(session, cardinality=1)
        .set("--batch-criteria", _UNIVAR_BC)
        .set("--compare", "compare.graphs")
        .set("--across", "controllers")
        .set("--center", center)
        .set("--spread", spread)
        .set("--things", ",".join(controllers))
    )
    session.run(*cc_cmd.render(), silent=True)
    verify.verify_comparison(
        comparisons.JS_CC_MODELS, session.env["SIERRA_ROOT"], n_csvs=1
    )

    # Second scenario: inter-scenario comparison compares one controller across
    # the two scenarios.
    _run_stage1234(
        session,
        comparisons.JS_FIELDTEST,
        controllers,
        center=center,
        spread=spread,
        proc=proc,
    )

    sc_cmd = (
        _stage5_base(session, cardinality=1)
        .set("--batch-criteria", _UNIVAR_BC)
        .set("--compare", "compare.graphs")
        .set("--across", "scenarios")
        .set("--controller", comparisons.JS_KALMAN)
        .set("--spread", "none")
        .set("--things", ",".join(scenarios))
    )
    session.run(*sc_cmd.render(), silent=True)
    verify.verify_comparison(
        comparisons.JS_SC_MODELS, session.env["SIERRA_ROOT"], n_csvs=1
    )
