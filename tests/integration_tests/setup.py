#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import os

# 3rd party packages
import nox

# Project packages


def setup_env(session) -> None:
    session.install("-e", ".")  # same as 'pip3 install .'
    session.install("-e", ".[devel]")  # same as 'pip3 install .'

    # Default to local testing
    argos_install_prefix = pathlib.Path.home() / ".local"
    sierra_sample_root = pathlib.Path.home() / "git/thesis/sierra-sample-project"

    env = {}
    session.env["SIERRA_ROOT"] = pathlib.Path.home() / "test"

    if os.environ.get("GITHUB_ACTIONS") is not None:
        argos_install_prefix = pathlib.Path("/usr/local")
        sierra_sample_root = (
            pathlib.Path(os.getenv("GITHUB_WORKSPACE")) / "sierra-sample-project"
        )

    session.env["LD_LIBRARY_PATH"] = str(argos_install_prefix / "lib/argos3")

    session.env["ARGOS_INSTALL_PREFIX"] = argos_install_prefix
    session.env["SIERRA_SAMPLE_ROOT"] = sierra_sample_root
    session.env["SIERRA_PLUGIN_PATH"] = session.env["SIERRA_SAMPLE_ROOT"]
    session.env["ARGOS_PLUGIN_PATH"] = "{0}:{1}".format(
        session.env["ARGOS_INSTALL_PREFIX"] / "lib/argos3",
        session.env["SIERRA_SAMPLE_ROOT"] / "argos/build",
    )

    # Display which executables we're using
    session.run("which", "sierra-cli")
    session.run("which", "python3")

    # Create a nodefile for SIERRA
    with open("/tmp/nodefile", "w") as f:
        f.write(":\n")
    session.env["SIERRA_NODEFILE"] = "/tmp/nodefile"
    session.env["PARALLEL"] = "--env LD_LIBRARY_PATH"

    # Remove any existing SIERRA config
    rcpath = pathlib.Path("$HOME/.sierrarc")
    if rcpath.exists():
        rcpath.unlink()
