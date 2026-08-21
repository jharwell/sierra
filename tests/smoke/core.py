#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Core smoke sessions — plugin-agnostic framework behavior.

These test guarantees SIERRA's core makes to *every* plugin: env-var handling,
builtin batch-criteria, cmdline/rcfile resolution, parallelism paradigms, and
stage-5 cardinality dispatch. The tell that a session belongs here rather than
in ``smoke.py``'s plugin/conformance sections: it would still make sense if
every engine plugin were deleted. Where a session must drive *some* engine to
exercise core plumbing, it uses the lightest one that fits (the reference
engine, or ARGoS where physics/parallelism flags are the thing under test) and
asserts only core behavior, never engine-specific artifacts.
"""

# Core packages
import os
import pathlib
import shutil

# 3rd party packages
import nox

# Project packages
from tests._framework import engines, verify, env
from tests._framework.command import SierraCommand
from sierra.core import batchroot

_ARGOS = engines.ARGOS
_JSONSIM = engines.REFERENCE_ENGINE


def _batch_root(session, project, controller, scenario, bc, template_stem):
    leaf = batchroot.ExpRootLeaf(bc=[bc], template_stem=template_stem)
    return batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project=project,
        controller=controller,
        leaf=leaf,
        scenario=scenario,
    ).to_path()


@nox.session(python=env.VERSIONS, tags=["core", "presence", "smoke", "argos", "grpb"])
@env.session_setup
@env.session_teardown
def core_env_vars(session):
    """SIERRA_ARCH selects an arch-suffixed engine binary.

    Core concern: the framework resolves the engine executable through
    ``SIERRA_ARCH`` regardless of which engine plugin is loaded. This is one of
    the few core sessions that legitimately requires ARGoS: the mechanism under
    test (arch-suffixing a compiled executable, argos3 -> argos3-fizzbuzz) only
    applies to a binary-backed engine. The lightweight pure-python engines run
    their sim as a script with no executable to arch-suffix, so this behavior
    cannot be exercised through them. The assertion is that the arch-suffixed run
    completes, not any ARGoS-specific artifact.
    """
    session.env["SIERRA_ARCH"] = "fizzbuzz"

    # Symlink an arch-suffixed argos3 so SIERRA_ARCH resolution has a target.
    bin_dir = pathlib.Path(session.env["ARGOS_INSTALL_PREFIX"]) / "bin"
    arch_link = bin_dir / "argos3-fizzbuzz"
    arch_target = bin_dir / "argos3"
    if arch_link.exists():
        arch_link.unlink()
    arch_link.symlink_to(arch_target)

    cmd = (
        SierraCommand.from_base(session.env["ARGOS_BASE_CMD"].split())
        .set("--physics-n-engines", "1")
        .set("--batch-criteria", "population_size.Linear3.C3")
        .pipeline(1, 2)
        .render()
    )
    session.run(*cmd, silent=True)


@nox.session(python=env.VERSIONS, tags=["core", "presence", "smoke", "grpa"])
@env.session_setup
@env.session_teardown
def core_builtin_bc(session):
    """Builtin (engine-independent) batch criteria expand into c1-exp{i} dirs.

    ``builtin.MonteCarlo`` is a core batch-criteria: it must produce the
    experiment directory structure regardless of which engine consumes it. Uses
    the lightweight reference engine (jsonsim) since the criteria, not the
    engine, is under test.
    """
    bc = "builtin.MonteCarlo.C5"
    batch_root = _batch_root(
        session,
        project=_JSONSIM.project,
        controller=_JSONSIM.controller,
        scenario=_JSONSIM.scenario,
        bc=bc,
        template_stem=_JSONSIM.template_stem,
    )
    input_root = batch_root / "exp-inputs"

    base = SierraCommand.from_base(session.env[_JSONSIM.base_cmd_env].split()).set(
        "--batch-criteria", bc
    )

    session.run(*base.pipeline(1).render(), silent=True)

    # Core assertion: cardinality-5 criteria yields 5 experiment dirs.
    for i in range(5):
        input_dir = input_root / f"c1-exp{i}"
        assert input_dir.is_dir(), f"Directory {input_dir} not found"

    # Remainder of the pipeline runs to completion off the builtin criteria.
    session.run(*base.pipeline(2, 3, 4).render(), silent=True)


@nox.session(python=env.VERSIONS, tags=["core", "presence", "smoke", "grpa"])
@env.session_setup
@env.session_teardown
def core_cmdline_opts(session):
    """Cmdline plotting flags, --version, and rcfile precedence.

    All core: these are framework-level CLI behaviors independent of any engine.
    Rcfile scratch lives under ``SIERRA_SCRATCH`` (a per-session temp dir).
    """
    scratch = pathlib.Path(session.env["SIERRA_SCRATCH"])
    home = pathlib.Path.home()

    base = SierraCommand.from_base(session.env[_JSONSIM.base_cmd_env].split()).set(
        "--batch-criteria", _JSONSIM.batch_criteria
    )

    # Processing + plotting flags across stages. Each variant forks from base
    # via copy() so its flags don't leak into the next command.
    session.run(
        *base.copy().pipeline(1, 2, 3).set("--processing-parallelism", "1").render(),
        silent=True,
    )
    for flag in (
        "--plot-log-xscale",
        "--plot-enumerated-xscale",
        "--plot-large-text",
    ):
        session.run(*base.copy().pipeline(4).set(flag).render(), silent=True)
    session.run(
        *base.copy()
        .pipeline(4)
        .set("--plot-log-yscale")
        .set("--processing-parallelism", "1")
        .render(),
        silent=True,
    )

    shutil.rmtree(session.env["SIERRA_ROOT"])

    # --version short-circuits the pipeline.
    session.run(*base.copy().set("--version").render(), silent=True)

    # --- rcfile precedence -------------------------------------------------
    # The base command already sets --sierra-root; an rcfile pointing elsewhere
    # must be OVERRIDDEN by the explicit cmdline flag. Then, with the flag
    # removed, the rcfile (via --rcfile, then SIERRA_RCFILE, then ~/.sierrarc)
    # must take effect.
    #
    # These check only WHERE --sierra-root resolves from (which root dir gets
    # created), which is a stage-1 action -- so run --pipeline 1 rather than the
    # full sim pipeline. Cuts three ~63s full runs to ~5s each.
    rcfile = scratch / "sierrarc"
    rcfile.write_text("--sierra-root=~/test2")

    for d in ("test", "test2"):
        if (home / d).exists():
            shutil.rmtree(home / d)

    # cmdline --sierra-root (in base) wins over rcfile's ~/test2
    session.run(
        *base.copy().set("--rcfile", str(rcfile)).pipeline(1).render(), silent=True
    )
    assert not (home / "test").is_dir(), "cmdline --sierra-root should win over rcfile"

    # Drop the explicit --sierra-root so the rcfile's value is used instead.
    base_no_root = base.copy().remove("--sierra-root").remove("--rcfile").pipeline(1)

    session.env["SIERRA_RCFILE"] = str(rcfile)
    session.run(*base_no_root.render(), silent=True)
    assert (home / "test2").is_dir(), "SIERRA_RCFILE rcfile value not applied"
    shutil.rmtree(home / "test2")

    del session.env["SIERRA_RCFILE"]
    shutil.copy(rcfile, home / ".sierrarc")
    session.run(*base_no_root.render(), silent=True)
    assert (home / "test2").is_dir(), "~/.sierrarc value not applied"

    for d in ("test", "test2"):
        if (home / d).exists():
            shutil.rmtree(home / d)
    (home / ".sierrarc").unlink()


@nox.session(python=env.VERSIONS, tags=["core", "presence", "smoke", "grpb"])
@env.session_setup
@env.session_teardown
def core_parallelism(session):
    """Execution-parallelism paradigm controls commands.txt placement.

    Core concern: ``--exec-parallelism-paradigm=per-batch`` must NOT emit
    per-experiment ``commands.txt`` files (per-exp does). That presence/absence
    is paradigm-dependent, so it can't live in the static engine manifest and is
    asserted inline here.
    """
    bc = _JSONSIM.batch_criteria
    batch_root = _batch_root(
        session,
        project=_JSONSIM.project,
        controller=_JSONSIM.controller,
        scenario="cleanroom",
        bc=bc,
        template_stem=_JSONSIM.template_stem,
    )
    input_root = batch_root / "exp-inputs"

    base = (
        SierraCommand.from_base(session.env[_JSONSIM.base_cmd_env].split())
        .set("--batch-criteria", bc)
        .set("--controller", _JSONSIM.controller)
        .set("--exec-parallelism-paradigm", "per-batch")
    )

    session.run(*base.pipeline(1).render(), silent=True)

    # Paradigm-specific core assertion: per-batch emits NO commands.txt.
    assert not (
        input_root / "commands.txt"
    ).is_file(), "per-batch paradigm should not emit a batch-level commands.txt"
    for i in range(_JSONSIM.cardinality):
        f = input_root / f"c1-exp{i}" / "commands.txt"
        assert (
            not f.is_file()
        ), f"per-batch paradigm should not emit {f} (that is per-exp behavior)"

    # Standard stage-1 input structure, from the manifest (no per-engine ladder).
    verify.verify_stage(_JSONSIM, 1, batch_root, max_tier=1)

    session.run(*base.pipeline(2).render(), silent=True)
    verify.verify_stage(_JSONSIM, 2, batch_root, max_tier=1)


@nox.session(python=env.VERSIONS, tags=["core", "presence", "smoke", "grpa"])
@env.session_setup
@env.session_teardown
def core_stage5_univar(session):
    """Stage-5 cardinality-1 dispatch runs end-to-end.

    Core concern: cardinality dispatch and pipeline plumbing. Detailed
    verification of the comparison artifacts (CSV/graph/model counts, legends)
    lives in ``tests/smoke/plugin/compare/graphs.py``; here we assert only that
    dispatch produced the comparison output tree.
    """
    controllers = ["signal.kalman", "signal.lowpass"]

    # Generate stage 1-4 data for both controllers in one scenario.
    for c in controllers:
        cmd = (
            SierraCommand.from_base(session.env[_JSONSIM.base_cmd_env].split())
            .set("--controller", c)
            .set("--batch-criteria", _JSONSIM.batch_criteria)
            .set("--spread", "bw")
            .set("--scenario", "cleanroom")
            .pipeline(1, 2, 3, 4)
            .render()
        )
        session.run(*cmd, silent=True)

    # A single univariate comparison confirms cardinality-1 dispatch + stage-5
    # completion.
    stage5 = (
        SierraCommand.from_base(session.env["COVERAGE_CMD"].split())
        .set("--sierra-root", str(session.env["SIERRA_ROOT"]))
        .set("--project", _JSONSIM.project)
        .set("--n-runs", str(_JSONSIM.n_runs))
        .set("--bc-cardinality", "1")
        .set("--log-level", "TRACE")
        .set("--batch-criteria", _JSONSIM.batch_criteria)
        .set("--compare", "compare.graphs")
        .set("--across", "controllers")
        .set("--spread", "none")
        .set("--things", ",".join(controllers))
        .pipeline(5)
        .render()
    )
    session.run(*stage5, silent=True)

    cc_graph_root = (
        pathlib.Path(session.env["SIERRA_ROOT"])
        / _JSONSIM.project
        / "signal.kalman+signal.lowpass-cc-graphs"
    )
    assert cc_graph_root.is_dir(), f"{cc_graph_root} not created by stage 5"
    assert any(cc_graph_root.iterdir()), f"{cc_graph_root} is empty"
