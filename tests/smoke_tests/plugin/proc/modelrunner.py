#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages

# 3rd party packages
import nox

# Project packages
from sierra.core import batchroot
from tests.smoke_tests import utils, setup


@nox.session(python=utils.versions, tags=["proc"])
@setup.session_setup
@setup.session_teardown
def modelrunner_sanity(session):
    """Check that the modelrunner plugin works/doesn't crash."""
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

    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria max_speed.1.9.C5 "
        f"--pipeline 1 2 3 4 "
        f"--exec-jobs-per-node 4 "
        f"--proc proc.statistics proc.collate proc.modelrunner "
    )
    cardinality = 5

    output_root = batch_root / "exp-outputs"
    scratch_root = batch_root / "scratch"
    model_root = batch_root / "models"

    session.run(*sierra_cmd.split(), silent=True)
    utils.stage3_univar_check_outputs("jsonsim", batch_root, cardinality, {})

    # Check for model outputs
    for i in range(3):
        exp = model_root / f"c1-exp{i}"
        for ext in [".legend", ".model"]:
            path = (exp / "output1D").with_suffix(ext)
            assert path.exists(), f"{path} does not exist"

        for ext in [".legend", ".model"]:
            path = (model_root / "inter-exp/random-noise3-col2").with_suffix(ext)
            assert path.exists(), f"{path} does not exist"
