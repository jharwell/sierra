#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Single environment-resolution layer."""

# Core packages
import functools
import os
import pathlib
import shutil
import tempfile
import typing as tp

VERSIONS = ["3.9", "3.12"]


def _resolve_roots():
    """One place that knows local-vs-CI paths.

    Get the root of (a) where ARGoS was installed and (b) where the sample
    project repo lives.

    """
    if "GITHUB_ACTIONS" in os.environ:
        argos_prefix = pathlib.Path("/usr/local")
        sample_root = (
            pathlib.Path(os.environ["GITHUB_WORKSPACE"]) / "sierra-sample-project"
        )
    else:
        argos_prefix = pathlib.Path(
            os.environ.get("ARGOS_INSTALL_PREFIX", pathlib.Path.home() / ".local")
        )
        sample_root = pathlib.Path(
            os.environ.get(
                "SIERRA_SAMPLE_ROOT",
                pathlib.Path.home() / "git/thesis/sierra-sample-project",
            )
        )
    return argos_prefix, sample_root


def sample_project_root() -> pathlib.Path:
    """The sierra-sample-project root, resolved for local-vs-CI.

    Public accessor over ``_resolve_roots`` for callers (e.g. the noxfile's
    unit-test session) that only need the sample-project path and shouldn't
    re-derive the GITHUB_WORKSPACE-vs-HOME logic themselves.
    """
    _, sample_root = _resolve_roots()
    return sample_root


def _build_base_cmd(spec, coverage_cmd: str, sierra_root: str, sample_root: str) -> str:
    """Assemble one engine's base command from its EngineSpec.

    The structured fields (project/controller/scenario/n-runs/engine) are
    emitted here; the engine-specific tail comes from ``spec.base_flags``, with
    {sample_root}/{sierra_root} placeholders expanded. Returns a single
    space-joined string (the smoke sessions ``.split()`` it, same as before).

    """
    parts = [
        coverage_cmd,
        f"--sierra-root={sierra_root}",
        f"--project={spec.project}",
        f"--controller={spec.controller}",
        f"--scenario={spec.scenario}",
        f"--engine={spec.engine_module}",
        f"--n-runs={spec.n_runs}",
    ]
    for flag in spec.base_flags:
        parts.append(flag.format(sample_root=sample_root, sierra_root=sierra_root))
    return " ".join(parts)


def setup_env(session) -> None:
    argos_prefix, sample_root = _resolve_roots()

    # Scratch under a real temp dir, not literal /tmp/... paths.
    scratch = pathlib.Path(tempfile.mkdtemp(prefix="sierra-test-"))
    session.env["SIERRA_ROOT"] = scratch / "root"
    # A writable scratch dir for tests that need to drop transient files (e.g.
    # an rcfile), replacing hardcoded ``/tmp/tmpfile`` literals. Lives under the
    # per-session temp dir, so it is unique per session and cleaned with it.
    session.env["SIERRA_SCRATCH"] = str(scratch)
    session.env["ARGOS_INSTALL_PREFIX"] = str(argos_prefix)
    session.env["SIERRA_SAMPLE_ROOT"] = str(sample_root)

    # --- library + plugin search paths (needed for ARGoS/ROS to find plugins)
    argos_lib = argos_prefix / "lib/argos3"
    if "LD_LIBRARY_PATH" in os.environ:
        session.env["LD_LIBRARY_PATH"] = f"{os.environ['LD_LIBRARY_PATH']}:{argos_lib}"
    else:
        session.env["LD_LIBRARY_PATH"] = str(argos_lib)

    if "SIERRA_PLUGIN_PATH" in os.environ:
        session.env["SIERRA_PLUGIN_PATH"] = (
            f"{os.environ['SIERRA_PLUGIN_PATH']}:{sample_root}"
        )
    else:
        session.env["SIERRA_PLUGIN_PATH"] = str(sample_root)

    session.env["ARGOS_PLUGIN_PATH"] = f"{argos_lib}:{sample_root / 'argos/build'}"
    session.env["PARALLEL"] = "--env ARGOS_PLUGIN_PATH --env LD_LIBRARY_PATH"

    # --- ROS environment (per-session) ---------------------------------------
    # nox builds session.env fresh per session, so ROS must be sourced here, not
    # once at the CI-job level (that wouldn't survive into later sessions). We
    # source ROS in a bash subprocess, dump its environment, and lift it into
    # session.env so later session.run() calls (the sierra invocations) inherit
    # ROS_DISTRO/PATH/CMAKE_PREFIX_PATH/PYTHONPATH/LD_LIBRARY_PATH.
    #
    # Source the catkin WORKSPACE OVERLAY ($HOME/.local/setup.bash), NOT the base
    # distro: the overlay chains the base distro AND adds the compiled
    # sample-project packages (launch files, robot descriptions). The base distro
    # alone suffices for stage-1 generation but not stage-2 execution, where
    # roslaunch needs the sample project's launch files.
    #
    # No-op on images without ROS (e.g. ubuntu24.04), so only the ros slice pays.
    ros_overlay = pathlib.Path(os.path.expanduser("~/.local/setup.bash"))
    ros_bases = sorted(pathlib.Path("/opt/ros").glob("*/setup.bash"))
    ros_setup = ros_overlay if ros_overlay.exists() else (
        ros_bases[0] if ros_bases else None
    )
    if ros_setup is not None:
        dumped = session.run(
            "bash",
            "-c",
            f"source {ros_setup} && env -0",
            external=True,
            silent=True,
        )
        for entry in dumped.split("\0"):
            if not entry or "=" not in entry:
                continue
            key, _, value = entry.partition("=")
            # Merge the search paths this setup already composed above rather
            # than letting ROS clobber them; take ROS's value for everything
            # else (ROS_DISTRO, ROS_PACKAGE_PATH, CMAKE_PREFIX_PATH, etc.).
            if key in ("LD_LIBRARY_PATH",) and key in session.env:
                session.env[key] = f"{session.env[key]}:{value}"
            else:
                session.env[key] = value

    nodefile = scratch / "nodefile"
    nodefile.write_text("localhost\n")
    session.env["SIERRA_NODEFILE"] = str(nodefile)

    # Remove any existing SIERRA config so tests start clean.
    rcpath = pathlib.Path.home() / ".sierrarc"
    if rcpath.exists():
        rcpath.unlink()

    session.install("-e", ".")
    executable = session.run("which", "sierra", silent=True).strip()
    coverage_cmd = f"coverage run --debug=debug {executable}"
    session.env["COVERAGE_CMD"] = coverage_cmd

    # --- engine base commands, assembled from the specs (single source of truth)
    from tests._framework import engines

    for spec in engines.ALL_ENGINES:
        session.env[spec.base_cmd_env] = _build_base_cmd(
            spec,
            coverage_cmd,
            str(session.env["SIERRA_ROOT"]),
            str(sample_root),
        )


