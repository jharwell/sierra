#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import os
import shutil
import sys

# 3rd party packages
import nox

# Project packages
from sierra.core import batchroot
from tests.smoke_tests import utils, setup


@nox.session(python=utils.versions, tags=["jsonsim"])
@setup.session_setup
@setup.session_teardown
def jsonsim_stage1_univar(session):
    """Check that stage 1 outputs what it is supposed to."""
    # Get batch root path
    bc = ["max_speed.1.9.C5"]
    template_stem = "template"
    scenario = "scenario1"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_jsonsim",
        controller="default.default",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    input_root = batch_root / "exp-inputs"

    # Build and run command
    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria max_speed.1.9.C5 "
        f"--pipeline 1"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    utils.stage1_univar_check_outputs("jsonsim", "per-batch", input_root, 5, 4)


@nox.session(python=utils.versions, tags=["jsonsim"])
@setup.session_setup
@setup.session_teardown
def jsonsim_stage3_univar(session):
    """Check that stage 3 outputs what it is supposed to."""
    bc = ["max_speed.1.9.C5"]
    template_stem = "template"
    scenario = "scenario1"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_jsonsim",
        controller="default.default",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    # Build and run command
    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria max_speed.1.9.C5 "
        f"--pipeline 1 2 3"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check stage3 generated stuff
    utils.stage3_univar_check_outputs("jsonsim", batch_root, 5, ["mean"])
