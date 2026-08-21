#
# Copyright 2025 John Harwell, All rights reserved.
#
# SPDX-License-Identifier: MIT
#

# Core packages
import pathlib
import sys

# 3rd party packages

# Project packages
from sierra.core.variables import batch_criteria as bc
from sierra.plugins.engine.argos.variables import population_size
from sierra.core import types, cmdline
from sierra import main


def test_univar_argos():
    args = [
        "sierra",
        "--sierra-root=/tmp/sierra",
        "--engine=engine.argos",
        "--project=projects.sample_argos",
        "--exp-setup=exp_setup.T5.K5",
        "--expdef-template=sierra-sample-project/exp/argos/template.argos",
        "--scenario=HighBlockCount.10x10x2",
        "--controller=foraging.footbot_foraging",
        "--batch-criteria=population_size.Log16",
        "--physics-n-engines=1",
        "--pipeline",
        "1",
        "--exp-overwrite",
    ]

    cmdopts = {
        "project": "projects.sample_argos",
        "engine": "engine.argos",
        "pipeline": [1],
        "expdef": "expdef.xml",
    }
    sys.argv = args
    app = main.SIERRA(cmdline.BootstrapCmdline())

    criteria = bc.factory(
        {},
        cmdopts,
        pathlib.Path(
            "/tmp/sierra/projects.sample_argos/foraging.footbot_foraging/HighBlockCount.10x10x2/template-population_size.Log16/exp-inputs/"
        ),
        app.args,
        "HighBlockCount.10x10x2",
    )

    assert len(criteria.gen_attr_changelist()) == 5
    dirnames = criteria.gen_exp_names()
    assert len(dirnames) == 5
    assert dirnames[0] == "c1-exp0"
    assert dirnames[4] == "c1-exp4"

    app()

    populations = criteria.populations(cmdopts)

    assert populations == [1, 2, 4, 8, 16]

    assert criteria.n_exp() == 5


# Use jsonsim here too: its batch criteria have more than one thing in their
# attr change set.
def test_univar_jsonsim():
    args = [
        "sierra",
        "--sierra-root=/tmp/sierra",
        "--engine=plugins.jsonsim",
        "--project=projects.sample_jsonsim",
        "--exp-setup=exp_setup.T5.K5",
        "--expdef-template=sierra-sample-project/exp/jsonsim/template.json",
        "--scenario=cleanroom",
        "--expdef=expdef.json",
        "--controller=signal.lowpass",
        "--batch-criteria=fuel.1.10.C5",
        "--jsonsim-path=sierra-sample-project/plugins/jsonsim/jsonsim.py",
        "--pipeline",
        "1",
        "--exp-overwrite",
    ]

    cmdopts = {
        "project": "projects.sample_jsonsim",
        "engine": "plugins.jsonsim",
        "pipeline": [1],
        "expdef": "expdef.json",
    }
    sys.argv = args
    app = main.SIERRA(cmdline.BootstrapCmdline())

    criteria = bc.factory(
        {},
        cmdopts,
        pathlib.Path(
            "/tmp/sierra/projects.sample_jsonsim/signal.lowpass/fieldtest/template-fuel.1.10.C5/exp-inputs/"
        ),
        app.args,
        "fieldtest",
    )

    assert len(criteria.gen_attr_changelist()) == 5
    dirnames = criteria.gen_exp_names()
    assert len(dirnames) == 5
    assert dirnames[0] == "c1-exp0"
    assert dirnames[4] == "c1-exp4"

    assert len(criteria.gen_attr_changelist()[0]) == 2
    assert len(criteria.gen_attr_changelist()[4]) == 2


def test_bivar_jsonsim():
    # Bivariate criteria factory: two criteria form a 2D cross-product. Uses the
    # lightweight jsonsim engine -- this tests the engine-agnostic bivar machinery
    # (cross-product cardinality + c1-exp{i}+c2-exp{j} naming), not any engine
    # specifics, so there's no reason to drive it through a heavyweight binary
    # engine. max_speed.1.9.C5 x fuel.1.9.C4 -> 5 x 4 = 20 experiments.
    args = [
        "sierra",
        "--sierra-root=/tmp/sierra",
        "--engine=plugins.jsonsim",
        "--project=projects.sample_jsonsim",
        "--exp-setup=exp_setup.T5.K5",
        "--expdef-template=sierra-sample-project/exp/jsonsim/template.json",
        "--scenario=cleanroom",
        "--controller=signal.kalman",
        "--batch-criteria",
        "--expdef=expdef.json",
        "max_speed.1.9.C5",
        "fuel.1.9.C4",
        "--jsonsim-path=sierra-sample-project/plugins/jsonsim/jsonsim.py",
        "--exp-overwrite",
        "--pipeline",
        "1",
    ]

    cmdopts = {
        "project": "projects.sample_jsonsim",
        "engine": "plugins.jsonsim",
        "scenario": "cleanroom",
        "pipeline": [1],
        "expdef": "expdef.json",
    }
    sys.argv = args
    app = main.SIERRA(cmdline.BootstrapCmdline())

    criteria = bc.factory(
        {},
        cmdopts,
        pathlib.Path(
            "/tmp/sierra/projects.sample_jsonsim/signal.kalman/cleanroom/"
            "template-max_speed.1.9.C5+fuel.1.9.C4/exp-inputs"
        ),
        app.args,
        "cleanroom",
    )
    assert len(criteria.gen_attr_changelist()) == 20

    dirnames = criteria.gen_exp_names()
    assert len(dirnames) == 20
    assert dirnames[0] == "c1-exp0+c2-exp0"
    assert dirnames[19] == "c1-exp4+c2-exp3"

    app()

    assert criteria.n_exp() == 20
