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


@nox.session(python=utils.versions, tags=["ros1gazebo"])
@setup.session_setup
@setup.session_teardown
def ros1gazebo_stage1_univar(session):
    """Check that stage 1 outputs what it is supposed to."""
    # Get batch root path
    bc = ["population_size.Linear3.C3"]
    template_stem = "turtlebot3_house"
    scenario = "HouseWorld.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_ros1gazebo",
        controller="turtlebot3.wander",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    input_root = batch_root / "exp-inputs"

    # Build and run command
    sierra_cmd = (
        f"{session.env['ROS1GAZEBO_BASE_CMD']} "
        f"--batch-criteria population_size.Linear3.C3 "
        f"--pipeline 1"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check outputs
    utils.stage1_univar_check_outputs("ros1gazebo", "per-exp", input_root, 3, 4)
