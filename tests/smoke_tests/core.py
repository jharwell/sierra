#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import sys
import os
import shutil
import typing as tp

# 3rd party packages
import nox

# Project packages
from tests.smoke_tests import setup, utils
from sierra.core import batchroot


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_env_vars(session):
    """Test environment variables usage."""

    # Generate batch root path
    bc = ["population_size.Linear3.C3"]
    template_stem = "turtlebot3"
    scenario = "OutdoorWorld.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_ros1robot",
        controller="turtlebot3.wander",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    input_root = batch_root / "exp-inputs/"

    # Test SIERRA_ARCH
    session.env["SIERRA_ARCH"] = "fizzbuzz"

    session.run("which", "argos3", external=True)

    # Create symlink for argos3
    os.makedirs(
        (session.env["ARGOS_INSTALL_PREFIX"] / "bin/argos3-fizzbuzz").name,
        exist_ok=True,
    )
    arch_link = session.env["ARGOS_INSTALL_PREFIX"] / "bin/argos3-fizzbuzz"
    arch_target = session.env["ARGOS_INSTALL_PREFIX"] / "bin/argos3"
    if arch_link.exists():
        arch_link.unlink()
    arch_link.symlink_to(arch_target)

    # Run SIERRA command

    sierra_cmd = f"{session.env['ARGOS_BASE_CMD']} --physics-n-engines=1 --batch-criteria population_size.Linear3.C3 --pipeline 1 2"

    session.run(*sierra_cmd.split(), silent=True)


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_builtin_bc(session):
    """Test builtin batch criteria."""

    # Generate batch root path for Monte Carlo
    bc = ["builtin.MonteCarlo.C5"]
    template_stem = "template"
    scenario = "scenario1"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_jsonsim",
        controller="default.default",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    input_root = batch_root / "exp-inputs/"

    # Run SIERRA with Monte Carlo batch criteria
    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} --batch-criteria builtin.MonteCarlo.C5"
    )
    session.run(*(f"{sierra_cmd} --pipeline 1").split(), silent=True)

    # Check directory structure
    for i in range(5):
        input_dir = input_root / f"c1-exp{i}"
        assert os.path.isdir(input_dir), f"Directory {input_dir} not found"

    # Run rest of pipeline
    session.run(*(f"{sierra_cmd} --pipeline 2 3 4").split(), silent=True)


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_cmdline_opts(session):
    """Test command line options."""

    # Base command for testing
    sierra_cmd = f"{session.env['ARGOS_BASE_CMD']} --physics-n-engines=1 --batch-criteria population_size.Linear3.C3"

    # Run pipeline stages
    session.run(
        *(f"{sierra_cmd} --pipeline 1 2 3 --processing-parallelism=1").split(),
        silent=True,
    )

    # Test plotting options
    session.run(*(f"{sierra_cmd} --pipeline 4 --plot-log-xscale").split(), silent=True)
    session.run(
        *(f"{sierra_cmd} --pipeline 4 --plot-enumerated-xscale").split(), silent=True
    )
    session.run(
        *(
            f"{sierra_cmd} --pipeline 4 --plot-log-yscale --processing-parallelism=1"
        ).split(),
        silent=True,
    )
    session.run(*(f"{sierra_cmd} --pipeline 4 --plot-large-text").split(), silent=True)

    # Clean up
    shutil.rmtree(session.env["SIERRA_ROOT"])

    # Check version
    session.run(*(f"{sierra_cmd} --version").split(), silent=True)

    # Create rcfile
    with pathlib.Path("/tmp/tmpfile").open(mode="w") as f:
        f.write("--sierra-root=~/test2")

    # Test cmdline override of rcfile
    home = pathlib.Path.home()

    for d in ["test", "test2"]:
        if (home / d).exists():
            shutil.rmtree(home / d)

    session.run(*(f"{sierra_cmd} --rcfile=/tmp/tmpfile").split(), silent=True)
    assert (home / "test").is_dir(), "Directory ~/test not found"
    shutil.rmtree(home / "test")

    sierra_cmd = sierra_cmd.replace(
        "--sierra-root=" + str(pathlib.Path.home() / "test"), ""
    )

    # Test environment variable for rcfile
    session.env["SIERRA_RCFILE"] = "/tmp/tmpfile"
    session.run(*sierra_cmd.split(), silent=True)
    assert (home / "test2").is_dir(), "Directory ~/test2 not found"

    shutil.rmtree(home / "test2")

    # Test ~/.sierrarc
    del session.env["SIERRA_RCFILE"]
    shutil.copy("/tmp/tmpfile", home / ".sierrarc")
    session.run(*sierra_cmd.split(), silent=True)
    assert (home / "test2").is_dir(), "Directory ~/test2 not found"

    for d in ["test", "test2"]:
        if (home / d).exists():
            shutil.rmtree(home / d)

    (home / ".sierrarc").unlink()
    pathlib.Path("/tmp/tmpfile").unlink()


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_parallelism(session):
    """Test parallelism features."""
    # Generate batch root path
    bc = ["population_size.Linear3.C3"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    input_root = batch_root / "exp-inputs"

    # Define SIERRA command
    cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--batch-criteria population_size.Linear3.C3 "
        f"--controller=foraging.footbot_foraging "
        f"--physics-n-engines=1 "
        f"--pipeline 1 "
        f"--exec-parallelism-paradigm=per-batch"
    )

    # Run SIERRA command for pipeline stage 1 and check outputs
    session.run(*cmd.split(), silent=True)
    utils.stage1_univar_check_outputs("argos", "per-batch", input_root, 3, 4)

    # Run SIERRA command for pipeline stage 2 and check outputs
    session.run(*(f"{cmd} --pipeline 2").split(), silent=True)
    utils.stage2_univar_check_outputs("argos", batch_root, 3, 4)


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_stage5_univar(session):
    """Test stage 5 univariate comparison."""

    criteria = ["population_size.Linear3.C3"]
    controllers = ["foraging.footbot_foraging", "foraging.footbot_foraging_slow"]
    stats = ["none", "conf95", "bw"]

    # Set up stage 5 base command
    stage5_base_cmd = (
        f"{session.env['COVERAGE_CMD']} "
        f"--sierra-root={session.env['SIERRA_ROOT']} "
        f"--project=projects.sample_argos "
        f"--pipeline 5 "
        f"--n-runs=4 "
        f"--bc-cardinality=1 "
        f"-plog-yscale "
        f"-plarge-text "
        f"-pprimary-axis=1 "
        f"--log-level=TRACE "
    )

    # Run experiments with both controllers
    for bc in criteria:
        for c in controllers:
            sierra_cmd = (
                f"{session.env['ARGOS_BASE_CMD']} "
                f"--controller {c} "
                f"--physics-n-engines=1 "
                f"--batch-criteria {bc} "
                f"--pipeline 1 2 3 4 --dist-stats=all "
                f"--scenario=HighBlockCount.10x10x2"
            )
            session.run(*sierra_cmd.split(), silent=True)

    # Compare controllers within the same scenario
    for stat in stats:
        stage5_cmd = (
            f"{stage5_base_cmd} "
            f"--batch-criteria population_size.Linear3.C3 "
            f"--compare compare.graphs "
            f"--across=controllers "
            f"--dist-stats={stat} "
            f"--things=foraging.footbot_foraging,foraging.footbot_foraging_slow"
        )
        session.run(*stage5_cmd.split(), silent=True)

        # Check outputs
        utils.stage5_univar_check_cc_outputs(session, "argos")

    # Run more experiments with both controllers for scenario comparison
    for bc in criteria:
        for c in controllers:
            sierra_cmd = (
                f"{session.env['ARGOS_BASE_CMD']} "
                f"--controller {c} "
                f"--physics-n-engines=1 "
                f"--batch-criteria {bc} "
                f"--pipeline 1 2 3 4 --dist-stats=all "
                f"--scenario=LowBlockCount.10x10x2"
            )
            session.run(*sierra_cmd.split(), silent=True)

    # Compare controller across scenarios
    for stat in stats:
        stage5_cmd = (
            f"{stage5_base_cmd} "
            f"--batch-criteria population_size.Linear3.C3 "
            f"--compare compare.graphs "
            f"--across=scenarios "
            f"--controller=foraging.footbot_foraging "
            f"--dist-stats={stat} "
            f"--things=LowBlockCount.10x10x2,HighBlockCount.10x10x2"
        )
        session.run(*stage5_cmd.split(), silent=True)

        # Check outputs
        utils.stage5_univar_check_cc_outputs(session, "argos")


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_stage1_bivar(session):
    """Test stage 1 bivariate batch criteria."""

    # Generate batch root paths
    bc = ["population_size.Linear3.C3", "max_speed.1.9.C5"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root1 = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    bc = ["max_speed.1.9.C5", "population_size.Linear3.C3"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root2 = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    input_root1 = batch_root1 / "exp-inputs/"
    input_root2 = batch_root2 / "exp-inputs/"

    # Run first test
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--batch-criteria population_size.Linear3.C3 max_speed.1.9.C5 "
        f"--controller=foraging.footbot_foraging "
        f"--physics-n-engines=1 "
        f"--pipeline 1"
    )
    session.run(*sierra_cmd.split(), silent=True)

    utils.stage1_bivar_check_outputs("argos", input_root1, 3, 5, 4)

    # Clean up for second test
    shutil.rmtree(session.env["SIERRA_ROOT"])

    # Run second test
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--batch-criteria max_speed.1.9.C5 population_size.Linear3.C3 "
        f"--controller=foraging.footbot_foraging "
        f"--physics-n-engines=1 "
        f"--pipeline 1"
    )
    session.run(*sierra_cmd.split(), silent=True)
    utils.stage1_bivar_check_outputs("argos", input_root2, 5, 3, 4)


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_stage2_bivar(session):
    """Test stage 2 bivariate batch criteria."""

    # Generate batch root path
    bc = ["population_size.Linear2.C2", "max_speed.1.9.C3"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root1 = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    output_root1 = batch_root1 / "exp-outputs/"

    # Define SIERRA command
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--controller=foraging.footbot_foraging "
        f"--batch-criteria population_size.Linear2.C2 max_speed.1.9.C3 "
        f"--physics-n-engines=1 "
        f"--pipeline 1 2"
    )

    # Run SIERRA command
    session.run(*sierra_cmd.split(), silent=True)

    # Check SIERRA directory structure
    for i in range(2):  # {0..1}
        for j in range(3):  # {0..2}
            dir_path = f"{output_root1}/c1-exp{i}+c2-exp{j}"
            assert os.path.isdir(dir_path), f"Directory {dir_path} does not exist"

    # Check stage2 generated files
    for i in range(2):  # {0..1}
        for j in range(3):  # {0..2}
            for run in range(4):  # {0..3}
                file_path = f"{output_root1}/c1-exp{i}+c2-exp{j}/template_run{run}_output/output/collected-data.csv"
                assert os.path.isfile(file_path), f"File {file_path} does not exist"


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_stage3_bivar(session):
    """Test stage 3 bivariate batch criteria."""

    # Generate batch root path
    bc = ["population_size.Linear2.C2", "max_speed.1.9.C3"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_argos",
        controller="foraging.footbot_foraging",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    # Define SIERRA command
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--batch-criteria population_size.Linear2.C2 max_speed.1.9.C3 "
        f"--controller=foraging.footbot_foraging "
        f"--physics-n-engines=1 "
        f"--pipeline 1 2 3"
    )

    # Define stat types to check
    none_stats = ["mean"]
    conf95_stats = ["mean", "stddev"]
    bw_stats = ["mean", "median", "whishi", "whislo", "q1", "q3", "cilo", "cihi"]

    # Run tests for each stats type

    # Test 1: none stats
    if session.env["SIERRA_ROOT"].exists():
        shutil.rmtree(session.env["SIERRA_ROOT"])

    session.run(*(f"{sierra_cmd} --dist-stats=none").split(), silent=True)
    utils.stage3_bivar_check_outputs("argos", batch_root, 2, 3, none_stats)

    # Test 2: conf95 stats
    if session.env["SIERRA_ROOT"].exists():
        shutil.rmtree(session.env["SIERRA_ROOT"])

    session.run(*(f"{sierra_cmd} --dist-stats=conf95").split(), silent=True)
    utils.stage3_bivar_check_outputs("argos", batch_root, 2, 3, conf95_stats)

    # Test 3: bw stats
    if session.env["SIERRA_ROOT"].exists():
        shutil.rmtree(session.env["SIERRA_ROOT"])

    session.run(*(f"{sierra_cmd} --dist-stats=bw").split(), silent=True)
    utils.stage3_bivar_check_outputs("argos", batch_root, 2, 3, bw_stats)


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_stage4_bivar(session):
    """Test stage 4 bivariate batch criteria."""
    # Define stat types to check
    none_stats = ["mean"]
    conf95_stats = ["mean", "stddev"]
    bw_stats = ["mean", "median", "whishi", "whislo", "q1", "q3", "cilo", "cihi"]

    # Define SIERRA command
    sierra_cmd = (
        f"{session.env['ARGOS_BASE_CMD']} "
        f"--controller=foraging.footbot_foraging2 "
        f"--physics-n-engines=1 "
        f"--batch-criteria population_size.Linear3.C3 max_speed.1.9.C3 "
        f"--pipeline 1 2 3 4"
    )

    # Generate batch root path
    bc = ["population_size.Linear3.C3", "max_speed.1.9.C3"]
    template_stem = "template"
    scenario = "LowBlockCount.10x10x2"
    leaf = batchroot.ExpRootLeaf(bc=bc, template_stem=template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=session.env["SIERRA_ROOT"],
        project="projects.sample_argos",
        controller="foraging.footbot_foraging2",
        leaf=leaf,
        scenario=scenario,
    ).to_path()

    # Test 1: none stats
    session.run(*(f"{sierra_cmd} --dist-stats=none").split(), silent=True)
    utils.stage4_bivar_check_outputs("argos", batch_root, 3, 3, none_stats)
    if session.env["SIERRA_ROOT"].exists():
        shutil.rmtree(session.env["SIERRA_ROOT"])

    # Test 2: conf95 stats
    session.run(*(f"{sierra_cmd} --dist-stats=conf95").split(), silent=True)
    utils.stage4_bivar_check_outputs("argos", batch_root, 3, 3, conf95_stats)
    if session.env["SIERRA_ROOT"].exists():
        shutil.rmtree(session.env["SIERRA_ROOT"])

    # Test 3: bw stats
    session.run(*(f"{sierra_cmd} --dist-stats=bw").split(), silent=True)
    utils.stage4_bivar_check_outputs("argos", batch_root, 3, 3, bw_stats)
    if session.env["SIERRA_ROOT"].exists():
        shutil.rmtree(session.env["SIERRA_ROOT"])

    # Test 4: all stats
    session.run(*(f"{sierra_cmd} --dist-stats=all").split(), silent=True)
    utils.stage4_bivar_check_outputs("argos", batch_root, 3, 3, bw_stats + conf95_stats)


