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


@nox.session(python=utils.versions, tags=["yamlsim"])
@setup.session_setup
@setup.session_teardown
def yamlsim_stage1_univar(session):
    """Check that stage 1 outputs what it is supposed to."""
    # Get batch root path
    bc = ["noise_floor.1.9.C5"]
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

    input_root = batch_root / "exp-inputs"

    # Build and run command
    sierra_cmd = (
        f"{session.env['YAMLSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria noise_floor.1.9.C5 "
        f"--pipeline 1"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    utils.stage1_univar_check_outputs("yamlsim", "per-batch", input_root, 5, 4)


@nox.session(python=utils.versions, tags=["yamlsim"])
@setup.session_setup
@setup.session_teardown
def yamlsim_stage3_univar(session):
    """Check that stage 3 outputs what it is supposed to."""
    bc = ["noise_floor.1.9.C5"]
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

    stat_root = batch_root / "statistics"

    # Build and run command
    sierra_cmd = (
        f"{session.env['YAMLSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria noise_floor.1.9.C5 "
        f"--pipeline 1 2 3"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check stage3 generated stuff
    utils.stage3_univar_check_outputs("yamlsim", batch_root, 5, [".mean"])


@nox.session(python=utils.versions, tags=["yamlsim"])
@setup.session_setup
@setup.session_teardown
def yamlsim_stage4_univar(session):
    """Check that stage 4 outputs what it is supposed to."""
    bc = ["noise_floor.1.9.C5"]
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

    graph_root = batch_root / "graphs"

    # Build base command
    sierra_cmd = (
        f"{session.env['YAMLSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria noise_floor.1.9.C5 "
    )

    # Run pipeline 1-3
    session.run(*f"{sierra_cmd} --pipeline 1 2 3".split(), silent=True)

    # Run pipeline 4 with matplotlib
    session.run(
        *f"{sierra_cmd} --pipeline 4 --graphs-backend=matplotlib".split(), silent=True
    )

    # Run pipeline 4 with bokeh
    session.run(
        *f"{sierra_cmd} --pipeline 4 --graphs-backend=bokeh".split(), silent=True
    )

    # Check stage4 generated stuff
    assert (
        graph_root / "inter-exp"
    ).is_dir(), f"Directory {graph_root}/inter-exp does not exist"

    # Check collated files
    interexp_files = [
        "SLN-random-noise-col1.png",
        "SLN-random-noise2-col2.png",
        "SM-random-noise3-col2.png",
        "SLN-random-noise-col1.html",
        "SLN-random-noise2-col2.html",
        "SM-random-noise3-col2.html",
    ]

    for file_name in interexp_files:
        file_path = graph_root / "inter-exp" / file_name
        assert file_path.is_file(), f"File {file_path} does not exist"

    # Check individual experiment files
    for i in range(5):
        exp_files = [
            "SLN-random-noise.png",
            "SLN-random-noise2.png",
            "SLN-random-noise3.png",
            "SLN-random-noise.html",
            "SLN-random-noise2.html",
            "SLN-random-noise3.html",
        ]

        for file_name in exp_files:
            file_path = graph_root / f"c1-exp{i}" / file_name
            assert file_path.is_file(), f"File {file_path} does not exist"


@nox.session(python=utils.versions, tags=["yamlsim"])
@setup.session_setup
@setup.session_teardown
def yamlsim_imagize(session):
    """Imagize test."""
    # Get batch root path
    bc = ["noise_floor.1.3.C3"]
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

    output_root = batch_root / "exp-outputs"
    video_root = batch_root / "videos"
    imagize_root = batch_root / "imagize"

    # Build and run command
    sierra_cmd = (
        f"{session.env['YAMLSIM_BASE_CMD']} "
        f"--bc noise_floor.1.3.C3 "
        f"--pipeline 1 2 3 4 "
        f"--proc proc.imagize "
        f"--prod prod.render "
        f"--imagize-no-stats "
        f"--project-rendering "
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    for i in range(4):
        graphs_dir = output_root / f"c1-exp0/template_run{i}_output/output/erdos_renyi"
        assert graphs_dir.is_dir(), f"Directory {graphs_dir} does not exist"

        # Check generated images exist
        png_files = list(
            (imagize_root / f"c1-exp0/template_run{i}_output/output/erdos_renyi").glob(
                "*.png"
            )
        )
        assert (
            len(png_files) > 0
        ), f"No PNG files found in {imagize_root}/c1-exp0/template_run{i}_output/output/erdos_renyi"

    # Check generated videos
    video_file = (
        video_root
        / f"c1-exp0/template_run{i}_output/output/erdos_renyi/erdos_renyi.mp4"
    )
    assert video_file.is_file(), f"Video file {video_file} does not exist"
