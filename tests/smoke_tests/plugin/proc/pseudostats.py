#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import shutil

# 3rd party packages
import nox

# Project packages
from sierra.core import batchroot
from tests.smoke_tests import utils, setup


@nox.session(python=utils.versions, tags=["proc"])
@setup.session_setup
@setup.session_teardown
def pseudostats_sanity(session):
    """Check that the pseudostats plugin works/doesn't crash."""
    bc = ["tolerance.1.5.C5"]
    template_stem = "template"
    scenario = "scenario1"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_yamlsim",
        controller="default.default",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    sierra_cmd = (
        f"{session.env['YAMLSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria tolerance.1.5.C5 "
        f"--pipeline 1 2 3 "
        f"--proc proc.pseudostats"
    )

    session.run(*sierra_cmd.split(), silent=True)

    # Check stat outputs. Not interexp items, because those aren't generated in
    # this test.
    utils._stage3_univar_check_outputs_yamlsim(
        batch_root / "statistics", 5, ["mean"], False
    )

    # Check raw outputs
    for exp in range(0, 5):
        for run in range(0, 4):
            path = batch_root / "exp-outputs" / f"c1-exp{exp}/template_run{run}_output/"
            assert (
                len(list(path.rglob("*.csv"))) > 0
            ), f"Raw data at {path} does not exist"

    shutil.rmtree(session.env["SIERRA_ROOT"])

    sierra_cmd = (
        f"{session.env['YAMLSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria tolerance.1.5.C5 "
        f"--pipeline 1 2 3 "
        f"--proc proc.pseudostats "
        f"--dataop=move "
    )

    session.run(*sierra_cmd.split(), silent=True)

    # Check stat outputs
    utils._stage3_univar_check_outputs_yamlsim(
        batch_root / "statistics", 5, ["mean"], False
    )

    # Check raw outputs
    for exp in range(0, 5):
        for run in range(0, 4):
            path = batch_root / "exp-outputs" / f"c1-exp{exp}/template_run{run}_output/"
            assert len(list(path.rglob("*.csv"))) == 0, f"Raw data at {path} exists"
