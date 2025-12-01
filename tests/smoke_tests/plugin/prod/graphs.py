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


@nox.session(python=utils.versions, tags=["graphs"])
@setup.session_setup
@setup.session_teardown
def graphs_backend(session):
    """Check that backend selection with the prod.graphs plugin works/doesn't
    crash for all supported graph types."""

    _graphs_backend_jsonsim(session)


def _graphs_backend_jsonsim(session):
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

    graph_root = batch_root / "graphs"

    # Build base command
    sierra_cmd = (
        f"{session.env['JSONSIM_BASE_CMD']} "
        f"--controller=default.default "
        f"--batch-criteria max_speed.1.9.C5 "
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
            "HM-output2D-1.png",
            "HM-output2D-2.png",
            "SLN-random-noise.html",
            "SLN-random-noise2.html",
            "SLN-random-noise3.html",
            "HM-output2D-1.html",
            "HM-output2D-2.html",
        ]

        for file_name in exp_files:
            file_path = graph_root / f"c1-exp{i}" / file_name
            assert file_path.is_file(), f"File {file_path} does not exist"


def graphs_backend_yamlsim(session):
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
    stat_root = batch_root / "statistics"
    graph_root = batch_root / "graphs"

    for i in range(5):
        interexp_csvs = [
            stat_root / f"inter-exp/c1-exp{i}/output1D-col1.csv",
            stat_root / f"inter-exp/c1-exp{i}/output1D-col2.csv",
        ]
        for f in interexp_csvs:
            assert f.is_file(), f"File {f} does not exist"

    # Check stage4 generated graphs
    for i in range(5):
        exp_files = [
            "SLN-random-noise.png",
            "CM-confusion-matrix.png",
            "SLN-random-noise.html",
            "CM-confusion-matrix.html",
        ]

        for file_name in exp_files:
            file_path = graph_root / f"c1-exp{i}" / file_name
            assert file_path.is_file(), f"File {file_path} does not exist"

    # Check interexp files
    interexp_files = [
        "SLN-random-noise-col1.png",
    ]

    for file_name in interexp_files:
        file_path = graph_root / "inter-exp" / file_name
        assert file_path.is_file(), f"File {file_path} does not exist"
