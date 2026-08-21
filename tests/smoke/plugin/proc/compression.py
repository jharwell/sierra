#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#

# Core packages
import shutil

# 3rd party packages
import nox

# Project packages
from sierra.core import batchroot
from tests._framework import engines, verify
from tests._framework import env as fwenv
from tests._framework.command import SierraCommand

_JSONSIM = engines.BY_NAME["jsonsim"]


@nox.session(python=fwenv.VERSIONS, tags=["proc", "presence", "smoke"])
@fwenv.session_setup
@fwenv.session_teardown
def compression_sanity(session):
    """Check that the compress/decompress plugins work/don't crash."""
    spec = _JSONSIM
    bc = spec.batch_criteria
    leaf = batchroot.ExpRootLeaf(bc=[bc], template_stem=spec.template_stem)
    batch_root = batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project=spec.project,
        controller=spec.controller,
        leaf=leaf,
        scenario=spec.scenario,
    ).to_path()

    output_root = batch_root / "exp-outputs"

    def _base(*procs):
        return (
            SierraCommand.from_base(session.env[spec.base_cmd_env].split())
            .set("--controller", spec.controller)
            .set("--batch-criteria", bc)
            .set("--exec-jobs-per-node", "4")
            .set_multi("--proc", ["proc.statistics", *procs])
        )

    # Compress: the per-run output tarball should be produced.
    session.run(*_base("proc.compress").pipeline(1, 2, 3).render(), silent=True)
    for exp in range(0, spec.cardinality):
        for run in range(0, spec.n_runs):
            path = output_root / f"c1-exp{exp}/template_run{run}_output/output.tar.gz"
            assert path.exists(), f"{path} does not exist"

    shutil.rmtree(session.env["SIERRA_ROOT"])

    # Compress with --compress-remove-after: after tarring a run's output into
    # output.tar.gz, everything else in that run's exp-outputs directory is
    # removed, so the run dir should contain ONLY the tarball.
    session.run(
        *_base("proc.compress")
        .pipeline(1, 2, 3)
        .set("--compress-remove-after")
        .render(),
        silent=True,
    )
    for exp in range(0, spec.cardinality):
        for run in range(0, spec.n_runs):
            run_dir = output_root / f"c1-exp{exp}/template_run{run}_output"
            tarball = run_dir / "output.tar.gz"
            assert tarball.exists(), f"{tarball} does not exist"
            # Everything except the tarball must have been removed.
            leftovers = [p for p in run_dir.iterdir() if p.name != "output.tar.gz"]
            assert not leftovers, (
                f"--compress-remove-after left raw output in {run_dir}: "
                f"{[p.name for p in leftovers]}"
            )

    # Decompress, then verify stage 4 produces the full graph/stat manifest.
    session.run(*_base("proc.decompress").pipeline(3, 4).render(), silent=True)

    # Stage-4 verification after decompression. The run uses SIERRA's default
    # center/spread, so we check the full stage-4 manifest at those defaults:
    # intra-exp graphs, inter-exp graphs, AND the inter-exp .{stat} CSVs.
    verify.verify_stage(_JSONSIM, 4, batch_root, max_tier=1)
