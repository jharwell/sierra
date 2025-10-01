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


@nox.session(python=utils.versions, tags=["argos"])
@setup.session_setup
@setup.session_teardown
def argos_physics_engines(session):
    """Check that you can use multiple physics engines and things don't crash."""
    # Define engines to test - smallest, largest, and one in between
    engines = [1, 16, 24]

    for n in engines:
        sierra_cmd = (
            f"{session.env['ARGOS_BASE_CMD']} "
            f"--controller=foraging.footbot_foraging "
            f"--batch-criteria population_size.Linear3.C3 "
            f"--physics-n-engines={n} "
            f"--pipeline 1 2"
        )

        # Clear sierra root directory
        if session.env["SIERRA_ROOT"].exists():
            shutil.rmtree(session.env["SIERRA_ROOT"])

        # Run the command
        session.run(*sierra_cmd.split(), silent=True)


@nox.session(python=utils.versions, tags=["argos"])
@setup.session_setup
@setup.session_teardown
def argos_stage1_univar(session):
    bc = ["population_size.Linear3.C3", "population_constant_density.1p0.I16.C3"]

    for criteria in bc:
        template_stem = "template"
        scenario = "LowBlockCount.10x10x2"
        leaf = batchroot.ExpRootLeaf(bc=[criteria], template_stem=template_stem)
        batch_root = batchroot.ExpRoot(
            sierra_root=f"{session.env['SIERRA_ROOT']}",
            project="projects.sample_argos",
            controller="foraging.footbot_foraging",
            scenario=scenario,
            leaf=leaf,
        ).to_path()

        input_root = batch_root / "exp-inputs"

        sierra_cmd = (
            f"{session.env['ARGOS_BASE_CMD']} "
            f"--batch-criteria {criteria} "
            f"--controller=foraging.footbot_foraging "
            f"--pipeline 1"
        )

        # Run the command
        session.run(*sierra_cmd.split(), silent=True)

        # Check SIERRA directory structure
        for i in range(3):
            exp_dir = input_root / f"c1-exp{i}"
            assert exp_dir.is_dir(), f"Directory {exp_dir} does not exist"

            # Check stage1 generated files
            assert (
                exp_dir / "commands.txt"
            ).is_file(), f"File commands.txt missing in {exp_dir}"
            assert (
                exp_dir / "exp_def.pkl"
            ).is_file(), f"File exp_def.pkl missing in {exp_dir}"
            assert (
                exp_dir / "seeds.pkl"
            ).is_file(), f"File seeds.pkl missing in {exp_dir}"

            for run in range(4):
                template_file = exp_dir / f"template_run{run}.argos"
                assert template_file.is_file(), f"File {template_file} missing"