def reset_root(session) -> None:
    """Remove ``SIERRA_ROOT`` if it exists, so the next run starts clean."""
    root = pathlib.Path(session.env["SIERRA_ROOT"])
    if root.exists():
        shutil.rmtree(root)


def session_setup(func):
    @functools.wraps(func)
    def wrapper(session, *args, **kwargs):
        setup_env(session)
        reset_root(session)
        return func(session, *args, **kwargs)

    return wrapper


def session_teardown(func):
    @functools.wraps(func)
    def wrapper(session, *args, **kwargs):
        result = func(session, *args, **kwargs)
        reset_root(session)
        return result

    return wrapper


# ---------------------------------------------------------------------------
# Tiered sessions
# ---------------------------------------------------------------------------
# Depth is a selectable axis: CI runs `nox -t presence` on every PR (cheap,
# broad, no goldens), `nox -t shape` for row/column sanity, and `nox -t value`
# on release (golden compares). The three depth tags are EXCLUSIVE: a `value`
# session is not also selected by `-t presence`. Each depth maps to the
# ``max_tier`` the shared body passes to ``verify.verify_stage``.
#
# nox fixes ``tags`` per session and cannot vary them per parametrize-id, so a
# tiered behavior cannot be one parametrized session with per-tier tags. To keep
# depth tag-selectable WITHOUT duplicating any test logic, ``tiered`` registers
# one thin session per requested depth from a single shared body: the body is
# written once and receives ``max_tier`` as a keyword. The generated sessions
# are the only things that carry tags.
TIERS: tp.Mapping[str, int] = {"presence": 1, "shape": 2, "value": 3}


def tiered(*area_tags: str, tiers: tp.Sequence[str] = ("presence",)):
    """Decorate a body ``f(session, *, max_tier, **kw)`` to register one tagged
    nox session per depth in ``tiers``.

    ``area_tags`` are the non-depth tags (area/engine) every generated session
    carries; each session additionally carries its own depth tag, so the depth
    tags stay exclusive. ``session_setup``/``session_teardown`` are applied to
    every generated session, so bodies need not repeat them.

    The body is registered under ``{f.__name__}_{depth}`` (e.g.
    ``regression_stage3_value``). Callers that also need ``@nox.parametrize``
    (engine, stats) stack it on the BODY before ``tiered``; nox composes the
    parametrization across every generated depth session.

    Import nox lazily so this module stays importable by non-nox unit code.
    """
    import nox

    for depth in tiers:
        if depth not in TIERS:
            raise ValueError(f"unknown tier {depth!r}; valid: {sorted(TIERS)}")

    def register(f):
        for depth in tiers:
            max_tier = TIERS[depth]

            @functools.wraps(f)
            def body(session, *args, _max_tier=max_tier, **kwargs):
                return f(session, *args, max_tier=_max_tier, **kwargs)

            # Distinct qualname/name per depth so nox registers separate sessions.
            body.__name__ = f"{f.__name__}_{depth}"
            wrapped = session_setup(session_teardown(body))
            nox.session(python=VERSIONS, tags=[*area_tags, depth], name=body.__name__)(
                wrapped
            )
        # Return the original so any stacked decorators/refs still resolve.
        return f

    return register