@nox.session(python=utils.versions, tags=["core"])
@setup.session_setup
@setup.session_teardown
def core_stage5_bivar(session):
    """Test stage 5 bivariate comparison."""

    # Define controllers to test
    controllers = ["foraging.footbot_foraging2", "foraging.footbot_foraging_slow2"]

    # Run experiments with both controllers
    for controller in controllers:
        sierra_cmd = (
            f"{session.env['ARGOS_BASE_CMD']} "
            f"--controller {controller} "
            f"--physics-n-engines=1 "
            f"--batch-criteria population_size.Linear3.C3 max_speed.1.9.C5 "
            f"--pipeline 1 2 3 4"
        )
        session.run(*sierra_cmd.split(), silent=True)

    # Set up stage 5 base command
    stage5_base_cmd = (
        f"{session.env['COVERAGE_CMD']} "
        f"--sierra-root={session.env['SIERRA_ROOT']} "
        f"--project=projects.sample_argos "
        f"--pipeline 5 "
        f"--n-runs=4 "
        f"--bc-cardinality=2 "
        f"--log-level=TRACE"
    )

    # Define expected file counts and comparison types
    n_files = 2  # 1 graph per controller, 2 performance variables
    comps = ["LNraw"]

    # Run comparisons
    for i in range(1):  # {0..0}
        sierra_stage5_cmd = (
            f"{stage5_base_cmd} "
            f"--batch-criteria population_size.Linear3.C3 max_speed.1.9.C5 "
            f"--across=controllers "
            f"--dist-stats=conf95 "
            f"--comparison-type={comps[i]} "
            f"--plot-log-yscale "
            f"--plot-large-text "
            f"--plot-transpose-graphs "
            f"--things=foraging.footbot_foraging2,foraging.footbot_foraging_slow2"
        )

        # Define paths
        cc_csv_root = (
            session.env["SIERRA_ROOT"]
            / "projects.sample_argos/foraging.footbot_foraging2+foraging.footbot_foraging_slow2-cc-csvs"
        )
        cc_graph_root = (
            session.env["SIERRA_ROOT"]
            / "projects.sample_argos/foraging.footbot_foraging2+foraging.footbot_foraging_slow2-cc-graphs"
        )

        # Clean directories if they exist
        if cc_csv_root.exists():
            shutil.rmtree(cc_csv_root)
        if cc_graph_root.exists():
            shutil.rmtree(cc_graph_root)

        # Run with primary axis = 0
        session.run(
            *(f"{sierra_stage5_cmd} --plot-primary-axis=0").split(), silent=True
        )
        utils.stage5_bivar_check_cc_outputs(cc_graph_root, n_files)

        # Clean directories again
        if cc_csv_root.exists():
            shutil.rmtree(cc_csv_root)
        if cc_graph_root.exists():
            shutil.rmtree(cc_graph_root)

        # Run with primary axis = 1
        session.run(
            *(f"{sierra_stage5_cmd} --plot-primary-axis=1").split(), silent=True
        )
        utils.stage5_bivar_check_cc_outputs(cc_graph_root, n_files)