@nox.session(python=utils.versions, tags=["argos"])
@setup.session_setup
@setup.session_teardown
@nox.parametrize("dist_stats", ["none", "conf95", "bw"])
def argos_stage3_univar(session, dist_stats):
    """Check that stage 3 outputs what it is supposed to."""
    # Define expected stats files based on dist_stats parameter
    stats_map = {
        "none": ["mean"],
        "conf95": ["mean", "stddev"],
        "bw": ["mean", "median", "whishi", "whislo", "q1", "q3", "cilo", "cihi"],
    }
    to_check = stats_map[dist_stats]

    # Get batch root path
    bc = ["population_size.Linear3.C3"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    # Build and run command
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--controller=foraging.footbot_foraging "
        f"--batch-criteria population_size.Linear3.C3 "
        f"--pipeline 1 2 3 "
        f"--dist-stats={dist_stats}"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check outputs
    utils.stage3_univar_check_outputs("argos", batch_root, 3, to_check)


@nox.session(python=utils.versions, tags=["argos"])
@setup.session_setup
@setup.session_teardown
@nox.parametrize(
    "bc", ["population_size.Linear3.C3", "population_variable_density.1p0.4p0.C4"]
)
@nox.parametrize("dist_stats", ["none", "conf95", "bw", "all"])
def argos_stage4_univar(session, bc, dist_stats):
    """Check that stage 4 outputs what it is supposed to."""
    # Define expected stats files based on dist_stats parameter
    stats_map = {
        "none": ["mean"],
        "conf95": ["mean", "stddev"],
        "bw": ["mean", "median", "whishi", "whislo", "q1", "q3", "cilo", "cihi"],
        "all": [
            "mean",
            "stddev",
            "median",
            "whishi",
            "whislo",
            "q1",
            "q3",
            "cilo",
            "cihi",
        ],
    }
    to_check = stats_map[dist_stats]

    # Get batch root path
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=[bc], template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    # Build and run command
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--controller=foraging.footbot_foraging "
        f"--batch-criteria {bc} "
        f"--pipeline 1 2 3 4 "
        f"--dist-stats={dist_stats}"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check outputs
    utils.stage4_univar_check_outputs("argos", batch_root, 3, to_check)


@nox.session(python=utils.versions, tags=["argos"])
@setup.session_setup
@setup.session_teardown
@nox.parametrize("camera_config", ["overhead", "sw", "sw+interp"])
def argos_vc(session, camera_config):
    """Visual capture test."""
    # Get batch root path
    bc = ["population_size.Linear1.C1"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    output_root = batch_root / "exp-outputs"
    video_root = batch_root / "videos"

    # Build and run command. Need prod.graphs for --exp-n-datapoints-factor in
    # the base command.
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--controller=foraging.footbot_foraging "
        f"--batch-criteria population_size.Linear1.C1 "
        f"--pipeline 1 2 3 4 "
        f"--prod prod.render prod.graphs "
        f"--engine-vc "
        f"--camera-config={camera_config}"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check SIERRA directory structure
    for i in range(4):
        frames_dir = output_root / f"c1-exp0/template_run{i}_output/frames"
        assert frames_dir.is_dir(), f"Directory {frames_dir} does not exist"

        # Check generated frames exist
        frames = list(frames_dir.glob("*"))
        assert len(frames) > 0, f"No frames found in {frames_dir}"

        # Check generated videos
        video_file = video_root / f"c1-exp0/template_run{i}_output.mp4"
        assert video_file.is_file(), f"Video file {video_file} does not exist"


@nox.session(python=utils.versions, tags=["argos"])
@setup.session_setup
@setup.session_teardown
def argos_imagize(session):
    """Imagize test."""
    # Get batch root path
    bc = ["population_size.Linear1.C1"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    output_root = batch_root / "exp-outputs"
    video_root = batch_root / "videos"
    imagize_root = batch_root / "imagize"

    # Build and run command
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--batch-criteria population_size.Linear1.C1 "
        f"--pipeline 1 2 3 4 "
        f"--proc proc.statistics proc.imagize proc.collate "
        f"--prod prod.render prod.graphs "
        f"--project-rendering "
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check SIERRA directory structure
    for i in range(4):
        floor_state_dir = (
            output_root / f"c1-exp0/template_run{i}_output/output/floor-state"
        )
        assert floor_state_dir.is_dir(), f"Directory {floor_state_dir} does not exist"

    # Check generated images exist
    png_files = list((imagize_root / "c1-exp0/floor-state").glob("*.png"))
    assert (
        len(png_files) > 0
    ), f"No PNG files found in {imagize_root}/c1-exp0/floor-state"

    # Check generated videos
    video_file = video_root / "c1-exp0/floor-state/floor-state.mp4"
    assert video_file.is_file(), f"Video file {video_file} does not exist"


@nox.session(python=utils.versions, tags=["argos"])
@setup.session_setup
@setup.session_teardown
def argos_cmdline(session):
    """Command line test."""
    # Get batch root path
    bc = ["population_size.Linear3.C3"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    input_root = batch_root / "exp-inputs"

    # Build and run command
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--batch-criteria population_size.Linear3.C3 "
        f"--n-agents=10 "
        f"--pipeline 1"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check that n-agents parameter was correctly applied
    for i in range(3):
        for run in range(4):
            template_file = input_root / f"c1-exp{i}/template_run{run}.argos"
            assert (
                template_file.is_file()
            ), f"Template file {template_file} does not exist"

            # Read file and check for quantity="10"
            content = template_file.read_text()
            assert (
                'quantity="10"' in content
            ), f'File {template_file} does not contain quantity="10"'
