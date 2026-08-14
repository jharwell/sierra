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
from tests.smoke_tests import utils, setup
from sierra.core import config


def _stage5_base_cmd(session) -> str:
    return (
        f"{session.env['COVERAGE_CMD']} "
        f"--sierra-root={session.env['SIERRA_ROOT']} "
        f"--project=projects.sample_argos "
        f"--pipeline 5 "
        f"--n-runs=4 "
        f"--bc-cardinality=1 "
        f"--log-level=TRACE "
    )


def _run_stage1234(session, scenario: str, controllers, proc: str = ""):
    """Run stages 1-4 for the given controllers in a single scenario."""
    for c in controllers:
        sierra_cmd = (
            f"{session.env['ARGOS_BASE_CMD']} "
            f"--controller {c} "
            f"--physics-n-engines=1 "
            f"--batch-criteria population_size.Linear3.C3 "
            f"--pipeline 1 2 3 4 --center=mean --spread=bw "
            f"--scenario={scenario} "
            f"{proc}"
        )
        session.run(*sierra_cmd.split(), silent=True)


@nox.session(python=utils.versions, tags=["compare"])
@setup.session_setup
@setup.session_teardown
@nox.parametrize(
    "stats",
    [
        ("mean", "none"),
        ("mean", "conf95"),
        ("mean", "bw"),
        ("median", "iqr"),
    ],
)
def compare_cc_univar(session, stats):
    """Inter-controller univariate comparison: collated CSVs + graphs."""
    controllers = ["foraging.footbot_foraging", "foraging.footbot_foraging_slow"]

    _run_stage1234(session, "HighBlockCount.10x10x2", controllers)

    center = stats[0]
    spread = stats[1]
    stage5_cmd = (
        f"{_stage5_base_cmd(session)} "
        f"--batch-criteria population_size.Linear3.C3 "
        f"--compare compare.graphs "
        f"--across=controllers "
        f"--center={center} "
        f"--spread={spread} "
        f"--things=foraging.footbot_foraging,foraging.footbot_foraging_slow"
    )
    session.run(*stage5_cmd.split(), silent=True)
    utils.stage5_univar_check_cc_outputs(session, "argos", 16)


@nox.session(python=utils.versions, tags=["compare"])
@setup.session_setup
@setup.session_teardown
@nox.parametrize(
    "stats",
    [
        ("mean", "none"),
        ("mean", "conf95"),
        ("mean", "bw"),
        ("median", "iqr"),
    ],
)
def compare_sc_univar(session, stats):
    """Inter-scenario univariate comparison: collated CSVs + graphs."""
    controllers = ["foraging.footbot_foraging", "foraging.footbot_foraging_slow"]

    _run_stage1234(session, "HighBlockCount.10x10x2", controllers)
    _run_stage1234(session, "LowBlockCount.10x10x2", controllers)

    center = stats[0]
    spread = stats[1]
    stage5_cmd = (
        f"{_stage5_base_cmd(session)} "
        f"--batch-criteria population_size.Linear3.C3 "
        f"--compare compare.graphs "
        f"--across=scenarios "
        f"--controller=foraging.footbot_foraging "
        f"--center={center} "
        f"--spread={spread} "
        f"--things=LowBlockCount.10x10x2,HighBlockCount.10x10x2"
    )
    session.run(*stage5_cmd.split(), silent=True)
    utils.stage5_univar_check_cc_outputs(session, "argos", 16)


@nox.session(python=utils.versions, tags=["compare"])
@setup.session_setup
@setup.session_teardown
def compare_cc_bivar(session):
    """Inter-controller bivariate comparison across both primary axes."""
    controllers = ["foraging.footbot_foraging2", "foraging.footbot_foraging_slow2"]

    for controller in controllers:
        sierra_cmd = (
            f"{session.env['ARGOS_BASE_CMD']} "
            f"--controller {controller} "
            f"--physics-n-engines=1 "
            f"--batch-criteria population_size.Linear3.C3 max_speed.1.9.C5 "
            f"--pipeline 1 2 3 4"
        )
        session.run(*sierra_cmd.split(), silent=True)

    stage5_base_cmd = (
        f"{session.env['COVERAGE_CMD']} "
        f"--sierra-root={session.env['SIERRA_ROOT']} "
        f"--project=projects.sample_argos "
        f"--pipeline 5 "
        f"--n-runs=4 "
        f"--bc-cardinality=2 "
        f"--log-level=TRACE"
    )

    n_files = 2  # 1 graph per performance variable
    sierra_stage5_cmd = (
        f"{stage5_base_cmd} "
        f"--batch-criteria population_size.Linear3.C3 max_speed.1.9.C5 "
        f"--across=controllers "
        f"--spread=conf95 "
        f"--comparison-type=LNraw "
        f"--plot-log-yscale "
        f"--plot-large-text "
        f"--plot-transpose-graphs "
        f"--things=foraging.footbot_foraging2,foraging.footbot_foraging_slow2"
    )

    cc_csv_root = (
        session.env["SIERRA_ROOT"]
        / "projects.sample_argos/foraging.footbot_foraging2+foraging.footbot_foraging_slow2-cc-csvs"
    )
    cc_graph_root = (
        session.env["SIERRA_ROOT"]
        / "projects.sample_argos/foraging.footbot_foraging2+foraging.footbot_foraging_slow2-cc-graphs"
    )

    for axis in [0, 1]:
        if cc_csv_root.exists():
            shutil.rmtree(cc_csv_root)
        if cc_graph_root.exists():
            shutil.rmtree(cc_graph_root)

        session.run(
            *(f"{sierra_stage5_cmd} --plot-primary-axis={axis}").split(), silent=True
        )
        utils.stage5_bivar_check_cc_outputs(cc_graph_root, n_files)


@nox.session(python=utils.versions, tags=["compare"])
@setup.session_setup
@setup.session_teardown
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
    controllers = ["foraging.footbot_foraging", "foraging.footbot_foraging_slow"]
    proc = "--proc proc.statistics proc.collate proc.modelrunner"

    # First scenario only: inter-controller comparison needs each controller on
    # exactly one scenario.
    _run_stage1234(session, "HighBlockCount.10x10x2", controllers, proc=proc)

    # Inter-controller comparison
    cc_cmd = (
        f"{_stage5_base_cmd(session)} "
        f"--batch-criteria population_size.Linear3.C3 "
        f"--compare compare.graphs "
        f"--across=controllers "
        f"--spread=none "
        f"--things=foraging.footbot_foraging,foraging.footbot_foraging_slow"
    )
    session.run(*cc_cmd.split(), silent=True)
    utils.stage5_univar_check_cc_models_outputs(session, "argos")

    # Second scenario: inter-scenario comparison compares one controller across
    # the two scenarios.
    _run_stage1234(session, "LowBlockCount.10x10x2", controllers, proc=proc)

    sc_cmd = (
        f"{_stage5_base_cmd(session)} "
        f"--batch-criteria population_size.Linear3.C3 "
        f"--compare compare.graphs "
        f"--across=scenarios "
        f"--controller=foraging.footbot_foraging "
        f"--spread=none "
        f"--things=LowBlockCount.10x10x2,HighBlockCount.10x10x2"
    )
    session.run(*sc_cmd.split(), silent=True)
    utils.stage5_univar_check_sc_models_outputs(session, "argos")
