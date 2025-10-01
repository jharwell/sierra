#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import os
import shutil
import sys
import pathlib

# 3rd party packages
import nox

# Project packages
from sierra.core import batchroot
from tests.smoke_tests import utils, setup


@nox.session(python=utils.versions, tags=["ros1robot"])
@setup.session_setup
@setup.session_teardown
@nox.parametrize("bc", ["population_size.Linear3.C3", "population_size.Log8"])
def ros1robot_stage1_univar(session, bc):
    """Check that stage 1 outputs what it is supposed to."""

    template_stem = "turtlebot3"
    scenario = "OutdoorWorld.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=[bc], template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_ros1robot",
        controller="turtlebot3.wander",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    sierra_cmd = (
        f"{session.env['ROS1ROBOT_BASE_CMD']} "
        f"--batch-criteria {bc} "
        f"--pipeline 1"
    )

    session.run(*sierra_cmd.split())
    utils.stage1_univar_check_outputs(
        "ros1robot", "per-batch", batch_root / "exp-inputs", 3, 4
    )
