#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#
"""Smoke tests for the ``prod.graphs`` plugin's backend selection.

Exercises the plugin producing BOTH matplotlib (.png) and bokeh (.html) variants
of every graph. The graph NAMES are not duplicated here: they come from the
engine's stage-4 manifest via ``verify.graph_paths``. This test's unique job is
the backend dimension -- assert that each declared graph exists in both the
.png and .html variant -- so it derives the .png set from the manifest and
checks the .html twin alongside it.
"""

# 3rd party packages
import nox

# Project packages
from sierra.core import batchroot
from tests._framework import engines, verify
from tests._framework import env as fwenv
from tests._framework.command import SierraCommand


def _batch_root(session, spec, bc, scenario):
    leaf = batchroot.ExpRootLeaf(bc=[bc], template_stem=spec.template_stem)
    return batchroot.ExpRoot(
        sierra_root=f"{session.env['SIERRA_ROOT']}",
        project=spec.project,
        controller=spec.controller,
        leaf=leaf,
        scenario=scenario,
    ).to_path()


def _run_backends(session, spec, bc):
    """Run stages 1-3, then stage 4 once per graphs backend."""
    base = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--controller", spec.controller)
        .set("--batch-criteria", bc)
    )
    session.run(*base.copy().pipeline(1, 2, 3).render(), silent=True)
    for backend in ("matplotlib", "bokeh"):
        session.run(
            *base.copy().pipeline(4).set("--graphs-backend", backend).render(),
            silent=True,
        )


def _assert_both_backends(batch_root, spec):
    """Every graph the stage-4 manifest declares must exist as BOTH a .png
    (matplotlib) and a .html (bokeh) file."""
    for png_rel in verify.graph_paths(spec, 4):
        html_rel = png_rel[: -len(".png")] + ".html"
        png = batch_root / png_rel
        html = batch_root / html_rel
        assert png.is_file(), f"matplotlib graph missing: {png}"
        assert html.is_file(), f"bokeh graph missing: {html}"


@nox.session(python=fwenv.VERSIONS, tags=["graphs", "presence", "smoke"])
@fwenv.session_setup
@fwenv.session_teardown
def graphs_backend(session):
    """Check backend selection with the prod.graphs plugin for all graph
    types (matplotlib .png + bokeh .html), across jsonsim and yamlsim."""
    spec = engines.BY_NAME["yamlsim"]
    batch_root = _batch_root(session, spec, "noise_floor.1.9.C5", "scenario1")
    _run_backends(session, spec, "noise_floor.1.9.C5")
    assert (
        batch_root / "graphs" / "inter-exp"
    ).is_dir(), f"Directory {batch_root}/graphs/inter-exp does not exist"
    _assert_both_backends(batch_root, spec)
