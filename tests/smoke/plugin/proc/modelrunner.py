#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#

# Core packages

# 3rd party packages
import nox

# Project packages
from sierra.core import batchroot
from tests._framework import engines, verify
from tests._framework import env as fwenv
from tests._framework.command import SierraCommand
from tests._framework.engines import ExpectedOutput, StageManifest

_JSONSIM = engines.BY_NAME["jsonsim"]

#: Outputs produced by the modelrunner plugin (``--proc proc.modelrunner``).
#: These are NOT in JSONSIM's shared stage-4 ``stages`` manifest because they
#: only exist when the plugin is enabled; a default stage-4 run doesn't produce
#: them. Checked declaratively via ``verify.verify_manifest`` so model outputs
#: go through the same presence machinery as graphs and stats, rather than a
#: hand-rolled loop. Each measure yields a ``.model`` and a matching ``.legend``.
_MODEL_MANIFEST = StageManifest(
    per_exp=(
        ExpectedOutput("models/c1-exp{i}/signal-trace.model"),
        ExpectedOutput("models/c1-exp{i}/signal-trace.legend"),
    ),
    inter_exp=(
        ExpectedOutput("models/inter-exp/signal-summary.model"),
        ExpectedOutput("models/inter-exp/signal-summary.legend"),
    ),
)


@nox.session(python=fwenv.VERSIONS, tags=["proc", "presence", "smoke"])
@fwenv.session_setup
@fwenv.session_teardown
def modelrunner_sanity(session):
    """Check that the modelrunner plugin works/doesn't crash."""
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

    cmd = (
        SierraCommand.from_base(session.env[spec.base_cmd_env].split())
        .set("--controller", spec.controller)
        .set("--batch-criteria", bc)
        .set("--exec-jobs-per-node", "4")
        .set_multi("--proc", ["proc.statistics", "proc.modelrunner"])
        .pipeline(1, 2, 3, 4)
    )

    session.run(*cmd.render(), silent=True)

    # Modelrunner outputs (intra-exp per experiment + inter-exp collated),
    # checked through the same presence machinery as every other artifact.
    verify.verify_manifest(_MODEL_MANIFEST, batch_root, spec.cardinality, spec.n_runs)
