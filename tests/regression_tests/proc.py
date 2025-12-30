#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License Identifier: MIT
#

# Core packages
import pathlib
import typing as tp
import os
import subprocess

# 3rd party packages
import csv
import nox
import polars as pl
from polars.testing import assert_frame_equal

# Project packages
from tests.smoke_tests import utils, setup
from sierra.core import batchroot

versions = ["3.9", "3.12"]


@nox.session(python=utils.versions, tags=["jsonsim"])
@setup.session_setup
@setup.session_teardown
@nox.parametrize("stats", ["bw"])
def statistics_reg(session, stats):
    """Check that the statistics plugin outputs what it is supposed to by
    comparing against known good outputs when asked to compute statistics for
    95% confidence intervals.
    """
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
        f"--pipeline 1 2 3 "
        f"--dist-stats={stats}"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check stage3 generated stuff
    stats_map = {
        "conf95": ["mean", "stddev"],
        "bw": ["mean", "median", "whishi", "whislo", "q1", "q3", "cilo", "cihi"],
    }
    to_check = stats_map[stats]
    _stage3_univar_check_outputs_jsonsim(batch_root / "statistics", 5, stats, to_check)


def _stage3_univar_check_outputs_jsonsim(
    stat_root: pathlib.Path, cardinality: int, stats: str, to_check: list[str]
):
    current_dir = pathlib.Path.cwd()

    # Check stage3 generated statistics
    for i in range(0, cardinality):
        for stat in to_check:
            exp_dir = stat_root / f"c1-exp{i}"
            intraexp_items = [
                {
                    "path": exp_dir / f"output1D.{stat}",
                    "ref": current_dir
                    / f"tests/regression_tests/statistics-jsonsim-{stats}"
                    / exp_dir
                    / f"output1D.{stat}",
                },
                {
                    "path": exp_dir / f"output2D.{stat}",
                    "ref": current_dir
                    / f"tests/regression_tests/statistics-jsonsim-{stats}"
                    / f"c1-exp{i}/output2D.{stat}",
                },
                {
                    "path": exp_dir / f"subdir1/subdir2/output1D.{stat}",
                    "ref": current_dir
                    / f"tests/regression_tests/statistics-jsonsim-{stats}"
                    / f"c1-exp{i}/subdir1/subdir2/output1D.{stat}",
                },
                {
                    "path": exp_dir / f"subdir1/subdir2/output2D.{stat}",
                    "ref": current_dir
                    / f"tests/regression_tests/statistics-jsonsim-{stats}"
                    / f"c1-exp{i}/subdir1/subdir2/output2D.{stat}",
                },
                {
                    "path": exp_dir / f"subdir3/output1D.{stat}",
                    "ref": current_dir
                    / f"tests/regression_tests/statistics-jsonsim-{stats}"
                    / f"c1-exp{i}/subdir3/output1D.{stat}",
                },
                {
                    "path": exp_dir / f"subdir3/output2D.{stat}",
                    "ref": current_dir
                    / f"tests/regression_tests/statistics-jsonsim-{stats}"
                    / f"c1-exp{i}/subdir3/output2D.{stat}",
                },
            ]
            for item in intraexp_items:
                assert_frame_equal(
                    pl.read_csv(item["path"]),
                    pl.read_csv(item["ref"]),
                    check_column_order=False,
                )

            interexp_items = [
                {
                    "path": stat_root
                    / f"inter-exp/c1-exp{i}/subdir1/subdir2/output1D-col1.csv",
                    "ref": current_dir
                    / f"tests/regression_tests/statistics-jsonsim-{stats}/inter-exp/c1-exp{i}/subdir1/subdir2/output1D-col1.csv",
                },
                {
                    "path": stat_root
                    / f"inter-exp/c1-exp{i}/subdir3/output1D-col2.csv",
                    "ref": current_dir
                    / f"tests/regression_tests/statistics-jsonsim-{stats}/inter-exp/c1-exp{i}/subdir3/output1D-col2.csv",
                },
            ]

            for item in interexp_items:
                assert_frame_equal(
                    pl.read_csv(item["path"]),
                    pl.read_csv(item["ref"]),
                    check_column_order=False,
                )
