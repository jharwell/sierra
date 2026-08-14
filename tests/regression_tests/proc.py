#
# Copyright 2026 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#

# Core packages
import pathlib

# 3rd party packages
import nox
import polars as pl
from polars.testing import assert_frame_equal

# Project packages
from tests.smoke_tests import utils, setup
from sierra.core import batchroot, config

versions = ["3.9", "3.12"]


@nox.session(python=utils.versions, tags=["jsonsim"])
@setup.session_setup
@setup.session_teardown
@nox.parametrize(
    "stats",
    [
        ("mean", "conf95"),
        ("mean", "bw"),
        ("median", "iqr"),
    ],
)
def statistics_reg(session, stats):
    """Check that the statistics plugin outputs what it is supposed to by
    comparing against known good outputs when asked to compute statistics for
    all supported measures of central tendency and spread.
    """
    center = stats[0]
    spread = stats[1]
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
        f"--center={center} "
        f"--spread={spread}"
    )

    # Run the command
    session.run(*sierra_cmd.split(), silent=True)

    # Check stage3 generated stuff
    to_check = config.STATS[center].spreads[spread].exts
    _stage3_univar_check_outputs_jsonsim(
        batch_root / "statistics", 5, center, spread, to_check
    )


def _stage3_univar_check_outputs_jsonsim(
    stat_root: pathlib.Path,
    cardinality: int,
    center: str,
    spread: str,
    to_check: list[str],
):
    current_dir = pathlib.Path.cwd()
    ref_root = (
        current_dir / f"tests/regression_tests/statistics-jsonsim-{center}-{spread}"
    )

    # Statistics gathers exactly the raw outputs named by a graph 'src' in
    # graphs.yaml, matched exactly (rooted, path-qualified for nesting) -- the
    # same rule the collation plugin uses.
    intraexp_stems = [
        "output1D",
        "output2D",
        "subdir1/subdir2/output1D",
        "subdir3/output1D",
        "subdir3/output2D",
    ]

    # Check stage3 generated statistics
    for i in range(0, cardinality):
        exp_dir = stat_root / f"c1-exp{i}"
        for stat in to_check:
            for stem in intraexp_stems:
                path = exp_dir / f"{stem}.{stat}"
                ref = ref_root / f"c1-exp{i}" / f"{stem}.{stat}"
                assert_frame_equal(
                    pl.read_csv(path),
                    pl.read_csv(ref),
                    check_column_order=False,
                )

            # subdir1/subdir2/output2D must NOT be produced: no graph names it,
            # so exact matching (correctly) does not gather it.
            assert not (exp_dir / f"subdir1/subdir2/output2D.{stat}").exists(), (
                "subdir1/subdir2/output2D was gathered but no graph names it "
                "(substring-bleed regression)"
            )

        # Collated (inter-exp) outputs come from collate.yaml
        interexp_present = [
            "output1D-col1.csv",
            "output1D-col2.csv",
            "subdir1/subdir2/output1D-col1.csv",
            # Multi-source collation: one collated file per output column of the
            # 'combined' target, assembled from columns in two different files.
            "combined-col1.csv",
            "combined-col1_subdir3.csv",
        ]
        interexp_absent = [
            "subdir1/subdir2/output1D-col2.csv",
            "subdir3/output1D-col1.csv",
            "subdir3/output1D-col2.csv",
        ]

        inter_dir = stat_root / f"inter-exp/c1-exp{i}"
        inter_ref = ref_root / f"inter-exp/c1-exp{i}"
        for rel in interexp_present:
            assert_frame_equal(
                pl.read_csv(inter_dir / rel),
                pl.read_csv(inter_ref / rel),
                check_column_order=False,
            )
        for rel in interexp_absent:
            assert not (
                inter_dir / rel
            ).exists(), f"{rel} was collated but no collate entry names it"
