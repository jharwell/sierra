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
def compression_sanity(session):
    """Check that the compress/decompress plugins work/don't crash."""
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

    output_root = batch_root / "exp-outputs"

    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria max_speed.1.9.C5 "
        f"--pipeline 1 2 3 "
        f"--exec-jobs-per-node 4 "
        f"--proc proc.statistics proc.collate proc.compress"
    )

    session.run(*sierra_cmd.split(), silent=True)

    # Check for compression outputs
    for exp in range(0, 5):
        for run in range(0, 4):
            path = output_root / f"c1-exp{exp}/template_run{run}_output/output.tar.gz"
            assert path.exists(), f"{path} does not exist"

    shutil.rmtree(session.env["SIERRA_ROOT"])

    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria max_speed.1.9.C5 "
        f"--pipeline 1 2 3 "
        f"--exec-jobs-per-node 4 "
        f"--proc proc.statistics proc.collate proc.compress "
        f"--compress-remove-after "
    )

    session.run(*sierra_cmd.split(), silent=True)

    # Check for compression outputs
    for exp in range(0, 5):
        for run in range(0, 4):
            path = output_root / f"c1-exp{exp}/template_run{run}_output/output.tag.gz"
            assert not path.exists(), f"{path} does not exist"

    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria max_speed.1.9.C5 "
        f"--pipeline 3 4 "
        f"--exec-jobs-per-node 4 "
        f"--proc proc.statistics proc.collate proc.decompress "
    )

    session.run(*sierra_cmd.split(), silent=True)

    utils.stage4_univar_check_outputs("jsonsim", batch_root, 5, {})
