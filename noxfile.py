# Copyright 2022 John Harwell, All rights reserved.
#
#  SPDX-License-Identifier: MIT

# Core packages
import os
import pathlib

# 3rd party packages
import nox
import psutil

# Project packages
#
# Importing these modules registers their @nox.session functions with nox. The
# test suite was reorganized around tests/_framework (shared machinery) plus
# thin session modules; the old per-engine smoke files (argos/jsonsim/yamlsim/
# ros1robot/ros1gazebo) and the old utils/setup modules no longer exist -- their
# sessions are now the manifest/spec-driven sessions in tests.smoke.smoke.
from tests._framework import env
from tests.smoke import core, smoke
from tests.smoke.plugin import execenv
from tests.smoke.plugin.proc import modelrunner, compression, pseudostats
from tests.smoke.plugin.prod import graphs
from tests.smoke.plugin.compare import graphs as compare_graphs
from tests.regression import regression

# Silence "imported but unused" linters: these imports exist for their
# side effect of registering nox sessions.
__all__ = [
    "core",
    "smoke",
    "execenv",
    "modelrunner",
    "compression",
    "pseudostats",
    "graphs",
    "compare_graphs",
    "proc",
    "regression",
]

nox.options.default_venv_backend = "uv"
nox.options.reuse_venv = "always"


@nox.session(python=env.VERSIONS)
def analyze_misc(session):
    session.install(".")  # same as 'pip3 install .'
    session.install(".[dev]")  # same as 'pip3 install .[dev]'

    session.run(
        "xenon",
        "--max-absolute C",
        "--max-modules B",
        "--max-average A",
        "--no-assert sierra",
    )


@nox.session(python=env.VERSIONS)
def analyze_ruff(session):
    session.install(".")  # same as 'pip3 install .'
    session.install(".[dev]")  # same as 'pip3 install .[dev]'

    session.run("ruff", "check", "sierra")


# venv argument needed so the apt module can be found in the nox venv on linux
@nox.session(python=env.VERSIONS)
def analyze_pytype(session):
    session.install(".")  # same as 'pip3 install .'
    session.install(".[dev]")  # same as 'pip3 install .[dev]'

    cores = psutil.cpu_count()
    session.run(
        "pytype",
        f"-j {cores}",
        "-k",
        "--config pyproject.toml",
        "sierra",
        external=True,
    )


# venv argument needed so the apt module can be found in the nox venv on linux
@nox.session(python=env.VERSIONS)
def analyze_mypy(session):
    session.install(".")  # same as 'pip3 install .'
    session.install(".[dev]")  # same as 'pip3 install .[dev]'
    session.run("mypy", "--install-types", "--non-interactive", external=False)
    session.run("mypy", "--install-types")


@nox.session(python=env.VERSIONS)
def docs(session):
    session.install(".")  # same as 'pip3 install .'
    session.install(".[dev]")  # same as 'pip3 install .[dev]'

    # Check for imperative voice
    session.run("pydocstyle", "--select=D401", "sierra")

    # Check for summary line+body
    session.run("pydocstyle", "--select=D205", "sierra")

    # Check for punctuation on summary lines
    session.run("pydocstyle", "--select=D400", "sierra")


@nox.session(python=env.VERSIONS)
def unit_tests(session):
    session.install(".")  # same as 'pip3 install .'
    session.install(".[dev]")  # same as 'pip3 install .[dev]'

    # The sample project supplies the plugins the unit tests load. Resolve its
    # path through the framework's single local-vs-CI resolver rather than
    # re-deriving GITHUB_WORKSPACE/HOME here.
    session.env["SIERRA_PLUGIN_PATH"] = str(env.sample_project_root())

    # We use 'coverage run' instead of 'pytest' directly, because the latter
    # autocombines all coverage at reports it at the end of the session
    # into .coverage, which is not unique across CI jobs.
    session.run(
        "coverage",
        "run",
        "-m",
        "pytest",
        "tests/unit",
    )
